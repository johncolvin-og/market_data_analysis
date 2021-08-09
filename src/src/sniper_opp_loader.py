from src.core.postgres_connection import PostgresConnection
from src.synthetic_book_loader import SyntheticBookLoader
from src.core.iter_utils import ensure_iterable, is_none_or_empty
import src.core.kwarg_picker as kwarg_picker
from src.core.stopwatch_logger import StopwatchLogger

import pandas as pd
import numpy as np
# from pandas.api.types import union_categoricals
import sqlite3


class CommonArgs:
    @staticmethod
    def channels(kwargs):
        return ensure_iterable(
            kwarg_picker.pick(kwargs, 'channels', 'channel', 'chs', 'ch'),
            None)

    @staticmethod
    def symbols(kwargs):
        return ensure_iterable(
            kwarg_picker.pick(kwargs, 'symbols', 'symbol', 'syms', 'sym'),
            None)

    @staticmethod
    def market_dates(kwargs):
        return ensure_iterable(
            kwarg_picker.pick(
                kwargs, 'market_dates', 'market_date', 'dates', 'date'), None)

    @staticmethod
    def table_name(kwargs, default=None):
        return kwarg_picker.pick_or(kwargs, default, 'table', 'table_name')


def uncommon_poly_regex():
    return '^(\+[1-9]|.*:.*)'


def get_sorted_market_dates(market_dates):
    if market_dates is None:
        return None
    sorted_market_dates = [
        d if isinstance(d, pd.Timestamp) else pd.Timestamp(d)
        for d in market_dates
    ]
    sorted_market_dates.sort()


def fmt_query_vals(vals, wrap_in_quotes=False):
    if isinstance(vals, str):
        return vals
    vals = ensure_iterable(vals)

    def fmt_val(v):
        rv = v if isinstance(v, str) else str(v)
        if wrap_in_quotes:
            rv = f"'{rv}'"
        return rv

    rv = ', '.join(map(fmt_val, vals))
    return rv


def fmt_query_in_vals_clause(name, vals, wrap_in_quotes=False):
    vals_str = fmt_query_vals(vals, wrap_in_quotes)
    rv = f'{name} in ({vals_str})'
    return rv


def _cast_and_filter_sniper_opps(src: pd.DataFrame, **kwargs):
    """The cast procedure is combined with the filtering to reduce the size of the dataframe
    before casting (most) columns. Some columns, however, must be cast before the filter is
    applied, if they are the subject of a particular filter (e.g., symbols and market_dates)."""

    df = src.copy()
    symbols = CommonArgs.symbols(kwargs)
    market_dates = CommonArgs.market_dates(kwargs)

    def cast_col(col_name, type_arg, nan_repl=None):
        if nan_repl is not None:
            df.at[df[col_name].isna(), col_name] = nan_repl
        df[col_name] = df[col_name].astype(type_arg)

    def cast_datetime(col_name, nan_repl=0):
        cast_col(col_name, 'int64', nan_repl)
        df[col_name] = pd.to_datetime(df[col_name], unit='ns')

    def cast_timedelta(col_name, nan_repl=0):
        cast_col(col_name, 'int64', nan_repl)
        df[col_name] = pd.to_timedelta(df[col_name], unit='ns')

    df['market_date'] = pd.to_datetime(df['market_date'])
    sym_col = 'poly' if 'poly' in df else 'symbol'
    if 'poly' in df:
        df['symbol'] = df['poly'].astype('category')
        df.drop(columns='poly', inplace=True)
    elif 'symbol' in df:
        df['symbol'] = df['symbol'].astype('category')

    filters = []
    if not is_none_or_empty(market_dates):
        filters.append(df['market_date'].isin(market_dates))
    if not is_none_or_empty(symbols):
        filters.append(df['symbol'].isin(symbols))
    if filters:
        df = df.loc[np.logical_and.reduce(filters)]

    if not is_none_or_empty(symbols):
        df['symbol'] = pd.Categorical(
            df['symbol'], categories=symbols.cat.categories)
    df['run_id'] = df['run_id'].astype('uint32')
    df['opp_id'] = df['opp_id'].astype('uint32')
    df['eid'] = df['eid'].astype('int64')
    cast_col('min_days', 'int', -1)
    cast_col('max_days', 'int', -1)
    cast_col('min_fut_vol', 'int', -1)
    cast_col('entry_ticks', 'int', -1)
    df['side'] = df['side'].astype('category')
    df['has_futures'] = df['has_futures'].astype('bool')
    if 'ht_time' in df:
        df.drop(columns='ht_time', inplace=True)
    cast_datetime('t_time')
    df['t_tod'] = df['t_time'] - df['market_date'] - pd.Timedelta('1d')
    cast_timedelta('fsn_win')
    cast_timedelta('lsn_win')
    df['entry_pnl'] = df['entry_pnl'].astype('float')
    df['is_direct'] = df['is_direct'].astype('bool')
    cast_col('entry_qty', 'uint32', 0)

    df['is_bf'] = df['symbol'].str.contains('BF')
    df['tot_ticks'] = df['entry_ticks'] * df['entry_qty']

    df = df.set_index(['market_date', 'symbol', 'eid']).sort_index()
    return df


