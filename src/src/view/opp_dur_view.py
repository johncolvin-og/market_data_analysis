import pandas as pd
import src.core.kwarg_picker as kwarg_picker
from src.core.iter_utils import ensure_iterable
from src.view.color import Color, Colors, WebColors
from src.view.cell_view import CellView
from src.view.data_view import TimedeltaView, get_style_dict
from src.core.sort_utils import binary_search


class OppDurView:
    @staticmethod
    def fmt_dur_selector(dur, even_odd=None):
        parts = ['lsn-win', f'{dur.microseconds}']
        if even_odd is not None:
            parts.append(even_odd)
        return '-'.join(parts)

    @staticmethod
    def get_dur_selector_column(df, col_name, odb_keys):
        if isinstance(odb_keys, dict):
            odb_keys = list(odb_keys)
        odb_keys.sort()

        def impl(r):
            return binary_search(odb_keys, r[col_name], within_bounds=True)

        even_odd = ['even', 'odd']
        default_css = [even_odd[i % 2] for i in range(1, len(df) + 1)]
        res = pd.DataFrame(
            data={
                'dur_css': df.apply(impl, axis=1),
                'default_css': default_css
            })
        return res.apply(
            lambda r: f'{OppDurView.fmt_dur_selector(odb_keys[r[0]])}-{r[1]}',
            axis=1)

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
        self.dur_cols = kwargs.get('dur_cols') or kwargs.get('dur_col')

        self.opp_durs = ensure_iterable(kwargs.get('opp_durs'), if_none=None)
        if self.opp_durs is None:
            raise ValueError('opp_durs cannot be None')
        # self.opp_durs = ensure_iterable(kwargs.get('opp_durs'), if_none = None) or\
        #     [pd.Timedelta(x, unit='us') for x in [50, 100, 500, 1000, 2000]]

    def display(self, **kwargs):
        dur_cols = kwarg_picker.pick(kwargs, self.dur_cols, 'dur_cols')
        opp_durs = kwargs.get('opp_durs') or self.opp_durs
        sorted_opp_durs = list(opp_durs)
        sorted_opp_durs.sort()

        opp_dur_view = self.opp.copy()
        sdict = get_style_dict(opp_dur_view)
        sdict.update({
            c: lambda x: f'{TimedeltaView(x).normal_microseconds():.0f}'
            for c in dur_cols
        })

        def get_selector_columns(s):
            def get_dur_formatter(col):
                return lambda x: OppDurView.get_dur_selector_column(
                    opp_dur_view, col, sorted_opp_durs)

            # The dur_formatter lambdas must be created in a separate function (not inline),
            # because of the way capture works (or arguably doesn't) in loops:
            # https://stackoverflow.com/questions/2295290/what-do-lambda-function-closures-capture
            formatters = {col: get_dur_formatter(col) for col in dur_cols}
            if s.name in formatters:
                return formatters[s.name](s)
            even_odd = ['even', 'odd']
            default_css = [
                even_odd[i % 2] for i in range(1,
                                               len(opp_dur_view) + 1)
            ]
            res = pd.DataFrame(data={'default_css': default_css})
            return res.apply(lambda r: f'cell-{r["default_css"]}', axis=1)

        selector_cols = opp_dur_view.apply(get_selector_columns)
        even_style = self.even_style
        odd_style = self.odd_style
        hover_style = self.hover_style
        header_style = self.header_style

        table_styles = [{
            'selector': '.cell-even',
            'props': even_style
        }, {
            'selector': '.cell-odd',
            'props': odd_style
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

        append_bucket_styles(opp_durs, OppDurView.fmt_dur_selector)
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

        self.opp_dur_view = opp_dur_view
        self.table_styles = table_styles
        return opp_dur_view.style\
            .format(sdict)\
            .set_td_classes(selector_cols)\
            .set_table_styles(table_styles, overwrite=True)


def to_opp_dur_view(opp_dur, **kwargs):
    opp_dur_buckets = ensure_iterable(
        kwarg_picker.pick(kwargs, 'durs', 'dur', 'opp_durs', 'opp_dur'), None)
    thresholds = ensure_iterable(
        kwarg_picker.pick(
            kwargs, 'threshes', 'thresh', 'thresholds', 'threshold'), None)
    if opp_dur_buckets is None and thresholds is None:
        opp_dur_buckets = {
            pd.Timedelta('0us'):
            CellView(),
            pd.Timedelta('50us'):
            CellView(bg=Colors.gold(), fw='bold'),
            pd.Timedelta('100us'):
            CellView(bg=WebColors.sky_blue(), fw='bold'),
            pd.Timedelta('500us'):
            CellView(bg=Colors.lightgreen_pastel(), fw='bold')
        }

    ov = OppDurView(
        opp_dur.head(320), opp_durs=opp_dur_buckets, thresholds=thresholds)
    return ov


def display_opp_dur_view(odv, **kwargs):
    dur_cols = ensure_iterable(kwarg_picker.pick(kwargs, 'dur_cols', 'dur_col'), None) or\
        [c for c, t in filter(
            lambda tup: pd.api.types.is_timedelta64_dtype(tup[1]),
            zip(odv.opp.columns, odv.opp.dtypes))]
    res = odv.display(verbose=None, dur_cols=dur_cols)
    return res.format(
        {c: lambda x: TimedeltaView(x, fmt='micros')
         for c in dur_cols},
        subset=dur_cols)
