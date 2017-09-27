from threading import Lock


class Event(object):
    """
    Represents an event that can have handlers registered and deregistered
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

    def notify(self, *args, **kwargs):
        """
        Notifies all clients with the given arguments and keyword-arguments
        """
        with self._handler_lock:
            handlers = self._handlers[:]

        for h in handlers:
            try:
                h(*args, **kwargs)
            except Exception as e:
                if self._logger:
                    self._logger.exception(e)
