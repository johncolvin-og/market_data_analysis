from src.core.logger import Logger
import src.core.kwarg_picker as kwarg_picker
# from src.core.stopwatch import Stopwatch
from src.core.stopwatch_logger import StopwatchLogger
from src.core.chunker import get_chunks
import pandas as pd
# from pandarallel import pandarallel
import numpy as np
# import traceback
from multiprocessing import Pool, cpu_count


class SyntheticBookMerger:
    def __init__(
            self,
            odg,
            synth_bk_date_groupby,
            delay=pd.Timedelta('5000us'),
            show_all_changes=True,
            log_level=0):
        self.__opp_date_groupby = odg
        self.__synth_bk_date_groupby = synth_bk_date_groupby
        self.__delay = delay
        self.__show_all_changes = show_all_changes
        self.__log_level = log_level

    def merge_date(self, date):
        date_opp = self.__opp_date_groupby.get_group(date)
        date_sb = self.__synth_bk_date_groupby.get_group(date)
        logger = Logger(self.__log_level)
        logger.log(f'Adding synth books for {date}', 0)

        def impl(x):
            symbol = x.name[1]
            opp_start_eid = x.name[2]
            sb = date_sb.loc[date, symbol, :]
            sb = sb.reset_index(['eid', 'market_date', 'symbol'])\
                .drop(columns=['market_date', 'symbol'])\
                .rename(columns={'eid': 'synth_bk_eid'})

            sb_start_idx = sb.loc[
                sb['synth_bk_eid'] <= opp_start_eid]['synth_bk_eid'].idxmax()
            sb_start_eid = sb.iloc[sb_start_idx]['synth_bk_eid']
            sb_start_time = sb.iloc[sb_start_idx]['t_time']
            sb_start_time_fsn = sb.iloc[sb_start_idx]['fs_time']
            sb_start_time_lsn = sb.iloc[sb_start_idx]['ls_time']
            sn_delta_fsn = sb_start_time_fsn - sb_start_time
            sn_delta_lsn = sb_start_time_lsn - sb_start_time
            sb_stop_time = sb_start_time + self.__delay
            sb = sb.loc[(sb['synth_bk_eid'] >= sb_start_eid)
                        & (sb['t_time'] <= sb_stop_time)]
            sb['opp_dur'] = sb['t_time'] - sb_start_time
            sb['opp_dur_fsn'] = sb['opp_dur'] - sn_delta_fsn
            sb['opp_dur_lsn'] = sb['opp_dur'] - sn_delta_lsn
            # The amount of 'opp time' until the next bk changes.  This will be handy
            # when looking at the bk updates that occur within some fixed time period
            # of the opp beginning, as the row representing the last bk update within
            # such a window will indicate exactly how long the book persists.
            sb['opp_dur_thru'] = sb['opp_dur'] + sb['bk_dur']
            sb['opp_dur_thru_fsn'] = sb['opp_dur_fsn'] + sb['bk_dur']
            sb['opp_dur_thru_lsn'] = sb['opp_dur_lsn'] + sb['bk_dur']

            # Add opp side, and edge.  This could prob be better optimized
            is_buy_opp = np.where(sb['ask_p_1'] < 0, 1, 0)
            is_sell_opp = np.where(sb['bid_p_1'] > 0, 2, 0)
            sb['side'] = np.choose(
                is_buy_opp + is_sell_opp, [None, 'Buy', 'Sell', 'Invalid'])
            sb['side'] = sb['side'].astype('category')
            sb['edge'] = np.max([-sb['ask_p_1'], sb['bid_p_1']], axis=0)
            return sb

        rv = date_opp.groupby(
            level=['market_date', 'symbol', 'opp_start_eid']).apply(impl)
        rv = rv.set_index([rv.index.get_level_values(i)
                           for i in range(0, 3)] + ['synth_bk_eid'])
        return rv

    def merge_dates(self, dates):
        results = [self.merge_date(d) for d in dates]
        return pd.concat(objs=results)

    def merge(self, **kwargs):
        load_in_parallel = kwargs.get('load_in_parallel') or kwargs.get(
            'parallel') or False
        delay = kwargs.get('delay')
        if delay is None:
            delay = self.__delay

        show_all_changes = kwargs.get('show_all_changes')
        if show_all_changes is None:
            show_all_changes = self.__show_all_changes

        log_level = kwargs.get('log_level')
        if log_level is None:
            log_level = self.__log_level

        logger = Logger(log_level)
        dates = list(self.__opp_date_groupby.groups)

        def series_impl():
            """Gets a 1:1 list of synth-book-data:date"""
            return list(map(self.merge_date, dates))

        def parallel_impl(date_chunks):
            """Gets a 1:1 list of synth-book-data:date_chunk"""
            with Pool(cpu_count()) as p:
                return p.map(self.merge_dates, date_chunks)

        def impl():
            if load_in_parallel:
                parallel_min_sz = kwarg_picker.pick_or(
                    kwargs, 24, 'parallel_min_sz')
                if len(dates) >= parallel_min_sz:
                    min_chunk_sz = kwarg_picker.pick_or(
                        kwargs, 12, 'min_chunk_sz')
                    chunk_sz = max(int(len(dates) / cpu_count()), min_chunk_sz)
                    num_chunks = int(len(dates) / chunk_sz)
                    logger.log(
                        f'Processing in parallel: {num_chunks} chunks of size {chunk_sz} (rem {len(dates) % chunk_sz})'
                    )
                    date_chunks = get_chunks(dates, chunk_sz)
                    return parallel_impl(date_chunks)
                logger.log(
                    'Processing in sequence (insufficient data to justify parallel processing)'
                )
            return series_impl()

        with StopwatchLogger(f'merge opp books for {len(dates)} dates',
                             log_level=log_level):
            merged_date_chunks = impl()
            with StopwatchLogger(
                    f'concatenate date-opp-book chunks ({len(merged_date_chunks)})',
                    log_level=log_level):
                rv = pd.concat(objs=merged_date_chunks)
                return rv


# if __name__ == '__main__':
#     pandarallel.initialize(progress_bar=True, use_memory_fs=True)
