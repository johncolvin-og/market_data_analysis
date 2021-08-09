import pandas as pd
from bisect import bisect_left


def fmt_pnl_col(mship, delay):
    return f'{delay.microseconds}us_{mship}_pnl'


def get_single_opp_pnl(
        opp, req_edge, delays, latency=pd.Timedelta('50us'), cpp=50.0):
    data = {}
    for delay in delays:
        shot_idx = bisect_left(opp['opp_dur_thru'], delay)
        if shot_idx == len(opp):
            shot_idx -= 1
        shot_start_row = opp.iloc[shot_idx]
        if shot_start_row['opp_dur_thru'] < delay:
            return None

        fill_eid_col = f'{delay.microseconds}us_fill_eid'
        if shot_start_row['edge'] < req_edge:
            return pd.DataFrame(
                data={
                    fmt_pnl_col('nm', delay): 0.0,
                    fmt_pnl_col('m', delay): 0.0,
                    fill_eid_col: 0
                },
                index=[opp.index.get_level_values('opp_start_eid')[0]])

        fill_idx = bisect_left(
            opp.iloc[shot_idx:]['opp_dur_thru'], delay + latency)
        fill_idx += shot_idx
        if fill_idx == len(opp):
            fill_idx -= 1
        fill_row = opp.iloc[fill_idx]
        if fill_row['opp_dur_thru'] < (delay + latency):
            raise Exception('Unable to compute fill price')

        cash_edge = fill_row['edge'] * cpp,
        data[fmt_pnl_col('nm', delay)] = cash_edge - fill_row['non_member_fee']
        data[fmt_pnl_col('m', delay)] = cash_edge - fill_row['member_fee']
        data[fill_eid_col] = fill_row['synth_bk_eid']

    res = pd.DataFrame(
        data=data, index=[opp.index.get_level_values('opp_start_eid')[0]])
    return res


def get_opp_pnl(
        opps, req_edge, delays, latency=pd.Timedelta('50us'), cpp=50.0):
    def impl(opps):
        res = opps.groupby(level=['market_date', 'symbol', 'opp_start_eid'])\
            .apply(lambda x: get_single_opp_pnl(x, req_edge, delays, latency, cpp))\
            .reset_index(level=[0,1,2], drop=True)
        res.index.rename('opp_start_eid', inplace=True)
        return res

    grp = opps.groupby(level=[0, 1])
    return grp.apply(impl)


# from bisect import bisect_left

# def fmt_pnl_col(mship, delay):
#     return f'{delay.microseconds}us_{mship}_pnl'

# def get_edge_per_delay(all_opps, delays, req_edge, latency = pd.Timedelta('50us'), cpp = 50.0):
#     def get_edge(opps):
#         def impl(opp):
#             data = {}
#             for delay in delays:
#                 shot_idx = bisect_left(opp['opp_dur_thru'], delay)
#                 if shot_idx == len(opp):
#                     shot_idx -= 1
#                 shot_start_row = opp.iloc[shot_idx]
#                 if shot_start_row['opp_dur_thru'] < delay:
#                     return None

#                 fill_eid_col = f'{delay.microseconds}us_fill_eid'
#                 if shot_start_row['edge'] < req_edge:
#                     return pd.DataFrame(data={
#                         fmt_pnl_col('nm', delay): 0.0,
#                         fmt_pnl_col('m', delay): 0.0,
#                         fill_eid_col: 0
#                     }, index=[opp.index.get_level_values('opp_start_eid')[0]])

#                 fill_idx = bisect_left(opp.iloc[shot_idx:]['opp_dur_thru'], delay + latency)
#                 fill_idx += shot_idx
#                 if fill_idx == len(opp):
#                     fill_idx -= 1
#                 fill_row = opp.iloc[fill_idx]
#                 if fill_row['opp_dur_thru'] < (delay + latency):
#                     raise Exception('Unable to compute fill price')

#                 cash_edge = fill_row['edge'] * cpp,
#                 data[fmt_pnl_col('nm', delay)] = cash_edge - fill_row['non_member_fee']
#                 data[fmt_pnl_col('m', delay)] = cash_edge - fill_row['member_fee']
#                 data[fill_eid_col] = fill_row['synth_bk_eid']
#             res = pd.DataFrame(data=data, index=[opp.index.get_level_values('opp_start_eid')[0]])
#             return res

#         res = opps.groupby(level=[0, 1, 2]).apply(impl).reset_index(level=[0,1,2], drop=True)
#         res.index.rename('opp_start_eid', inplace=True)
#         return res
#     grp = all_opps.groupby(level=[0,1])
#     return grp.apply(get_edge)