def get_channel_runs(conn, channels):
    channel_clause = fmt_query_in_vals_clause('channel', channels)
    runs = pd.read_sql(f'select * from run where {channel_clause}', conn)
    return runs


def from_conn(conn, **kwargs):
    channels = CommonArgs.channels(kwargs)
    symbols = CommonArgs.symbols(kwargs)
    market_dates = CommonArgs.market_dates(kwargs)
    table_name = CommonArgs.table_name(kwargs, 'typed_sniper_opps')
    limit = kwargs.get('limit')
    query = f'select * from {table_name}'
    clauses = ['symbol!=\'\'']
    if channels is not None:
        runs = get_channel_runs(conn, channels)
        clauses.append(fmt_query_in_vals_clause('run_id', runs['run_id']))
    if symbols is not None:
        clauses.append(
            fmt_query_in_vals_clause('symbol', symbols, wrap_in_quotes=True))
    if market_dates is not None:
        clauses.append(
            fmt_query_in_vals_clause(
                'market_date', market_dates, wrap_in_quotes=True))
    query += ' where ' + ' and '.join(clauses)
    if limit is not None:
        query += f' limit {limit}'
    print(f'Reading sql query: {query}')
    df = pd.read_sql(query, conn)
    df = _cast_and_filter_sniper_opps(
        df, dates=get_sorted_market_dates(market_dates))
    return df


def from_sqlite(asset, **kwargs):
    symbols = ensure_iterable(
        kwarg_picker.pick(kwargs, 'symbols', 'symbol', 'syms', 'sym'), None)
    market_dates = ensure_iterable(
        kwarg_picker.pick(
            kwargs, 'market_dates', 'market_date', 'dates', 'date'), None)
    conn = sqlite3.connect(f'/md/SIM_DBs/sim_{asset}.sqlite')
    df = pd.read_sql('select * from sniper_opps', conn)
    return _cast_and_filter_sniper_opps(df, symbols, market_dates)


def from_postgres(**kwargs):
    username = kwarg_picker.pick_or(
        kwargs, 'postgres', 'username', 'user', 'un')
    host = kwarg_picker.pick_or(kwargs, 'localhost', 'host')
    password = kwarg_picker.pick_or(kwargs, 'postgres', 'password', 'pw')
    port = kwarg_picker.pick_or(kwargs, 5432, 'port')
    conn = PostgresConnection(
        host, port=port, username=username, password=password).connect()
    return from_conn(conn, kwargs)


# def from_postgres_simgrains(**kwargs):
#     channels = ensure_iterable(kwarg_picker.pick(kwargs, 'channels', 'channel', 'chs', 'ch'), None)
#     symbols = ensure_iterable(kwarg_picker.pick(kwargs, 'symbols', 'symbol', 'syms', 'sym'), None)
#     market_dates = ensure_iterable(kwarg_picker.pick(kwargs, 'market_dates', 'market_date', 'dates', 'date'), None)
#     limit = kwargs.get('limit')
#     conn = PostgresConnection('10.1.10.72', port=5432, username='postgres', password='KevinSucks1000Dicks').connect()
#     query = 'select * from sim_grains_07_'
#     def in_set_clause(name, values):
#         return f'{name} in ({", ".join(values)})'
#     clauses = ['symbol!=\'\'']
#     if channels is not None:
#         clauses.append(in_set_clause('channel', channels))
#     if symbols is not None:
#         clauses.append(in_set_clause('symbol', symbols))
#     if market_dates is not None:
#         clauses.append(in_set_clause('market_date', market_dates))
#     query += ' where ' + ' and '.join(clauses)
#     if limit is not None:
#         query += f' limit {limit}'
#     df = pd.read_sql(query, conn)
#     df = _cast_and_filter_sniper_opps(df)
#     return df


