def daterange(start, step=None, stop=None, count=None):
    def on_invalid_args():
        raise ValueError(
            f'invalid arguments (start, stop, step, count): {type(start), type(stop), type(step), type(count)}'
        )

    if start is None or step is None or (stop is None and count is None):
        on_invalid_args()
    if stop is None:
        stop = start + step * count
    rv = []

    # hack to ensure step > 0 without depending on timedelta type
    if (start + step) <= start:
        on_invalid_args()
    date = start
    while date < stop:
        rv.append(date)
        date += step
    return rv
