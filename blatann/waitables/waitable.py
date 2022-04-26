from typing import Callable
import queue
from blatann.exceptions import TimeoutError


class Waitable(object):
    """
    Base class for an object which can be waited on for an operation to complete.
    This is a similar concept to :class:`python:concurrent.futures.Future` where asynchronous
    operations can block the current thread, or register a handler to be called when it completes.
    """
    def __init__(self, n_args=1):
        self._queue = queue.Queue()
        self._callback = None
        self._n_args = n_args
        if n_args < 1:
            raise ValueError()

    def wait(self, timeout: float = None, exception_on_timeout=True):
        """
        Waits for the asynchronous operation to complete

        .. warning::
           If this call times out, it cannot be (successfully) called again as it will clean up all event handlers for the waitable.
           This is done to remove lingering references to the waitable object through event subscriptions

        :param timeout: How long to wait, or ``None`` to wait indefinitely
        :param exception_on_timeout: Flag to either throw an exception on timeout, or instead return ``None`` object(s)
        :return: The result of the asynchronous operation
        :raises: TimeoutError
        """
        did_timeout = False
        try:
            results = self._queue.get(timeout=timeout)
            if len(results) == 1:
                return results[0]
            return results
        except queue.Empty:
            did_timeout = True

        if did_timeout:
            self._on_timeout()
            if exception_on_timeout:
                raise TimeoutError("Timed out waiting for event to occur. "
                                   "Waitable type: {}".format(self.__class__.__name__))

        if self._n_args == 1:
            return None
        return [None] * self._n_args

    def then(self, callback: Callable):
        """
        Registers a function callback that will be called when the asynchronous operation completes

        .. note:: Only a single callback is supported-- subsequent calls to this method will overwrite previous callbacks

        :param callback: The function to call when the async operation completes
        :return: This waitable object
        """
        if callback and not callable(callback):
            raise ValueError(f"Callback provided is not callable (got {callback}).")
        self._callback = callback
        return self

    def _on_timeout(self):
        pass

    def _notify(self, *results):
        self._queue.put(results)
        if self._callback:
            self._callback(*results)


class GenericWaitable(Waitable):
    """
    Simple wrapper of a Waitable object which exposes a ``notify``
    method so external objects can signal/trigger the waitable's response
    """
    def notify(self, *results):
        self._notify(*results)


class EmptyWaitable(Waitable):
    """
    Waitable class which will immediately return the args provided when waited on
    or when a callback function is registered
    """
    def __init__(self, *args):
        super(EmptyWaitable, self).__init__(len(args))
        self._args = args

    def wait(self, timeout=None, exception_on_timeout=True):
        return self._args

    def then(self, callback):
        if callback and callable(callback):
            callback(*self._args)
        return self
