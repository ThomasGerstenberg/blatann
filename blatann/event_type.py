from __future__ import annotations

import types
import weakref
from threading import Lock
from typing import Callable, Generic, TypeVar

TSender = TypeVar("TSender")
TEvent = TypeVar("TEvent")


class Event(Generic[TSender, TEvent]):
    """
    Represents an event that can have handlers registered and deregistered.
    All handlers registered to an event should take in two parameters: the event sender and the event arguments.

    Those familiar with the C#/.NET event architecture, this should look very similar, though registration is done using the ``register()``
    method instead of ``+= event_handler``
    """
    def __init__(self, name):
        self.name = name
        self._handler_lock = Lock()
        self._handlers = []
        self._handlers_set = weakref.WeakSet()

    def register(self, handler: Callable[[TSender, TEvent], None], weak=False) -> EventSubscriptionContext[TSender, TEvent]:
        """
        Registers a handler to be called whenever the event is emitted.
        If the given handler is already registered, function does not register the handler a second time.

        This function can be used in a `with` context block which will automatically deregister the handler
        when the context is exited.

        :Example:

        >>> with device.client.on_connected.register(my_connected_handler):
        >>>    # Do something, my_connected_handler will be deregistered upon leaving this context

        :param handler: The handler to register
        :param weak: True to register the handler as a weakref

        :return: a context block that can be used to automatically unsubscribe the handler
        """
        if weak:
            if isinstance(handler, types.MethodType):
                entry = weakref.WeakMethod(handler)
            else:
                entry = weakref.ref(handler)
        else:
            entry = handler
        with self._handler_lock:
            if handler not in self._handlers_set:
                self._handlers.append(entry)
                self._handlers_set.add(handler)
        return EventSubscriptionContext(self, handler)

    def deregister(self, handler: Callable[[TSender, TEvent], None]):
        """
        Deregisters a previously-registered handler so it no longer receives the event.
        If the given handler is not registered, function does nothing

        :param handler: The handler to deregister
        """
        with self._handler_lock:
            if handler in self._handlers_set:
                self._handlers_set.remove(handler)
                # In the case of weakrefs, the caller must have a strong reference to the handler
                # in order to pass it into this function. Thus, it must exist in both the handler set and handler list
                if handler in self._handlers:
                    self._handlers.remove(handler)
                else:
                    # weakref, need to iterate to find the handler
                    item_to_remove = None
                    for entry in self._handlers:
                        if isinstance(entry, weakref.ref):
                            item = entry()
                            if item == handler:
                                item_to_remove = entry
                                break
                    if item_to_remove:
                        self._handlers.remove(item_to_remove)


class EventSource(Event):
    """
    Represents an Event object along with the controls to emit the events and notify handlers.
    This is done to "hide" the notify method from subscribers.
    """
    def __init__(self, name, logger=None):
        super(EventSource, self).__init__(name)
        self._logger = logger

    @property
    def has_handlers(self) -> bool:
        """
        Gets if the event has any handlers subscribed to the event
        """
        with self._handler_lock:
            return bool(self._handlers_set)

    def clear_handlers(self):
        """
        Clears all handlers from the event
        """
        with self._handler_lock:
            self._handlers = []
            self._handlers_set = weakref.WeakSet()

    def notify(self, sender: TSender, event_args: TEvent = None):
        """
        Notifies all subscribers with the given sender and event arguments
        """
        with self._handler_lock:
            handlers = self._handlers[:]

        dead_weakrefs = []
        for h in handlers:
            if isinstance(h, weakref.ref):
                h_ref = h
                h = h_ref()  # noqa: PLW2901  allow reassignment to iterated 'h'
                if h is None:
                    dead_weakrefs.append(h_ref)
                    continue

            try:
                h(sender, event_args)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error occurred while handling event '{self.name}'. Sender: {sender}, Event Args: {event_args}")
                    self._logger.exception(e)

        if dead_weakrefs:
            self._prune_dead_weakrefs(dead_weakrefs)

    def _prune_dead_weakrefs(self, dead_weakrefs):
        with self._handler_lock:
            for dead_weakref in dead_weakrefs:
                # Double-check now that we're locked that the weakref still is in the handler list
                if dead_weakref in self._handlers:
                    self._handlers.remove(dead_weakref)


class EventSubscriptionContext(Generic[TSender, TEvent]):
    def __init__(self, event: Event[TSender, TEvent], subscriber: Callable[[TSender, TEvent], None]):
        self._event = event
        self._subscriber = subscriber

    def __enter__(self):
        self._event.register(self._subscriber)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._event.deregister(self._subscriber)
