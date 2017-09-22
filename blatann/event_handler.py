from threading import Lock


class Event(object):
    def __init__(self, name):
        self.name = name
        self._handler_lock = Lock()
        self._handlers = []

    def register(self, handler):
        with self._handler_lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def deregister(self, handler):
        with self._handler_lock:
            if handler in self._handlers:
                self._handlers.remove(handler)


class EventSource(Event):
    def __init__(self, name, logger=None):
        super(EventSource, self).__init__(name)
        self._logger = logger

    def notify(self, *args, **kwargs):
        with self._handler_lock:
            handlers = self._handlers[:]

        for h in handlers:
            try:
                h(*args, **kwargs)
            except Exception as e:
                if self._logger:
                    self._logger.exception(e)