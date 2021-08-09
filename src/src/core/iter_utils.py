class HasNextIter(object):
    """An iterator wrapper that provides a 'has_next' fn"""
    def __init__(self, it):
        self.__it = iter(it)
        self.__has_next = None

    def __iter__(self):
        return self

    def next(self):
        if self.__has_next:
            result = self.__next
        else:
            result = next(self.__it)
        self.__has_next = None
        return result

    def has_next(self):
        if self.__has_next is None:
            try:
                self.__next = next(self.__it)
            except StopIteration:
                self.__has_next = False
        else:
            self.__has_next = True
        return self.__has_next


def is_iterable(val, count_str=False):
    if not count_str and isinstance(val, str):
        return False
    try:
        iter(val)
        return True
    except TypeError:
        return False


def is_none_or_empty(val):
    return val is None or (is_iterable(val) and len(val) == 0)


def ensure_iterable(val, if_none=[]):
    if is_iterable(val):
        return val
    return if_none if val is None else [val]


def ensure_len(val):
    if val is None:
        return 0
    try:
        return len(val)
    except:
        return 1


def fmt_iterable(
        iterable, separator=', ', max_explicit_items=4, if_none='None'):
    if iterable is None:
        return if_none
    if hasattr(iterable, '__len__'):
        sz = len(iterable)
        if sz <= max_explicit_items:
            return separator.join(iterable)
        rv = separator.join(
            map(lambda x: str(x), iterable[0:max_explicit_items]))
        rv += f'{separator}and {sz - max_explicit_items} others'
        return rv

    expl = []
    it = HasNextIter(iter(iterable))
    while len(expl) < max_explicit_items and it.has_next():
        expl.append(it.next())
    if it.has_next():
        expl.append('...')
    return separator.join(expl)
