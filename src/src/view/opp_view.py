import pandas as pd
from bisect import bisect_left
import src.core.kwarg_picker as kwarg_picker
from src.core.iter_utils import ensure_iterable
from src.view.color import Color, Colors, WebColors
from src.view.cell_view import CellView
from src.view.data_view import TimedeltaView, get_style_dict, with_groupby_origin_col


class OppView:
    @staticmethod
    def fmt_edge_selector(edge, even_odd=None):
        parts = ['edge', f'{edge:.2f}'.replace('.', '')]
        if even_odd is not None:
            parts.append(even_odd)
        return '-'.join(parts)

    @staticmethod
    def fmt_dur_selector(dur, even_odd=None):
        parts = ['lsn-win', f'{dur.microseconds}']
        if even_odd is not None:
            parts.append(even_odd)
        return '-'.join(parts)

    @staticmethod
    def get_dur_selector_column(df, col_name, odb_keys, opp_origin_selector):
        if isinstance(odb_keys, dict):
            odb_keys = list(odb_keys)
        odb_keys.sort()

        def impl(r):
            dur = r[col_name]
            eid = r.name[3]
            idx = bisect_left(odb_keys, dur)
            if idx >= len(odb_keys):
                idx = len(odb_keys) - 1
            elif idx > 0 and odb_keys[idx] > dur:
                idx -= 1
            rv = f'lsn-win-{odb_keys[idx].microseconds}'
            if r['is_origin']:
                rv += '-' + opp_origin_selector
            return rv

        even_odd = ['even', 'odd']
        default_css = [even_odd[i % 2] for i in range(1, len(df) + 1)]
        res = pd.DataFrame(
            data={
                'dur_css': df.apply(impl, axis=1),
                'default_css': default_css
            })
        return res.apply(lambda r: f'{r[0]}-{r[1]}', axis=1)

    @staticmethod
    def get_edge_selector_column(df, col_name, edge_keys, opp_origin_selector):
        if isinstance(edge_keys, dict):
            edge_keys = list(edge_keys)
        edge_keys.sort()

        def impl(r):
            edge = r[col_name]
            idx = bisect_left(edge_keys, edge)
            if idx >= len(edge_keys):
                idx = len(edge_keys) - 1
            elif idx > 0 and edge_keys[idx] > edge:
                idx -= 1
            rv = OppView.fmt_edge_selector(edge_keys[idx])
            if r['is_origin']:
                rv += '-' + opp_origin_selector
            return rv

        even_odd = ['even', 'odd']
        default_css = [even_odd[i % 2] for i in range(1, len(df) + 1)]
        res = pd.DataFrame(
            data={
                'edge_css': df.apply(impl, axis=1),
                'default_css': default_css
            })
        return res.apply(lambda r: f'{r[0]}-{r[1]}', axis=1)

    def __init__(self, opp, **kwargs):
        self.opp = opp
        self.header_style = kwargs.get('header_style') or CellView(
            bg=Colors.header_background(),
            border='solid',
            bdc='white',
            valign='top')
        self.even_style = kwargs.get('even') or kwargs.get(
            'even_style') or CellView(
                fg=Colors.black(), bg=Color(171, 171, 171))
        self.odd_style = kwargs.get('odd') or kwargs.get(
            'odd_style') or CellView(
                fg=Colors.black(), bg=Color(196, 196, 196))
        self.hover_style = kwargs.get('hover') or kwargs.get(
            'hover_style') or CellView(bg='slateblue')
        self.opp_origin_style = kwargs.get('opp_origin_style') or CellView(
            bdts='solid', bdtc='CornflowerBlue')
        self.opp_origin_selector = kwargs.get(
            'opp_origin_selector') or 'opp-origin'

        self.opp_durs = ensure_iterable(kwargs.get('opp_durs'), if_none = None) or\
            [pd.Timedelta(x, unit='us') for x in [50, 100, 500, 1000, 2000]]
        self.edges = ensure_iterable(kwargs.get('edges'), None) or {}

    def display(self, **kwargs):
        opp_durs = kwargs.get('opp_durs') or self.opp_durs
        sorted_opp_durs = list(opp_durs)
        sorted_opp_durs.sort()
        opp_origin_selector = self.opp_origin_selector

        opp_view = self.opp.copy()
        # opp_view['t_tod'] = opp_view['t_time'] - opp_view.index.get_level_values(0) - pd.Timedelta('1d')
        column_display = kwargs.get('columns') or [
            't_tod', 'opp_dur', 'opp_dur_thru', 'edge', 'side', 'bid_q_1',
            'bid_p_1', 'ask_p_1', 'ask_q_1'
        ]
        opp_view = opp_view[column_display]
        sdict = get_style_dict(opp_view)
        sdict.update({col: '{:.2f}' for col in ['bid_p_1', 'ask_p_1', 'edge']})
        sdict.update({
            c: lambda x: f'{TimedeltaView(x).normal_microseconds():.0f}'
            for c in [
                'opp_dur', 'opp_dur_fsn', 'opp_dur_lsn', 'opp_dur_thru',
                'opp_dur_thru_lsn', 'bk_dur'
            ]
        })

        edges = kwargs.get('edges') or self.edges
        sorted_edges = list(edges)
        sorted_edges.sort()
        opp_origin_style = kwargs.get(
            'opp_origin_style') or self.opp_origin_style

        def get_selector_columns(s):
            def get_dur_formatter(col):
                return lambda x: OppView.get_dur_selector_column(
                    opp_view, col, sorted_opp_durs, self.opp_origin_selector)

            # The dur_formatter lambdas must be created in a separate function (not inline),
            # because of the way capture works (or arguably doesn't) in loops:
            # https://stackoverflow.com/questions/2295290/what-do-lambda-function-closures-capture
            formatters = {
                col: get_dur_formatter(col)
                for col in [
                    'opp_dur', 'opp_dur_fsn', 'opp_dur_lsn', 'opp_dur_thru',
                    'opp_dur_thru_fsn', 'opp_dur_thru_lsn'
                ]
            }
            formatters.update({
                'edge':
                lambda x: OppView.get_edge_selector_column(
                    opp_view, 'edge', sorted_edges, self.opp_origin_selector)
            })
            if s.name in formatters:
                return formatters[s.name](s)

            def get_selector(r):
                if r['is_origin']:
                    return opp_origin_selector
                return "cell"

            even_odd = ['even', 'odd']
            default_css = [
                even_odd[i % 2] for i in range(1,
                                               len(opp_view) + 1)
            ]
            res = pd.DataFrame(
                data={
                    'edge_css': opp_view.apply(get_selector, axis=1),
                    'default_css': default_css
                })
            return res.apply(
                lambda r: f'{r["edge_css"]}-{r["default_css"]}', axis=1)

        selector_cols = opp_view.apply(get_selector_columns)
        even_style = self.even_style
        odd_style = self.odd_style
        opp_origin_even_style = opp_origin_style.merge(even_style)
        opp_origin_odd_style = opp_origin_style.merge(odd_style)
        hover_style = self.hover_style
        header_style = self.header_style

        table_styles = [{
            'selector': '.cell-even',
            'props': even_style
        }, {
            'selector': '.cell-odd',
            'props': odd_style
        }, {
            'selector': '.opp-origin-even',
            'props': opp_origin_style.merge(even_style)
        }, {
            'selector': '.opp-origin-odd',
            'props': opp_origin_style.merge(odd_style)
        }, {
            'selector': 'th',
            'props': header_style
        }, {
            'selector': 'th:hover',
            'props': header_style.merge(hover_style)
        }]

        def append_bucket_styles(buckets, fmt_selector):
            for val in buckets:
                val_style = buckets[val]
                if val_style is None:
                    continue
                val_even_style = val_style.merge(even_style)
                val_odd_style = val_style.merge(odd_style)

                table_styles.append({
                    'selector': f'.{fmt_selector(val)}-even',
                    'props': val_even_style
                })
                table_styles.append({
                    'selector': f'.{fmt_selector(val)}-odd',
                    'props': val_odd_style
                })
                table_styles.append({
                    'selector':
                    f'.{fmt_selector(val)}-{opp_origin_selector}-even',
                    'props':
                    opp_origin_style.merge(val_even_style)
                })
                table_styles.append({
                    'selector':
                    f'.{fmt_selector(val)}-{opp_origin_selector}-odd',
                    'props':
                    opp_origin_style.merge(val_odd_style)
                })

        append_bucket_styles(opp_durs, OppView.fmt_dur_selector)
        append_bucket_styles(edges, OppView.fmt_edge_selector)
        tslist = list(table_styles)
        for s in tslist:
            norm_style = s['props']
            hstyle = norm_style.merge(hover_style)
            table_styles.append({
                'selector': s['selector'] + ':hover',
                'props': hstyle
            })
        for s in table_styles:
            s['props'] = s['props'].to_tuples()

        self.opp_view = opp_view
        self.table_styles = table_styles
        return opp_view.style\
            .format(sdict)\
            .set_td_classes(selector_cols)\
            .set_table_styles(table_styles, overwrite=True)


