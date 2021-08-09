from src.core.logger import Logger
from src.core.stopwatch import Stopwatch

import traceback


class StopwatchLogger:
    def __init__(self, name, logger: Logger = None, log_level: int = 1):
        self.__name = name
        self.__log_level = log_level
        self.__logger = logger or Logger(log_level)
        self.__stopwatch = Stopwatch()

    def __enter__(self):
        self.__logger.log(f'Begin {self.__name}', self.__log_level)
        self.__stopwatch.start()

    def __exit__(self, ex_typ, ex_val, tb):
        self.__stopwatch.stop()
        self.__logger.log(
            f'End {self.__name}.  Took {self.__stopwatch.elapsed()}',
            self.__log_level)
        if ex_val is not None:
            tb_str = "\n".join(traceback.format_tb(tb))
            self.__logger.log(f'Error ({ex_typ}): {ex_val}\n{tb_str}', 3)
