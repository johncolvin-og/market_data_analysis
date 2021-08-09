import os.path
import datetime
import pandas as pd
from src.core.iter_utils import ensure_iterable
from calendar import monthrange
from os.path import isfile


class PCapLocationParams:
    def __init__(self, channel=None, date=None, store_root=None):
        self.__channel = channel
        self.__date = date
        self.__store_root = store_root if store_root is not None else '~/spartan_store/pcaps'
        self.__store_root = os.path.expanduser(self.__store_root)

    @staticmethod
    def fmt_date(value=None, **kwargs):
        if isinstance(value, str):
            try:
                value = pd.Timestamp(value)
            except Exception as e:
                print(
                    f'PCapLocationParams unable to convert \'{value}\' to pd.Timestamp: {e}'
                )
                value = pd.Timestamp()

        def ymd_impl():
            year = kwargs.get('year') or kwargs.get('y')
            month = kwargs.get('month') or kwargs.get('m')
            day = kwargs.get('day') or kwargs.get('d')
            return (year, month, day) if not (
                year is None and month is None and day is None) else None

        def date_impl():
            dt = kwargs.get('datetime') or kwargs.get('date') or kwargs.get(
                'dt')
            return (dt.year, dt.month, dt.day) if dt is not None else None

        def timestamp_impl():
            ts = kwargs.get('timestamp') or kwargs.get('ts')
            return date_impl(ts.date()) if ts is not None else None

        def value_date_impl():
            return (value.year, value.month,
                    value.day) if isinstance(value, datetime.date) else None

        def value_timestamp_impl():
            return (value.year, value.month,
                    value.day) if isinstance(value, pd.Timestamp) else None

        for fn in [ymd_impl, date_impl, timestamp_impl, value_date_impl,
                   value_timestamp_impl]:
            tup = fn()
            if tup is not None:
                if len(tup) != 3:
                    raise ValueError(f'Improper date components: {tup}')
                return f'{(tup[0] or 0):04}-{(tup[1] or 0):02}-{(tup[2] or 0):02}'
        raise ValueError(
            f'Unable to determine date from the specified arguments: {kwargs}')

    def store_root(self):
        return self.__store_root

    def channel_path(self, channel=None):
        if channel is None:
            channel = self.__channel
        return f'{self.store_root()}/{channel}'

    def date_path(self, channel=None, date=None):
        if channel is None:
            channel = self.__channel
        if date is None:
            date = self.__date
        return f'{self.channel_path(channel)}/{date}_{channel}_24h'

    def pcap_path(self, channel=None, date=None, require_exists=True):
        if channel is None:
            channel = self.__channel
        if date is None:
            date = self.__date
        prefix = self.date_path(channel, date)
        rv = prefix + '.pcap'
        if (os.path.exists(rv)):
            return rv
        rv += '.xz'
        if not require_exists or os.path.exists(rv):
            return rv
        return None

    def feather_cache_path(self, channel=None, date=None):
        return f'{self.date_path(channel, date)}_feather'

    def feather_file_path(
            self,
            name,
            start_frame=None,
            max_frames=None,
            channel=None,
            date=None):
        if channel is None:
            channel = self.__channel
        date = PCapLocationParams.fmt_date(date or self.__date)

        def impl(full_name):
            return f'{self.feather_cache_path(channel, date)}/{full_name}.feather'

        if start_frame is None:
            if max_frames is None:
                return impl(name)
            start_frame = 0
        elif max_frames is None:
            max_frames = 0
        print(f'mxf: {max_frames}: {start_frame}')
        return impl(f'{name}_frames_{start_frame}-{max_frames}')

    @staticmethod
    def all_feather_dates(
            channel, name, month=None, year=None, day=None, store_root=None):
        if month is None:
            month = range(1, 13)
        if year is None:
            year = range(2021, 2026)
        if day is None:
            day = range(1, 32)

        month = ensure_iterable(month)
        year = ensure_iterable(year)
        day = ensure_iterable(day)

        pcap = PCapLocationParams(store_root)
        dates = []
        for y in year:
            for m in month:
                max_days = monthrange(y, m)[1]
                for d in day:
                    if d > max_days:
                        continue
                    date = f'{y}-{m:02}-{d:02}'
                    f = pcap.feather_file_path(
                        name, channel=channel, date=date)
                    if isfile(f):
                        dates.append(date)
        return dates