def to_opp_view(opp_bk, **kwargs):
    max_dur = kwarg_picker.pick_or(kwargs, pd.Timedelta('500us'), 'max_dur')
    if max_dur is None:
        if not isinstance(max_dur, pd.Timedelta):
            max_dur = pd.Timedelta(max_dur)

    max_lsn_delta = kwarg_picker.pick_or(
        kwargs, pd.Timedelta('1ms'), 'max_lsn_delta')

    # TODO: Make accept display_cols parameter (it's a little messy right now,
    # much simpler to just hardcode them)
    # display_cols = kwarg_picker.pick_or(
    #     kwargs,
    #     [ 'is_origin', 't_tod', 'bk_dur', 'lsn_delta', 'opp_dur', 'opp_dur_fsn', 'opp_dur_lsn',
    #      'opp_dur_thru', 'opp_dur_thru_lsn', 'edge', 'side', 'bid_q_1', 'bid_p_1', 'ask_p_1', 'ask_q_1'],
    #     'display_columns', 'display_cols', 'columns', 'cols', 'visible_columns', 'visible_cols', 'vis_cols')

    display_cols = [
        'is_origin', 't_tod', 'bk_dur', 'lsn_delta', 'opp_dur', 'opp_dur_fsn',
        'opp_dur_lsn', 'opp_dur_thru', 'opp_dur_thru_lsn', 'edge', 'side',
        'bid_q_1', 'bid_p_1', 'ask_p_1', 'ask_q_1'
    ]

    opp_dur_buckets = kwarg_picker.pick(kwargs, 'dur_styles')
    if opp_dur_buckets is None:
        opp_dur_buckets = {
            pd.Timedelta('0us'): CellView(),
            pd.Timedelta('50us'): CellView(bg=Colors.gold()),
            pd.Timedelta('100us'): CellView(bg=WebColors.sky_blue()),
            pd.Timedelta('500us'): CellView(bg=Colors.lightgreen_pastel())
        }

    edge_buckets = kwarg_picker.pick(kwargs, 'edge_styles')
    if edge_buckets is None:
        edge_buckets = {
            -0.25:
            CellView(fw='bold', bg=Colors.darkred()),
            0.0:
            CellView(),
            0.25:
            CellView(fg=Colors.blue(), fw='bold'),
            0.50:
            CellView(fg=Colors.blue(), fw='bold', bg=WebColors.sky_blue()),
            1.0:
            CellView(fg=Colors.blue(), fw='bold', bg=Colors.gold()),
            2.0:
            CellView(
                fg=Colors.blue(), fw='bold', bg=Colors.lightgreen_pastel()),
        }

    opp_bk['lsn_delta'] = opp_bk['opp_dur_thru'] - opp_bk['opp_dur_thru_lsn']
    if max_dur is not None:
        opp_bk = opp_bk.loc[opp_bk['opp_dur_lsn'] <= max_dur]
    if max_lsn_delta is not None:
        opp_bk = opp_bk.loc[opp_bk['lsn_delta'] < max_lsn_delta]

    def get_pnl(x):
        obtainable = x.loc[x['opp_dur_thru_lsn'] >= pd.Timedelta('55us')]
        if len(obtainable) == 0:
            return x.head(1)
        idx = obtainable[['edge']].idxmax()
        rv = obtainable.loc[idx]
        return rv

    # opp_bk = opp_bk.groupby(level=[0,1,2]).apply(get_pnl)
    # opp_bk = opp_bk.set_index([opp_bk.index.get_level_values(i) for i in range(3, 7)])
    opp_bk = with_groupby_origin_col(opp_bk, level=['market_date', 'symbol'])
    if display_cols is not None:
        opp_bk = opp_bk[display_cols]

    ov = OppView(
        opp_bk.head(320),
        opp_durs=opp_dur_buckets,
        edges=edge_buckets,
        opp_origin_css='opp-origin')
    return ov


def display_opp_view(ov):
    microsecond_cols = [
        'opp_dur_fsn', 'opp_dur_lsn', 'lsn_delta', 'opp_dur_thru',
        'opp_dur_thru_lsn'
    ]
    return ov.display(
        verbose=None,
        columns =[
            'is_origin', 't_tod', 'bk_dur', 'lsn_delta', 'opp_dur', 'opp_dur_fsn', 'opp_dur_lsn',
            'opp_dur_thru', 'opp_dur_thru_lsn', 'edge', 'side', 'bid_q_1', 'bid_p_1', 'ask_p_1', 'ask_q_1'])\
        .format({c: lambda x: TimedeltaView(x, fmt='micros') for c in microsecond_cols}, subset=microsecond_cols)\
        .hide_columns(['is_origin', 'opp_dur', 'opp_dur_fsn', 'opp_dur_lsn', 'opp_dur_thru'])

    # opp_bk['edge'].sum() * 4 * 12.5
    # opp_bk.head(100).groupby(level=[0,1,2]).apply(lambda x: x.head(3))
    # ov.opp_view
