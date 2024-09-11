from __future__ import annotations

import asyncio
import queue
from typing import Generic, Optional, Tuple, Union

from blatann.event_type import Event, TEvent, TSender

_disconnect_sentinel = object()


class EventQueue(Generic[TSender, TEvent]):
    """
    Iterable object which provides a stream of events dispatched on a provided ``Event`` object.
    The iterator does not exit unless a "disconnect event" is provided, typically when a peer disconnects.
    """
    def __init__(
            self,
            event: Event[TSender, TEvent],
            disconnect_event: Event = None
    ):
        self._event = event
        self._queue = queue.Queue[Union[Tuple[TSender, TEvent], None]]()
        self._event.register(self._on_event, weak=True)
        self._disconnect_event = disconnect_event
        if disconnect_event:
            disconnect_event.register(self._on_disconnect, weak=True)

    def __iter__(self):
        """Create the iterator object"""
        return self

    def __next__(self) -> Tuple[TSender, TEvent]:
        """Block until the next event is received"""
        item = self.get()
        if item is None:
            raise StopIteration
        return item

    def get(self, block=True, timeout=None) -> Optional[Tuple[TSender, TEvent]]:
        """
        Gets the next item in the queue.
        If a disconnect event occurs, the queue will return ``None`` and not return any other events afterward.

        :param block: True to block the current thread until the next event is received
        :param timeout: Optional timeout to wait for the next object
        :return: The next item in the queue
        :raises: queue.Empty if a timeout is provided and no event was received
        """
        item = self._queue.get(block, timeout)
        if item is _disconnect_sentinel:
            self._event.deregister(self._on_event)
            if self._disconnect_event:
                self._disconnect_event.deregister(self._on_disconnect)
            item = None
        return item

    def _get_next(self, block=True, timeout=None):
        item = self._queue.get(block, timeout)
        if item is _disconnect_sentinel:
            # Disconnection occurred, clear the handlers from the events
            self._event.deregister(self._on_event)
            if self._disconnect_event:
                self._disconnect_event.deregister(self._on_disconnect)
            item = None
        return item

    def _on_event(self, sender: TSender, event: TEvent):
        self._queue.put((sender, event))

    def _on_disconnect(self, sender, event):
        self._queue.put(_disconnect_sentinel)


class AsyncEventQueue(Generic[TSender, TEvent]):
    """
    Asynchronous iterable object which provides a stream of events dispatched on a provided ``Event`` object.
    The iterator does not exit unless a "disconnect event" is provided, typically when a peer disconnects.
    """
    def __init__(
            self,
            event: Event[TSender, TEvent],
            disconnect_event: Event = None,
            event_loop: asyncio.AbstractEventLoop = None
    ):
        self._event = event
        self._queue = asyncio.Queue()
        self._event_loop = event_loop or asyncio.get_event_loop()
        self._event.register(self._on_event, weak=True)
        self._disconnect_event = disconnect_event
        if disconnect_event:
            disconnect_event.register(self._on_disconnect, weak=True)

    def __aiter__(self):
        """Create the async iterator object"""
        return self

    async def __anext__(self) -> Tuple[TSender, TEvent]:
        """Asynchronously block until the next event arrives. Return the sender and event objects"""
        item = await self.get()
        if item is None:
            raise StopAsyncIteration
        return item

    async def get(self) -> Optional[Tuple[TSender, TEvent]]:
        """
        Asynchronously gets the next item in the queue.
        If a disconnect event occurs, the queue will return ``None`` and not provide any other events afterward.

        :return: The next item in the queue, or None if the disconnect event occurred
        """
        item = await self._queue.get()
        if item is _disconnect_sentinel:
            # Disconnection occurred, clear the handlers from the events
            self._event.deregister(self._on_event)
            if self._disconnect_event:
                self._disconnect_event.deregister(self._on_disconnect)
            item = None
        return item

    def _on_event(self, sender: TSender, event: TEvent):
        asyncio.run_coroutine_threadsafe(self._queue.put((sender, event)), self._event_loop)

    def _on_disconnect(self, sender, event):
        asyncio.run_coroutine_threadsafe(self._queue.put(_disconnect_sentinel), self._event_loop)
