import pandas as pd
import math
from src.pcap_location_params import PCapLocationParams

def get_book_level_changes(synth_book, **kwargs):
    pcol_name = kwargs.get('pcol')
    qcol_name = kwargs.get('qcol')
    level = kwargs.get('level')
    side = kwargs.get('side')
    if level is not None and side is not None:
        pcol_name = f'{side}_p_{level}'
        qcol_name = f'{side}_q_{level}'

    def try_get_col(col_name):
        if col_name in synth_book:
            return synth_book[col_name]
        return None

    pcol = try_get_col(pcol_name)
    qcol = try_get_col(qcol_name)

    if pcol is None and qcol is None:
        raise ValueError(f'Inappropriate parameters: {kwargs}')

    pchange = None
    qchange = None
    change = None
    if pcol is not None:
        pchange = (pcol != pcol.shift(1)) & ((pcol.isna() == False) | (pcol.shift(1).isna() == False))
    if qcol is not None:
        qchange = qcol != qcol.shift(1)

    if qcol is None:
        change = pchange
    elif pcol is None:
        change = qchange
    else:
        change = qchange | pchange
    return change

def to_price_changes_only(bbo, **kwargs):
    bid_col = kwargs.get('bid') or kwargs.get('bid_col')
    ask_col = kwargs.get('ask') or kwargs.get('ask_col')
    if bid_col not in bbo:
        bid_col = 'bid_p_1'
    if ask_col not in bbo:
        ask_col = 'ask_p_1'
    bbo[f'delta_{bid_col}'] = bbo[bid_col] - bbo[bid_col].shift(-1)
    bbo[f'delta_{ask_col}'] = bbo[ask_col] - bbo[ask_col].shift(-1)
    bbo[f'{bid_col}_change'] = get_book_level_changes(bbo, pcol = bid_col)
    bbo[f'{ask_col}_change'] = get_book_level_changes(bbo, pcol = ask_col)
    bbo = bbo.loc[bbo[f'{bid_col}_change'] | bbo[f'{ask_col}_change']]
    return bbo

def load_bbo(channel, date, name = 'gc_sgu_bbo', security = None, **kwargs):
    path = PCapLocationParams(channel).feather_file_path(name, date=date)
    if kwargs.get('test'):
        return pd.read_feather(path)
#     epath = PCapLocationParams(channel).feather_file_path(name='event_info', date=date)
#     event_info = pd.read_feather(epath)
    if security is None:
        security = load_security(channel, date)
    bbo = pd.read_feather(path)
    for side in ['bid', 'ask']:
        bbo.loc[bbo[f'{side}_q_1'] == 0, f'{side}_p_1'] = math.nan
        print(len(bbo.loc[bbo[f'{side}_q_1'] == 0]))
        print(bbo[f'{side}_p_1'].isna().sum())

    for side in ['bid', 'ask']:
        bbo.loc[bbo[f'{side}_q_1'] == 0, f'{side}_p_1'] = math.nan
        print(len(bbo.loc[bbo[f'{side}_q_1'] == 0]))

    bbo = bbo.drop(columns=[f'{side}_{prop}_{i}' for side in ['bid', 'ask'] for prop in ['q', 'no'] for i in range(1,2)])
    bbo = bbo.rename(columns={f'{side}_p_1': side for side in ['bid', 'ask']})
    for side in ['bid', 'ask']:
        bbo.loc[bbo[f'{side}'] == 0, f'{side}'] = math.nan
        print(bbo.loc[bbo[f'{side}'].isna().sum()])
    bbo = bbo.loc[bbo['status'] == 'READY_TO_TRADE']
    bbo = pd.merge(
        bbo, security[['sid', 'symbol', 'asset', 'sec_group']].rename(columns={'sid': 'rsid'}),
        left_on='sid', right_on='rsid', how='left')\
        .drop(columns=['rsid'])

def synth_top_bk_side(bbo, legs):
    synthp = np.sum([p * legq for p, q, legq in legs])
    synthq = np.min([(q / legq).astype('int') for p, q, legq in legs], axis=1)


def get_synth_bbo(left, right):
    left['left_bid_nan'] = left['bid'].isna()
    left['left_ask_nan'] = left['ask'].isna()
    left['left_eid'] = left.index.get_level_values('eid')
    left = left.rename(columns={'bid': 'left_bid', 'ask': 'left_ask', 't_time': 'left_t_time'})[['left_bid', 'left_ask', 'left_eid', 'left_t_time', 'left_bid_nan', 'left_ask_nan']]

    right['right_bid_nan'] = right['bid'].isna()
    right['right_ask_nan'] = right['ask'].isna()
    right['right_eid'] = right.index.get_level_values('eid')
    right = right.rename(columns={'bid': 'right_bid', 'ask': 'right_ask', 't_time': 'right_t_time'})[['right_bid', 'right_ask', 'right_eid', 'right_t_time', 'right_bid_nan', 'right_ask_nan']]

    res = pd.concat(objs=[left, right])
    res = res.sort_index()
    res['t_time'] = res[['left_t_time', 'right_t_time']].apply(max, axis=1)
    to_fill = ['left_bid', 'left_ask', 'left_eid', 'left_t_time', 'left_bid_nan', 'left_ask_nan', 'right_bid', 'right_ask', 'right_eid', 'right_t_time', 'right_bid_nan', 'right_ask_nan']
    res[to_fill] = res[to_fill].fillna(method='ffill')
    for side in ['left', 'right']:
        res[f'{side}_eid'] = res[f'{side}_eid'].fillna(-1)
        res[f'{side}_eid'] = res[f'{side}_eid'].astype('int')
        for mktside in ['bid', 'ask']:
            res.loc[res[f'{side}_{mktside}_nan'].astype('bool'), f'{side}_{mktside}'] = math.nan
    res['bid'] = res['left_bid'] + res['right_bid']
    res['ask'] = res['left_ask'] + res['right_ask']
    return res

# def merge_leg_bks(leg1, leg2):
#     leg1 = leg1.rename(columns={'eid': 'eid1'})
#     leg2 = leg2.rename(columns={'eid': 'eid2'})
#     synth_bk = pd.merge_asof(leg1, leg2, left_on = 'eid1', right_on = 'eid2', direction='backward')
#     synth_bk = synth_bk.set_index('eid1')
#     leg2['eid1'] = synth_bk['eid1']
#     leg2 = leg2.rename(columns={'eid2': 'eid2_rem'})
#     synth_bk.append()
#     synth_bk = pd.merge_asof(leg2, synth_bk, left_on='eid2_rem', right_on = 'eid2', direction = 'backward')

#     pcols = [p * legq for p, legq, rem in legs]
#     margq = [(q + rem) for p, legq, rem in legs]
#     unitq = [(q + rem) / legq for p, legq, rem]
# #     old_qcols = [ - for p, legq, rem in legs]
#     qcols = [(q + rem) / legq for p, legq, rem in legs]
#     synthp = np.sum(pcols * qcols)


class Book:
    def __init__(self, b_bk_arg, a_bk_arg):
        self.b_bk = b_bk_arg
        self.a_bk = a_bk_arg
    def to_string(self, n_levels):
        return self.b_bk.to_string(n_levels) + ' ; ' + self.a_bk.to_string(n_levels)

