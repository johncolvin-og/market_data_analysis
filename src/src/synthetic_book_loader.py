from src.core.logger import Logger
# from src.core import chunker
from src.core.iter_utils import ensure_iterable, fmt_iterable
from src.pcap_location_params import PCapLocationParams
from src.core.stopwatch_logger import StopwatchLogger
import src.core.kwarg_picker as kwarg_picker

# from multiprocessing import Pool, Process, Manager, cpu_count
from multiprocessing import Pool, cpu_count
import pandas as pd
# import time


def deduce_opp_eids(synth_bk, bid='bid_p_1', ask='ask_p_1'):
    synth_bk = synth_bk.loc[(synth_bk['edge'] > 0) != (
        synth_bk['edge'].shift(-1) > 0)]
    return synth_bk


def _get_dsynth_book(args):
    if len(args) < 4:
        raise ValueError('Expected at least 3 arguments (pcap, date, pids)')
    pcap = args[0]
    date = args[1]
    pids = args[2]
    symbols = args[3]
    log_level = args[4] if len(args) > 4 else 0
    logger = Logger(log_level)
    logger.log(f'Processing {date}', 0)

    def get_psynth_book(pid):
        logger.log(f'[{date}] Processing {date} polygon {pid}', 1)
        try:
            psb = pd.read_feather(
                pcap.feather_file_path(
                    name=f'synthetic_book_{pid}', date=date))
        except Exception as e:
            logger.log(f'Error processing {date} polygon {pid}: {e}', 3)
            return None
        psb['market_date'] = pd.Timestamp(date)
        psb['bk_dur'] = psb.shift(-1)['t_time'] - psb['t_time']
        return psb

    sbs = [get_psynth_book(p) for p in pids]
    logger.log(f'[{date}] Concatenating synth books...', 0)
    sb_df = pd.concat(objs=[sb for sb in sbs if sb is not None])
    if symbols is not None:
        sb_df['symbol'] = pd.Categorical(sb_df['symbol'], categories=symbols)
    else:
        sb_df['symbol'] = sb_df['symbol'].astype('category')

    logger.log(f'[{date}] Loading event info...', 0)
    ei = pd.read_feather(pcap.feather_file_path(
        name='event_info', date=date)).drop(columns='t_time')

    logger.log(f'[{date}] Merging event info...', 0)
    sb_df = pd.merge(sb_df, ei.rename(columns={'eid': 'eidr'}), left_on='eid', right_on='eidr', how='left')\
        .drop(columns='eidr')\
        .set_index(['market_date', 'symbol', 'eid'])\
        .sort_index()
    sb_df['bk_dur_lsn'] = sb_df.shift(-1)['t_time'] - sb_df['ls_time']
    sb_df['bk_dur_fsn'] = sb_df.shift(-1)['t_time'] - sb_df['fs_time']
    return sb_df


class SyntheticBookLoader:
    @staticmethod
    def __pick_symbols(kwargs, default=None):
        return kwarg_picker.pick_or(
            kwargs, default, 'symbols', 'symbol', 'syms', 'sym')

    @staticmethod
    def __pick_market_dates(kwargs, default=None):
        return kwarg_picker.pick_or(
            kwargs, default, 'market_dates', 'market_date', 'dates', 'date')

    @staticmethod
    def __pick_n_levels(kwargs, default=None):
        return kwarg_picker.pick_or(kwargs, default, 'n_levels', 'levels', 'n')

    @staticmethod
    def __pick_log_level(kwargs, default=1):
        return kwarg_picker.pick_or(kwargs, default, 'log_level', 'log', 'll')

    def __init__(
            self, channel: int, synthetic_security_df: pd.DataFrame, **kwargs):
        self.__channel = channel
        # self.__pcap = PCapLocationParams(channel)
        self.__synthetic_security_df = synthetic_security_df
        self.__symbols = SyntheticBookLoader.__pick_symbols(kwargs)
        self.__market_dates = SyntheticBookLoader.__pick_market_dates(kwargs)
        self.__log_level = SyntheticBookLoader.__pick_log_level(kwargs)

        n_levels = SyntheticBookLoader.__pick_n_levels(kwargs)
        if channel is None:
            raise TypeError
        if synthetic_security_df is None:
            raise TypeError
        if n_levels is not None:
            if type(n_levels) is not int:
                raise TypeError
            if n_levels < 1 or n_levels < 5:
                raise ValueError
        self.__n_levels = n_levels

    def get_polygon_ids(self, **kwargs):
        symbols = SyntheticBookLoader.__pick_symbols(kwargs, self.__symbols)
        ss_df = self.__synthetic_security_df
        if symbols is None:
            return ss_df['id']
        symbols = ensure_iterable(symbols)
        return ss_df.loc[ss_df['symbol'].isin(symbols)]['id']

    def load_synth_book(self, **kwargs):
        log_level = SyntheticBookLoader.__pick_log_level(
            kwargs, self.__log_level)
        logger = Logger(log_level)
        load_in_parallel = kwarg_picker.pick(
            kwargs, False, 'load_in_parallel', 'parallel')
        market_dates = SyntheticBookLoader.__pick_market_dates(
            kwargs, self.__market_dates)
        if market_dates is None:
            raise ValueError('market_dates cannot be None')

        symbols = SyntheticBookLoader.__pick_symbols(kwargs, self.__symbols)
        pids = self.get_polygon_ids(symbols=symbols)
        n_levels = SyntheticBookLoader.__pick_n_levels(kwargs, self.__n_levels)

        pcap = PCapLocationParams(self.__channel)
        all_synth_books = []
        # if len(pids) > 12:
        #     raise ValueError(f'Too many pids ({len(pids)})')

        with StopwatchLogger(
                f'loading synth books ({fmt_iterable(symbols, if_none="all")} on '
                f'{fmt_iterable(self.__market_dates, if_none="all")})',
                log_level=1, logger=logger):

            if load_in_parallel:
                with Pool(cpu_count()) as p:
                    # chunks = chunker.get_chunks(market_dates, 4)
                    all_synth_books = p.map(
                        _get_dsynth_book, [(pcap, d, pids, symbols, log_level)
                                           for d in market_dates])
            else:
                all_synth_books = [
                    _get_dsynth_book((pcap, d, pids, symbols, log_level))
                    for d in market_dates
                ]

            with StopwatchLogger(
                    f'Concatenating {len(all_synth_books)} synth book dataframes',
                    log_level=1, logger=logger):
                result = pd.concat(objs=all_synth_books)
                return result
