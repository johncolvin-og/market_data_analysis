import time
import pandas as pd


class Stopwatch:
    def __init__(self):
        self.__start = None
        self.__stop = None
        self.__elapsed = 0
        self.__is_running = False

    def start(self):
        if not self.__is_running:
            self.__start = time.time_ns()
            self.__is_running = True

    def stop(self):
        if self.__is_running:
            self.__stop = time.time_ns()
            self.__is_running = False
            self.__elapsed += self.__stop - self.__start

    def reset(self):
        self.__is_running = False
        self.__elapsed = 0

    def elapsed_ns(self):
        return self.__elapsed

    def elapsed(self):
        return pd.Timedelta(self.__elapsed, unit='ns')
