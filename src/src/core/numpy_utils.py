import numpy as np

def fill(sz, val):
    rv = np.empty(sz)
    rv.fill(val)
    return rv
