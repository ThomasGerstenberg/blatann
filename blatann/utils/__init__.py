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
        self._t_mark = 0
        self._is_running = False
        self._started = False

    def start(self):
        self._t_start = time.perf_counter()
        self._t_stop = 0
        self._started = True
        self._is_running = True

    def stop(self):
        if self._is_running:
            self._t_stop = time.perf_counter()
            self._is_running = False

    def mark(self):
        if self._is_running:
            self._t_mark = time.perf_counter()

    @property
    def is_running(self):
        return self._is_running

    @property
    def start_time(self):
        return self._t_start

    @property
    def stop_time(self):
        return self._t_stop

    @property
    def elapsed(self):
        if not self._started:
            raise RuntimeError("Timer was never started")
        if self._is_running:
            if self._t_mark == 0:
                return time.perf_counter() - self._t_start
            return self._t_mark - self._t_start
        return self._t_stop - self._t_start

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return self
