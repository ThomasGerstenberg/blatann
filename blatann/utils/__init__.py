import time
import logging
import sys
from blatann.utils import _threading


LOG_FORMAT = "[%(asctime)s] [%(threadName)s] [%(name)s.%(funcName)s:%(lineno)s] [%(levelname)s]: %(message)s"


def setup_logger(name=None, level="DEBUG"):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


class Stopwatch(object):
    def __init__(self):
        self._t_start = 0
        self._t_stop = 0
        self._is_running = False

    def start(self):
        self._t_start = time.time_ns()
        self._t_stop = 0
        self._is_running = True

    def stop(self):
        if self._is_running:
            self._t_stop = time.time_ns()
            self._is_running = False

    @property
    def start_time(self):
        return self._t_start

    @property
    def stop_time(self):
        return self._t_stop

    @property
    def elapsed(self):
        return self.elapsed_ns / 1.0E9

    @property
    def elapsed_ms(self):
        return self.elapsed_ns / 1.0E6

    @property
    def elapsed_us(self):
        return self.elapsed_ns / 1.0E3

    @property
    def elapsed_ns(self):
        if self._t_start == 0:
            raise RuntimeError("Timer was never started")
        if self._is_running:
            return time.time_ns() - self._t_start
        return self._t_stop - self._t_start

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return self
