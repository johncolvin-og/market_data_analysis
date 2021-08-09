from core.iter_utils import ensure_iterable
import src.view.data_view as dview
from polygon_value_summarizer import *
from IPython.display import display


def get_heatmap_style(sym_opps: dict, quantiles: list, fmt_quantile_col=None):
    if fmt_quantile_col == None:
        fmt_quantile_col = DurationSummarizer.get_quantile_col
    quantile_cols = list(map(fmt_quantile_col, quantiles))
    style = dview.get_style_dict(next(iter(sym_opps.values())))
    hm_styles = {}
    for month, mopps in sym_opps.items():
        value_thresh = 10
        n_opps_thresh = 2
        print(
            f'{month}: polys with {n_opps_thresh}+ opps worth {value_thresh}+')
        hm = dview.Heatmap(
            steps={
                30: dview.Colors.darkblue(),
                50: dview.Colors.darkred(),
                100: dview.Colors.red(),
                10000: dview.Colors.green()
            },
            interpolate=True)

        def total_us(td):
            return td.components[1] * 60 * 60 * 1000 * 1000 + td.components[
                2] * 60 * 1000 * 1000 + td.components[
                    3] * 1000 + td.components[4]

        get_color = hm.to_lambda()

        def dur_heatmap(data):
            return data.apply(
                lambda x: 'background-color: {}'.format(
                    get_color(total_us(x))))

        quantile_dur_fmts = {}
        for q in quantile_cols:
            quantile_dur_fmts[q] = total_us
        temp = mopps.sort_values(f'n_opps_v{value_thresh}', ascending=False)
        temp = temp.loc[temp[f'n_opps_v{value_thresh}'] >= n_opps_thresh,
                        (temp.columns != 'n_opps') &
                        (temp.columns != 'n_opps_v40')]
        temp = temp.rename(
            columns={
                'n_opps_v10': 'nv10',
                'n_opps_v20': 'nv20',
                'n_opps_v30': 'nv30'
            })
        hm_styles[month] = temp\
            .style.format(style)\
            .format(quantile_dur_fmts)\
            .apply(lambda x: x.apply(hm.to_lambda(total_us)), subset=quantile_cols)
    return hm_styles


class HeatmapSummary:
    def __init__(
            self,
            opps=None,
            months=None,
            quantiles=None,
            min_value=10,
            min_qty=1):
        if opps == None:
            if months == None:
                raise ValueError("'opps' and 'months' cannot both be None")
            opps = map_opp_summary_csvs(months)
        if quantiles == None:
            quantiles = list(reversed([i * .05 for i in range(2, 19)]))
        self.opps = opps
        self.quantiles = quantiles
        self.min_value = min_value
        self.min_qty = min_qty
        self.sym_opps = DurationSummarizer.get_durations_per_polygon(
            opps, min_value=min_value, min_qty=min_qty, quantiles=quantiles)
        self.sym_opp_heatmaps = get_heatmap_style(self.sym_opps, quantiles)

    def display(self, months=None):
        if months is None:
            months = self.sym_opp_heatmaps
        elif type(months) is str:
            months = [months]
        else:
            months = ensure_iterable(months)
        for month in months:
            print(
                f'{month:7s} : opps worth >=${self.min_value} with >={self.min_qty} qty'
            )
            display(self.sym_opp_heatmaps[month])
