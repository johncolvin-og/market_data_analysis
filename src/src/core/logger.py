import time
import pandas as pd

def log_level_name(level):
    if level == 0:
        return 'Diag'
    elif level == 1:
        return 'Info'
    elif level == 2:
        return 'Warn'
    elif level == 3:
        return 'Error'
    return str(level)

def log(msg, level = 0, timestamp = None):
    if timestamp is None:
        timestamp = pd.Timestamp(time.time_ns(), unit="ns")
    print(f'[{log_level_name(level): <5}] [{timestamp}]  |  {msg}')

class Logger:
    def __init__(self, log_level):
        self.__log_level = log_level

    def log(self, msg, log_level = 0, timestamp = None):
        if log_level >= self.__log_level:
            log(msg, log_level, timestamp)

