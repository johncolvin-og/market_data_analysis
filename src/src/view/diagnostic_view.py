from src.view.cell_view import CellView
import pandas as pd


def fmt_table_styles(table_styles):
    for ts in table_styles:
        sel = ts.get('selector')
        if sel is None:
            continue
        for k, v in ts.items():
            if isinstance(v, CellView):
                print(
                    f'{sel}.{k}: {str(v.to_tuples()[0][0]) + "." + str(v.to_tuples()[0][1])}'
                )
                print(
                    map(
                        lambda tup: str(tup[0]) + "." + str(tup[1]),
                        v.to_tuples()))
            elif isinstance(v, str):
                print(f'{sel}.{k}: {v}')
            else:
                continue
            props = ts.get('props')
            if props is not None:
                print(
                    '\t' + '\n\t'.join(
                        map(
                            lambda tup: str(tup[0]) + "." + str(tup[1]),
                            props)))


def fmt_types_table(value: pd.DataFrame):
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
