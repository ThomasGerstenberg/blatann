from threading import Lock


class Event(object):
    """
    Represents an event that can have handlers registered and deregistered.
    All handlers registered to an event should take in two parameters: the event sender and the event arguments.
    Those familiar with the C#/.NET event architecture, this should look very similar.
    """
    def __init__(self, name):
        self.name = name
        self._handler_lock = Lock()
        self._handlers = []

    def register(self, handler):
        """
        Registers a handler to be called whenever the event is emitted.
        If the given handler is already registered, function does nothing

        :param handler: The handler to register
        """
        with self._handler_lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def deregister(self, handler):
        """
        Deregisters a previously-registered handler so it no longer receives the event.
        If the given handler is not registered, function does nothing

        :param handler: The handler to deregister
        """
        with self._handler_lock:
            if handler in self._handlers:
                self._handlers.remove(handler)


class EventSource(Event):
    """
    Represents an Event object along with the controls to emit the events and notify handlers.
    This is done to "hide" the notify method from subscribers.
    """
    def __init__(self, name, logger=None):
        super(EventSource, self).__init__(name)
        self._logger = logger

    def clear_handlers(self):
        with self._handler_lock:
            self._handlers = []

    def notify(self, sender, event_args=None):
        """
        Notifies all clients with the given arguments and keyword-arguments
        """
        with self._handler_lock:
            handlers = self._handlers[:]

        for h in handlers:
            try:
                h(sender, event_args)
            except Exception as e:
                if self._logger:
                    self._logger.exception(e)
