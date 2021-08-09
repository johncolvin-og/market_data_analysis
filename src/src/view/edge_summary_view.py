import src.core.kwarg_picker as kwarg_picker
from src.core.sort_utils import binary_search

import math
import numpy as np
import pandas as pd


def get_opp_fill_lambda(
        dur_col='opp_dur_thru_lsn',
        req_cash_col=None,
        fee_col='non_member_fee',
        fill_thresh=pd.Timedelta('55us'),
        cpp=None):
    if req_cash_col is None:
        req_cash_col = fee_col

    def impl(x):
        observed = x.iloc[0]
        observed_edge = observed['edge']
        observed_cash = observed_edge
        if cpp is not None:
            observed_cash = observed_cash * cpp

        obtainable = x.loc[x[dur_col] >= fill_thresh]
        if len(obtainable) == 0:
            rv = x.iloc[[-1]]
            rv['shot'] = False
            rv['fill_edge'] = math.nan
        else:
            idx = obtainable[['edge']].idxmax()
            rv = obtainable.loc[idx]
            rv['shot'] = (not math.isnan(observed_cash)) and (
                observed_cash > observed[req_cash_col])
            # rv['shot'] = True
            rv['fill_edge'] = rv['edge']
        rv['fill_cash'] = rv['fill_edge']
        if cpp is not None:
            rv['fill_cash'] = rv['fill_cash'] * cpp
        rv['net_fill_cash'] = rv['fill_cash'] - rv[fee_col]
        return rv

    return impl


def get_edge_summary(
        opp_bk,
        dur_col='opp_dur_thru_lsn',
        shot_thresh=pd.Timedelta('0us'),
        fill_thresh=pd.Timedelta('55us'),
        edges=[-.50, -.25, 0.0, .25, .50, 1.0],
        cpp=None,
        **kwargs):
    """Picks a fill price (in terms of edge) for each opportunity"""

    fmt_edge = kwarg_picker.pick_or(
        kwargs, lambda x: f'{x:.2f}', 'edge_col_fmtr', 'edge_fmtr',
        'edge_formatter', 'format_edge', 'fmt_edge')
    # todo: remove req_edge keyword (this col is expected to be in cash terms)
    fee_col = kwarg_picker.pick_or(kwargs, 'R106J_NON_MEMBER', 'fee')
    req_cash_col = kwarg_picker.pick_or(
        kwargs, fee_col, 'req_cash', 'req_edge')
    opp_edge_groupby = opp_bk.groupby(level=[0, 1, 2])
    opp_fill_lambda = get_opp_fill_lambda(
        dur_col, req_cash_col, fee_col, fill_thresh, cpp)
    opp_edge_df = opp_edge_groupby.apply(opp_fill_lambda)
    # opp_edge_df = opp_edge_df.loc[opp_edge_df['shot']]

    sorted_edges = list(edges)
    sorted_edges.sort()

    def get_edge_col(edge):
        idx = binary_search(edge, within_bounds=True)
        return fmt_edge(sorted_edges[idx])

    def count_opps_per_edge(x):
        xshot = x.loc[x['shot']]
        fill_edge = xshot['fill_edge'].sum()
        net_fill_cash = xshot['net_fill_cash'].sum()
        num_skipped = len(x) - len(xshot)

        xshot['edge_col'] = xshot['edge'].apply(get_edge_col)
        edge_counts = xshot.groupby(['edge_col']).size()

        def get_edge_count(edge):
            col_name = fmt_edge(edge)
            if col_name in edge_counts:
                return edge_counts.loc[col_name]
            return np.nan

        ope = pd.DataFrame(
            data=[[get_edge_count(e) for e in sorted_edges] +
                  [len(xshot), num_skipped, fill_edge, net_fill_cash]],
            columns=[get_edge_col(e) for e in sorted_edges] +
            ['num_shots', 'num_skipped', 'fill_edge', 'net_fill_cash'])
        return ope

    rv = opp_edge_df.groupby(
        level=['market_date', 'symbol']).apply(count_opps_per_edge)
    rv = rv.set_index(
        [rv.index.get_level_values(c) for c in ['market_date', 'symbol']])
    return rv
