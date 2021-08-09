from src.core.postgres_connection import PostgresConnection
from src.core.iter_utils import ensure_iterable

import math
import pandas as pd


class SyntheticSecurityLoader:
    def __init__(self, **kwargs):
        self.__symbols = ensure_iterable(
            kwargs.get('symbols') or kwargs.get('symbol')
            or kwargs.get('syms'), None)
        self.__pg_conn = kwargs.get('pg_conn') or kwargs.get(
            'conn') or PostgresConnection(host='titan')
        self.__result = None

    @staticmethod
    def load_fees(synthetic_security_leg, fee):
        synth_fee = pd.merge(
            synthetic_security_leg,
            fee,
            on=['product_type', 'exchange', 'venue', 'security_type'],
            how='left')
        synth_fee['fee'] = synth_fee['n_legs'] * synth_fee['fee']
        member_types = synth_fee['member_type'].unique()

        def impl(x):
            by_member_type = x.groupby('member_type')

            def get_member_type_fee(mt):
                if mt in by_member_type.groups:
                    mtg = by_member_type.get_group(mt)
                    return mtg['fee'].sum()
                return math.nan

            data = {'id': [x.name]}
            for mt in member_types:
                data[mt] = [get_member_type_fee(mt)]
            return pd.DataFrame(data=data)

        res = synth_fee.groupby('sid').apply(impl)
        res = res.set_index(res.index.get_level_values('sid'))
        return res

    def result(self):
        if self.__result is None:
            conn = self.__pg_conn.connect()
            synth_leg = pd.read_sql(
                'select * from synthetic_security_leg',
                conn).drop(columns='index')
            product_fee = pd.read_sql('select * from product_fee',
                                      conn).drop(columns='index')
            synth_fee = SyntheticSecurityLoader.load_fees(
                synth_leg, product_fee)
            synth_sec = pd.read_sql('select * from synthetic_security', conn)
            if self.__symbols is not None:
                synth_sec = synth_sec.loc[synth_sec['symbol'].isin(
                    self.__symbols)]
            self.__result = pd.merge(synth_sec, synth_fee, on='id')
        return self.__result
