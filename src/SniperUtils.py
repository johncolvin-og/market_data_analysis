import pandas as pd
import numpy as np
import os
import sqlite3


def split_kvp(kvp_txt):
    kvp_txt = kvp_txt.replace(": ", ":")
    toks = kvp_txt.strip().split(":")
    assert len(toks) == 2
    return toks[0], toks[1]


class FeedEvent:
    # id: 4734740 ttime: 1612167067272511221 fst: 1612167067273219874 lst: 1612167067273232755 npacks: 2 n_trs: 10 legs: GCJ1-GCM1
    def __init__(self, ev_txt):
        ev_txt = ev_txt.replace(": ", ":")
        kvp_list = ev_txt.strip().split(' ')
        self.fid = int(split_kvp(kvp_list[0])[1])
        self.ttime = int(split_kvp(kvp_list[1])[1])
        self.fstime = int(split_kvp(kvp_list[2])[1])
        self.lstime = int(split_kvp(kvp_list[3])[1])
        self.npacks = int(split_kvp(kvp_list[4])[1])
        self.ntrades = int(split_kvp(kvp_list[5])[1])

    def proc_time(self):
        return self.fstime - self.ttime

    def fs_adv(self):
        return self.lstime - self.fstime


def get_sniper_opps(csv_file):
    rv = pd.read_csv(csv_file)
    # get rid of run headers
    rv = rv[rv['eid'] != 0]
    res = rv
    res = res[res['has_futures'] == 0]
    res = res[~res["poly"].str.contains("\+2")]
    res = res[~res["poly"].str.contains("\-2")]
    res = res[~res["poly"].str.contains("\+3")]
    res = res[~res["poly"].str.contains("\-3")]
    rv = res
    # universal key across all days
    rv['opp_key'] = rv.market_date.map(
        str) + "_" + rv.opp_id.map(str)
    rv['penalty_poly'] = abs(rv['penalty_poly'])
    rv['tot_ticks'] = rv['entry_ticks'] * rv['entry_qty']
    # event columns
    # rv['npacks'] = rv.apply(lambda r: FeedEvent(r['entry_ev']).npacks, axis=1)
    # rv['ntrades'] = rv.apply(
    #     lambda r: FeedEvent(r['entry_ev']).ntrades, axis=1)
    # rv['proc_time'] = rv.apply(lambda r: FeedEvent(
    #     r['entry_ev']).proc_time(), axis=1)
    # rv['fs_adv'] = rv.apply(lambda r: FeedEvent(
    #     r['entry_ev']).fs_adv(), axis=1)
    # rv['fs_adv_ratio'] = rv['fs_adv']/rv['proc_time']
    # rv['adv_time_per_qty'] = rv['fs_adv']/rv['entry_qty']
    return rv
