import pandas as pd
import math
import numpy as np
import src.core.kwarg_picker as kwarg_picker


class TimedeltaView:
    """Encapsulates formatting logic for pd.Timedelta"""
    def __init__(
            self,
            value: pd.Timedelta,
            show_leading_zeros=False,
            show_micros=False,
            **kwargs):
        self.value = value
        self.show_leading_zeros = show_leading_zeros
        self.show_micros = show_micros
        self.fmt = kwarg_picker.pick(kwargs, 'fmt')
        self.n_decimals = kwarg_picker.pick(kwargs, 'n_decimals')

    def days(self):
        return self.value.components[0]

    def hours(self):
        return self.value.components[1]

    def minutes(self):
        return self.value.components[2]

    def seconds(self):
        return self.value.components[3]

    def milliseconds(self):
        return self.value.components[4]

    def normal_microseconds(self):
        """Because pandas represents negative time components stupidly. 
        Case in point: -1 min is represented '-1 day + 23:59.  Wow, that's just awful."""
        negate = self.value < pd.Timedelta(0, unit='us')
        nval = -self.value if negate else self.value
        us = nval.value / 1000
        return -us if negate else us

    @staticmethod
    def __str_impl__(value, show_leading_zeros, show_micros, fmt, n_decimals):
        if type(value) != pd.Timedelta:
            return str(type(value))
        float_selectors = {
            'micros': lambda x: x.value / 1000,
            'millis': lambda x: x.value / 1000_000,
            'secs': lambda x: x.total_seconds()
        }
        if fmt in float_selectors:
            display_val = float_selectors[fmt](value)
            if n_decimals is not None:
                return '{:.{prec}f}'.format(display_val, prec=n_decimals)
            return str(int(display_val))
        if fmt == 'nanos':
            return str(value.value)
        comps = value.components

        def get_subseconds():
            if show_micros:
                return f'{value.microseconds:06}'
            nonlocal n_decimals
            if n_decimals is None:
                n_decimals = 3
            elif not isinstance(n_decimals, int):
                raise ValueError('n_decimals must be int')
            else:
                n_decimals = min(6, max(0, n_decimals))
            return f'{value.microseconds:06}'[0:n_decimals]

        if comps[0] != 0:
            return f'{comps[0]}d, {comps[1]:02}:{comps[2]:02}:{comps[3]:02}.{get_subseconds()}'
        if show_leading_zeros or comps[1] != 0:
            return f'{comps[1]:02}:{comps[2]:02}:{comps[3]:02}.{get_subseconds()}'
        if comps[2] != 0:
            return f'{comps[2]:02}:{comps[3]:02}.{get_subseconds()}'
        return f'{comps[3]:02}.{get_subseconds()}'

    def __str__(self):
        """
        Python's str representation of negative timedelta's is absolutely horrendous.
        -2 minutes is displayed as: -1 day, 23:58:00...words cannot describe how ugly that is.
        Why stop at timedelta's?  Why display -1 as "-1", when you could call it '-1000 + 999'?!
        """
        if self.value < pd.Timedelta(0):
            return '-' + TimedeltaView.__str_impl__(
                -self.value, self.show_leading_zeros, self.show_micros,
                self.fmt, self.n_decimals)
        return TimedeltaView.__str_impl__(
            self.value, self.show_leading_zeros, self.show_micros, self.fmt,
            self.n_decimals)


class DatetimeView:
    """Encapsulates formatting logic for pd.Datetime"""
    def __init__(
            self,
            value: np.datetime64,
            show_year=True,
            show_month=True,
            show_day=True,
            show_time=True,
            fmt=None):
        self.value = value
        if fmt != None:
            return
        fmt = ''
        if show_month:
            fmt += '%m-'
        if show_day:
            fmt += '%d-'
        if show_year:
            fmt += '%y'
        if len(fmt) > 0 and fmt[:1] == '-':
            fmt = fmt[:-1]
        if show_time:
            if len(fmt) > 0:
                fmt += ' '
            fmt += '%hh:mm:ss'
        self.fmt = fmt

    def __str__(self):
        return str(self.value)
        # return str(type(self.value))
        # self.value.strftime(self.fmt)


def fmt_timedelta(value: pd.Timedelta, show_leading_zeros=False):
    """Formats Timedelta as hh:mm:ss"""
    return str(TimedeltaView(value, show_leading_zeros))


