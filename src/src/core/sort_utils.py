from bisect import bisect_left


def get_within_bounds(value, lo=None, hi=None):
    if lo is not None and value < lo:
        return lo
    if hi is not None and value > hi:
        return hi
    return value


def binary_search(items, value, within_bounds=False):
    idx = bisect_left(items, value)
    return get_within_bounds(idx, 0, len(items) - 1) if within_bounds else idx
