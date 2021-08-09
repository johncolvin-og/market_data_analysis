def pick_or(kwargs, default, *kws):
    for kw in kws:
        if kw in kwargs:
            return kwargs[kw]
    return default

def pick(kwargs, *kws):
    return pick_or(kwargs, None, *kws)
