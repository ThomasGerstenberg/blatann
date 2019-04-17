class BlatannException(Exception):
    pass


class InvalidStateException(BlatannException):
    pass


class InvalidOperationException(BlatannException):
    pass


class TimeoutError(BlatannException):
    pass


class DecodeError(BlatannException):
    pass
