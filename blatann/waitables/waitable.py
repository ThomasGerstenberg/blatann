from __future__ import annotations

import asyncio
import queue
from typing import Callable, Generic, Optional, TypeVar

from blatann.exceptions import TimeoutError

T = TypeVar("T")


class Waitable(Generic[T]):
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

    def _handle_timeout(self, exception_on_timeout: bool):
        self._on_timeout()
        if exception_on_timeout:
            raise TimeoutError("Timed out waiting for event to occur. "
                               "Waitable type: {}".format(self.__class__.__name__))

        if self._n_args == 1:
            return None
        return [None] * self._n_args

    def wait(self, timeout: float = None, exception_on_timeout=True) -> Optional[T]:
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
        try:
            results = self._queue.get(timeout=timeout)
            if len(results) == 1:
                return results[0]
            return results
        except queue.Empty:
            pass

        # If we got here, the queue timed out. Return the value
        return self._handle_timeout(exception_on_timeout)

    async def as_async(
            self,
            timeout: float = None,
            exception_on_timeout=True,
            loop: asyncio.AbstractEventLoop = None
    ) -> Optional[T]:
        """
        Waits for the asynchronous operation to complete that can be ``await``ed in async methods.

        .. warning::
            This method is experimental!

        :param timeout: How long to wait, or ``None`` to wait indefinitely
        :param exception_on_timeout: Flag to either throw an exception on timeout, or instead return ``None`` object(s)
        :param loop: Optional asyncio event loop to use instead of the default one returned by ``asyncio.get_event_loop()``
        :return: The result of the asynchronous operation
        :raises: TimeoutError
        """
        if loop is None:
            loop = asyncio.get_event_loop()

        fut = loop.create_future()

        def cb(*args):
            if not fut.cancelled():
                if len(args) == 0:
                    args = None
                elif len(args) == 1:
                    args = args[0]
                loop.call_soon_threadsafe(fut.set_result, args)

        self._callback = cb

        if timeout is None:
            return await fut  # Simply wait on the future

        # Timeout given, wait for the specified period for the
        try:
            val = await asyncio.wait_for(fut, timeout)
            return val
        except asyncio.TimeoutError:
            fut.cancel()
        return self._handle_timeout(exception_on_timeout)

    def then(self, callback: Callable[[T], None]):
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


class GenericWaitable(Waitable[T]):
    """
    Simple wrapper of a Waitable object which exposes a ``notify``
    method so external objects can signal/trigger the waitable's response
    """
    def notify(self, *results):
        self._notify(*results)


class EmptyWaitable(Waitable[T]):
    """
    Waitable class which will immediately return the args provided when waited on
    or when a callback function is registered
    """
    def __init__(self, *args):
        super().__init__(len(args))
        self._args = args

    def wait(self, timeout: float = None, exception_on_timeout=True) -> T:
        return self._args

    def then(self, callback: Callable[[T], None]):
        if callback and callable(callback):
            callback(*self._args)
        return self
