from typing import Generic, Tuple, Callable
from blatann.waitables.waitable import Waitable
from blatann.event_type import Event, TSender, TEvent


class EventWaitable(Waitable, Generic[TSender, TEvent]):
    """
    Waitable implementation which waits on an :class:`~blatann.event_type.Event`.
    """
    def __init__(self, event: Event[TSender, TEvent]):
        super(EventWaitable, self).__init__(n_args=2)
        self._event = event
        self._event.register(self._on_event)

    def _on_event(self, *args):
        self._event.deregister(self._on_event)
        self._notify(*args)

    def _on_timeout(self):
        self._event.deregister(self._on_event)

    def wait(self, timeout=None, exception_on_timeout=True) -> Tuple[TSender, TEvent]:
        res = super(EventWaitable, self).wait(timeout, exception_on_timeout)
        if res is None:  # Timeout, send None, None for the sender and event_args
            return None, None
        return res

    def then(self, callback: Callable[[TSender, TEvent], None]):
        return super(EventWaitable, self).then(callback)


class IdBasedEventWaitable(EventWaitable, Generic[TSender, TEvent]):
    """
    Extension of :class:`EventWaitable` for high-churn events which require IDs to ensure the correct operation is waited upon,
    such as characteristic read, write and notify operations
    """
    def __init__(self, event, event_id):
        self.id = event_id
        super(IdBasedEventWaitable, self).__init__(event)

    def _on_event(self, sender, event_args):
        if event_args.id == self.id:
            super(IdBasedEventWaitable, self)._on_event(sender, event_args)
