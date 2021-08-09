
def get_synth_bbo(left, right):
    import math
    import pandas as pd

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


class SyntheticSecurityDefinition:
    """Encapsulation of a synthetic spread"""
    
    class Leg:
        # leg_str is in the format stored in the DB
        # ex: +GCJ1, -(GCJ1-GCZ1) etc
        def __init__(self, leg_str):
            self.str = leg_str
            self.leg_qty = 1
            self.contract = ""
            self.is_future = False
            if(self.str[0] == '-'):
                self.leg_qty = -1
            if "(" in leg_str:
                self.contract = leg_str[2:-1]
            else:
                self.is_future = True
                self.contract = leg_str[1:]

        def n_contracts(self):
            if (self.is_future):
                return 1
            else:
                # TODO
                return 2
    # synth_str is in the format stored in the DB
    # ex: +GCJ1 -(GCJ1-GCZ1) -GCZ1
    # TODO: works with unit leg sizes only for now

    def __init__(self, synth_str):
        self.str = synth_str
        self.legs = []
        toks = synth_str.split(' ')
        for t in toks:
            self.legs.append(SyntheticSecurityDefinition.Leg(t))

    def has_future(self):
        for l in self.legs:
            if l.is_future:
                return True
        return False

    def leg_contracts(self):
        rv = []
        for l in self.legs:
            rv.append(l.contract)
        return rv

    def leg_quantities(self):
        rv = []
        for l in self.legs:
            rv.append(l.leg_qty)
        return rv