class SniperOppLoader:
    @staticmethod
    def __pick_log_level(kwargs, default):
        return kwarg_picker.pick_or(kwargs, default, 'log_level', 'log', 'll')

    def __init__(self, channel, **kwargs):
        symbols = ensure_iterable(
            kwarg_picker.pick(kwargs, 'symbols', 'symbol', 'syms', 'sym'),
            None)
        market_dates = ensure_iterable(
            kwarg_picker.pick(
                kwargs, 'market_dates', 'market_date', 'dates', 'date'), None)
        synth_bk = kwarg_picker.pick(kwargs, 'synth_bk')
        synth_sec = kwarg_picker.pick(
            kwargs, 'synthetic_securities', 'synthetic_security',
            'synthetic_secs', 'synthetic_sec', 'synth_secs', 'synth_sec',
            'synths', 'synth')
        opp_roots = kwarg_picker.pick_or(kwargs, {}, 'opp_roots', 'opp_root')
        opps = kwarg_picker.pick_or(kwargs, {}, 'opps', 'opp')
        log_level = SniperOppLoader.__pick_log_level(kwargs, 1)

        pg_conn = PostgresConnection(host='titan').connect()
        if synth_sec is None:
            synth_sec = pd.read_sql(
                'select * from synthetic_security where is_polygon', pg_conn)
        if symbols is not None:
            synth_sec = synth_sec.loc[synth_sec['symbol'].isin(symbols)]
        fee_cols = {
            c: c in synth_sec
            for c in ['nonmember_fee', 'member_fee', 'member106j_fee']
        }
        if any(fee_cols.values()):
            synth_fee = pd.read_sql(
                'select * from synthetic_exchange_fee', pg_conn)
            synth_fee = synth_fee.drop(
                columns=list(
                    map(
                        lambda x: x[0], filter(
                            lambda x: x[1], fee_cols.items()))))
            synth_sec = pd.merge(synth_sec, synth_fee, on='id')
        synth_sec['symbol'] = synth_sec['symbol'].astype('category')

        if market_dates is not None:
            self.__sorted_market_dates = [
                pd.Timestamp(d) for d in market_dates
            ]
            self.__sorted_market_dates.sort()
        self.__channel = channel
        self.__market_dates = market_dates
        self.__opp_roots = opp_roots
        self.__opp_summs = opps
        self.__synth_sec = synth_sec
        self.__synth_bk = synth_bk
        self.__log_level = log_level

    def synth_bk(self):
        if self.__synth_bk is None:
            synth_bk_loader = SyntheticBookLoader(
                self.__channel, self.__synth_sec, dates=self.__market_dates)
            self.__synth_bk = synth_bk_loader.load_synth_book(
                load_in_parallel=True, log_level=self.__log_level)
        return self.__synth_bk

    def synth_sec(self):
        return self.__synth_sec

    def load_asset_opp_root(self, key='', **kwargs):
        """Loads the core data, from which opps """
        if key in self.__opp_roots:
            return self.__opp_roots[key]

        def fmt_len_vals(x):
            return 'all' if x is None else len(x)

        log_level = SniperOppLoader.__pick_log_level(kwargs, self.__log_level)
        symbols = self.__synth_sec['symbol']
        conn = kwarg_picker.pick_or(
            kwargs, sqlite3.connect(f'/md/SIM_DBs/sim_{key}.sqlite'), 'conn')

        with StopwatchLogger(
                f'loading \'{key}\' ({fmt_len_vals(symbols)} symbols, {fmt_len_vals(self.__market_dates)} dates)',
                log_level=log_level):
            df = from_conn(
                conn,
                channel=self.__channel,
                symbol=symbols,
                dates=self.__market_dates,
                table_name=CommonArgs.table_name(kwargs),
                limit=kwargs.get('limit'))
            self.__opp_roots[key] = df
            return df

    def load(self, key='', **kwargs):
        if key in self.__opp_summs:
            return self.__opp_summs[key]

        log_level = SniperOppLoader.__pick_log_level(kwargs, self.__log_level)
        df = self.load_asset_opp_root(key, log_level=log_level).copy()

        cols_to_drop = [
            'exit_pbook', 'entry_ev', 'entry_pbook', 'entry_pbook_dir',
            'entry_leg_books', 'exit_event', 'exit_pbook', 'exit_pbook_dir',
            'exit_leg_books', 'cp1_win', 'cp1_pbook', 'cp1_pbook_dir',
            'cp2_win', 'cp2_pbook', 'cp2_pbook_dir', 't_time'
        ]
        cols_to_drop = [c for c in cols_to_drop if c in df]
        df = self.load_asset_opp_root(
            key, log_level=log_level).copy().drop(columns=cols_to_drop)
        self.__opp_summs[key] = df
        return df
