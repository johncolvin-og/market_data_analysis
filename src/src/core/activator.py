def astype(x, typ):
    if not isinstance(x, typ):
        x = typ(x)
    return x