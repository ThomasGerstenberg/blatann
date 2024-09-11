from __future__ import annotations

import asyncio
from typing import Callable, Generic, Tuple

from blatann.event_type import Event, TEvent, TSender
from blatann.waitables.waitable import Waitable


class EventWaitable(Waitable[Tuple[TSender, TEvent]]):
    """
    Waitable implementation which waits on an :class:`~blatann.event_type.Event`.
    """
    def __init__(self, event: Event[TSender, TEvent]):
        super().__init__(n_args=2)
        self._event = event
        self._event.register(self._on_event)

    def _on_event(self, *args):
        self._event.deregister(self._on_event)
        self._notify(*args)

    def _on_timeout(self):
        self._event.deregister(self._on_event)

    def wait(self, timeout=None, exception_on_timeout=True) -> Tuple[TSender, TEvent]:
        res = super().wait(timeout, exception_on_timeout)
        if res is None:  # Timeout, send None, None for the sender and event_args
            return None, None
        return res

    async def as_async(
            self, timeout: float = None,
            exception_on_timeout=True,
            loop: asyncio.AbstractEventLoop = None
    ) -> Tuple[TSender, TEvent]:

        res = await super().as_async(timeout, exception_on_timeout, loop)
        if res is None:  # Timeout, send None, None for the sender and event_args
            return None, None
        return res

    def then(self, callback: Callable[[TSender, TEvent], None]):
        return super().then(callback)


class IdBasedEventWaitable(EventWaitable):
    """
    Extension of :class:`EventWaitable` for high-churn events which require IDs to ensure the correct operation is waited upon,
    such as characteristic read, write and notify operations
    """
    def __init__(self, event, event_id):
        self.id = event_id
        super().__init__(event)

    def _on_event(self, sender, event_args):
        if event_args.id == self.id:
            super()._on_event(sender, event_args)
