import os
from src.core.domain.polygon import Polygon


def cast_opp_summary_columns(opps):
    import pandas as pd
    opps['date'] = pd.to_datetime(opps['date'])
    opps.rename(columns={"prod": "asset"}, inplace=True)
    opps.drop(columns='start_h_t_time', inplace=True)
    opps['start_t_time'] = pd.to_timedelta(opps['start_t_time'], unit='ns')
    opps['fs_win'] = pd.to_timedelta(opps['fs_win'], unit='ns')
    opps['ls_win'] = pd.to_timedelta(opps['ls_win'], unit='ns')


def compute_pnl(summ_rows_arg, fee_per_contract, latency, latency_col):
    def compute_pnl_row(r):
        n_contracts = Polygon(r['symbol']).n_contracts()
        n_legs = Polygon(r['symbol']).n_legs()
        # piggy backing filtering rows out
        if (r['merged_qty'] == 1):
            if (r[latency_col] < 1000000):
                return -1.0
        if r[latency_col] < latency:
            return -1.0
        if (r['is_direct'] == False):
            if (r['merged_qty'] < n_legs):
                return -1.0
        n_contracts = Polygon(r['symbol']).n_contracts()
        pnl = r['merged_value'] - n_contracts * fee_per_contract
        pnl = pnl * r['merged_qty']
        return pnl

    def agg(grp_rows):
        m_idx = grp_rows['pnl'].argmax()
        r = grp_rows.iloc[m_idx]
        return r

    summ_rows = summ_rows_arg.copy()
    summ_rows['pnl'] = summ_rows.apply(lambda r: compute_pnl_row(r), axis=1)
    summ_rows = summ_rows[summ_rows['pnl'] > 0]
    summ_rows['key'] = summ_rows['date'] + '-' + summ_rows['opp_id'].astype(
        str)
    return summ_rows.groupby('key').apply(lambda x: agg(x))
    # return summ_rows


def map_opp_summary_csvs(months):
    import pandas as pd
    opps = {}
    for month in months:
        poly_vals = pd.read_csv(f'data/360/poly_vals_summ_{month}.csv')
        cast_opp_summary_columns(poly_vals)
        opps[month] = poly_vals
    return opps


class DurationSummarizer:
    @staticmethod
    def val_gt_col(val):
        return f'merged_value_gt_{val}'

    @staticmethod
    def dur_gt_col(dur):
        return f'ls_win_gt_{dur.item().microseconds}'

    @staticmethod
    def val_dur_col(val, dur):
        return

    @staticmethod
    def default_quantiles():
        return list(reversed([0.05] + [.1 * i for i in range(1, 10)] + [.95]))

    @staticmethod
    def get_quantile_col(quantile: float):
        return f'{quantile:.2f}'

    @staticmethod
    def get_quantile_cols(quantiles=None):
        if quantiles == None:
            quantiles = DurationSummarizer.default_quantiles()
        return list(map(DurationSummarizer.get_quantile_col, quantiles))

    @staticmethod
    def get_durations_per_polygon(
            opps, min_value=10, min_qty=1, min_duration=None, quantiles=None):
        import numpy as np
        import pandas as pd

        if quantiles == None:
            quantiles = DurationSummarizer.default_quantiles()
        value_threshes = range(10, 50, 10)
        time_threshes = [
            np.timedelta64(v, 'us') for v in range(100000, 200000, 25000)
        ]
        refactored_opps = {}
        # time_threshes = [np.timedelta64(v, 'us') for v in range(50, 200, 25)]
        for month in opps:
            mo = opps[month]
            if min_value != None:
                mo = mo.loc[(mo['merged_value'] >= min_value)]
            if min_qty != None:
                mo = mo.loc[(mo['merged_qty'] >= min_qty)]
            if min_duration != None:
                mo = mo.loc[(mo['ls_win'] >= min_duration)]
            mo = mo.rename(columns={'ls_win': 'ls_win_temp'})
            mo['ls_win'] = mo['ls_win_temp'].apply(
                lambda x: pd.Timedelta(0, unit='us')
                if x < pd.Timedelta(0, unit='us') else x)
            mo = mo.drop(columns=['ls_win_temp'])
            for vt in value_threshes:
                mo[DurationSummarizer.val_gt_col(vt)] = mo['merged_value'] > vt
            for tt in time_threshes:
                mo[DurationSummarizer.dur_gt_col(tt)] = mo['ls_win'] > tt
            refactored_opps[month] = mo
        bin_breakdowns = {}
        for vt in value_threshes:
            data = {'n_total': [len(mo) for mo in refactored_opps.values()]}
            # data[val_dur_col(vt, tt)] = [len(mo.loc[mo[dur_gt_col(tt)] & mo[val_gt_col(vt)]]) for mo in opps.values()]
            for q in reversed([i * 0.1 for i in range(1, 10)]):
                data[f'{1 - q:.1f}'] = [
                    mo.loc[mo[DurationSummarizer.val_gt_col(vt)]]
                    ['ls_win'].quantile(q)
                    # f"{mo.loc[mo[DurationSummarizer.val_gt_col(vt)]]['ls_win'].apply(lambda x: x.microseconds).quantile(q):,.1f}"
                    for mo in refactored_opps.values()
                ]
            bin_breakdown = pd.DataFrame(
                index=refactored_opps.keys(), data=data)
            bin_breakdowns[vt] = bin_breakdown

        # quantiles = [.125 * i for i in range(1, int(1.0/.125 - 1))] + [.95, .99]
        result = {}
        for month, month_opps in refactored_opps.items():
            # nov_opps = opps['nov']
            month_opps_syms = month_opps.groupby('symbol')

            def count_opps(sym_opps):
                data = {'n_opps': len(sym_opps)}
                for vt in value_threshes:
                    data[f'n_opps_v{vt}'] = len(
                        sym_opps.loc[sym_opps['merged_value'] >= vt])
                for q in quantiles:
                    data[f'{q:.2f}'] = sym_opps['ls_win'].quantile(q)
                return pd.Series(data)

            sym_opp_grps = pd.DataFrame(data=month_opps_syms.apply(count_opps))
            sym_opp_grps.sort_values('n_opps', ascending=False, inplace=True)
            result[month] = sym_opp_grps
        return result
