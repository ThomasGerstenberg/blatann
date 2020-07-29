import time
import threading
import logging
import sys
import enum

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


def repr_format(obj, *args, **kwargs):
    """
    Helper function to format objects into strings in the format of:
    ClassName(param1=value1, param2=value2, ...)

    :param obj: Object to get the class name from
    :param args: Optional tuples of (param_name, value) which will ensure ordering during format
    :param kwargs: Other keyword args to populate with
    :return: String which represents the object
    """
    items = args + tuple(kwargs.items())
    inner = ", ".join("{}={!r}".format(k, v) for k, v in items)
    return "{}({})".format(obj.__class__.__name__, inner)


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


class SynchronousMonotonicCounter(object):
    """
    Utility class which implements a thread-safe monotonic counter
    """
    def __init__(self, start_value=0):
        self._lock = threading.Lock()
        self._counter = start_value

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        with self._lock:
            value = self._counter
            self._counter += 1
        return value


def snake_case_to_capitalized_words(string: str):
    parts = [p for p in string.split("_") if p]
    words = []
    for p in parts:
        if len(p) == 1:
            words.append(p.upper())
        else:
            words.append(p[0].upper() + p[1:])
    return " ".join(words)


class IntEnumWithDescription(int, enum.Enum):
    def __new__(cls, *args, **kwargs):
        val = args[0]
        obj = int.__new__(cls, val)
        obj._value_ = val
        return obj

    def __init__(self, _, description: str = ""):
        self._description_ = description
        if not self._description_:
            self._description_ = snake_case_to_capitalized_words(self.name)

    @property
    def description(self):
        return self._description_
