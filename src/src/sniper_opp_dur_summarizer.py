import pandas as pd
import src.core.kwarg_picker as kwarg_picker
from src.core.iter_utils import ensure_iterable
from src.core.errors import UnexpectedTypeError


def fmt_quantile_col(q, prefix=None, suffix=None):
    rv = str(q) if isinstance(q, int) else str(int(100 * q))
    if prefix is not None:
        rv = f'{prefix}_{rv}'
    if suffix is not None:
        rv = f'{rv}_{suffix}'
    return rv


def get_opp_dur_summary(opps, **kwargs):
    quantiles = ensure_iterable(
        kwarg_picker.pick(kwargs, 'quantiles', 'quantile')
        or [0.1 * i for i in range(1, 10)])
    dur_cols = ensure_iterable(
        kwarg_picker.pick_or(kwargs, ['lsn_win', 'fsn_win'], 'durs', 'dur'))
    threshes = ensure_iterable(
        kwarg_picker.pick(
            kwargs, 'threshes', 'thresh', 'thresholds', 'threshold'), None)

    def thresh_impl(x):
        thresh_df = pd.DataFrame(
            data=dict([('n_opps', [len(x)])] + [(
                f'{c}>={int(t.value / 1000)}us', [len(x.loc[x[c] > t])])
                                                for t in threshes
                                                for c in dur_cols]))
        return thresh_df

    def dur_impl(x):
        return pd.DataFrame(
            data=dict([('n_opps', [len(x)])] +
                      [(fmt_quantile_col(q, prefix=col), [x[col].quantile(q)])
                       for q in quantiles for col in dur_cols]))

    impl = dur_impl if threshes is None else thresh_impl
    if isinstance(opps, pd.DataFrame):
        return impl(opps)
    if isinstance(opps, pd.core.groupby.DataFrameGroupBy):
        return opps.apply(impl)
    raise UnexpectedTypeError(
        name='opps',
        actual=type(opps),
        expected=[pd.DataFrame, pd.core.groupby.DataFrameGroupBy])