def fmt_date(value: np.datetime64):
    """Formats Datetime as mm-dd-yyyy"""
    return str(
        DatetimeView(value, show_year=True, show_month=True, show_day=True))


def fmt_float_lambda(**kwargs):
    fmt = kwarg_picker.pick(kwargs, 'fmt', 'format')
    if fmt is None:
        ndecimals = kwarg_picker.pick(kwargs, 'ndecimals', 'ndec')
        if ndecimals is not None:
            fmt = '{' + ':.{}f'.format(ndecimals) + '}'
        else:
            fmt = '{}'
    nanfmt = kwarg_picker.pick(kwargs, 'nanfmt', 'nan_format') or ''
    return lambda x: nanfmt if math.isnan(x) else fmt.format(x)


def fmt_float(value, **kwargs):
    return fmt_float_lambda(kwargs)(value)


def fmt_datetime(value: np.datetime64):
    """Formats Datetime as mm-dd-yyyy hh:mm:ss"""
    return str(
        DatetimeView(
            value,
            show_year=True,
            show_month=True,
            show_day=True,
            show_time=True))


def get_style_dict(value: pd.DataFrame, style={}):
    for cname, ctype in zip(value.columns, value.dtypes):
        if pd.api.types.is_datetime64_dtype(ctype):
            style[cname] = lambda x: str(DatetimeView(x))
        elif pd.api.types.is_timedelta64_dtype(ctype):
            style[cname] = lambda x: str(TimedeltaView(x))
    return style


def with_groupby_origin_col(df, by=None, **kwargs):
    by = kwarg_picker.pick(kwargs, 'by')
    levels = kwarg_picker.pick(kwargs, 'level', 'levels')
    out_col = kwarg_picker.pick_or(
        kwargs, 'is_origin', 'out', 'out_col', 'col_name', 'col')
    if isinstance(df, pd.core.groupby.generic.DataFrameGroupBy):

        def impl(x):
            x[out_col] = False
            if len(x) > 0:
                x.iat[0, x.columns.get_loc(out_col)] = True
            return x

        return df.apply(impl)
    elif isinstance(df, pd.DataFrame):
        df[out_col] = False
        col_idx = df.columns.get_loc(out_col)

        def impl(x):
            if len(x) > 0:
                x.iat[0, col_idx] = True
            return x

        if levels is not None:
            return df.groupby(level=levels).apply(impl)
        elif by is not None:
            return df.groupby(by).apply(impl)
    raise ValueError('Inappropriate parameters')


def print_types_table(value: pd.DataFrame):
    print(str(pd.DatetimeIndex))
    widths = [19, 19, 10, 10, 14, 14]
    fmt_str = "{:{}s}: {:{}s} {:{}s} {:{}s} {:{}s} {:{}s} {:s}"
    print(
        fmt_str.format(
            'name', widths[0], 'type', widths[1], 'is_float', widths[2],
            'is_int', widths[3], 'is_timedelta', widths[4], 'is_datetime',
            widths[5], 'type_str'))
    for cname, ctype in zip(value.columns, value.dtypes):
        is_float = ctype == float
        is_int = ctype == int
        is_timedelta = pd.api.types.is_timedelta64_dtype(ctype)
        is_datetime = pd.api.types.is_datetime64_dtype(ctype)
        type_str = str(type(ctype))
        print(
            fmt_str.format(
                cname,
                widths[0], str(ctype), widths[1], str(is_float), widths[2],
                str(is_int), widths[3], str(is_timedelta), widths[4],
                str(is_datetime), widths[5], type_str))


def to_html_attributes(attributes: dict):
    return '; '.join(
        map(lambda kv: '{}: {}'.format(kv[0], kv[1]), attributes.items()))


def highlight_max(
        data, attributes={
            'color': 'white',
            'background-color': 'darkred'
        }):
    '''Highlight the maximum in a Series or DataFrame'''
    html_attrs = to_html_attributes(attributes)
    if data.ndim == 1:
        # Series from .apply(axis=0 or 1)
        is_max = data == data.max()
        return [html_attrs if v else '' for v in is_max]
    else:
        # from .apply(axis=None)
        is_max = data == data.max().max()
        return pd.DataFrame(
            np.where(is_max, html_attrs, ''),
            index=data.index,
            columns=data.columns)
