import threading


def _or(self, other):
    if isinstance(self, _OrEvent):
        events = self.events[:]
    elif isinstance(self, threading.Event):
        events = [self]
    else:
        raise ValueError("Incompatible Event type to OR with")

    if isinstance(other, _OrEvent):
        events.extend(other.events)
    elif isinstance(other, threading.Event):
        events.append(other)
    else:
        raise ValueError("Incompatible Event type to OR with")

    return _OrEvent(*events)


def _or_set(self):
    self._set()
    for h in self._changed:
        h()


def _or_clear(self):
    self._clear()
    for h in self._changed:
        h()


class _OrEvent(threading.Event):
    def __init__(self, *events):
        super(_OrEvent, self).__init__()
        self.events = []
        for e in events:
            self.add(e)

    def _changed(self):
        bools = [e.is_set() for e in self.events]
        if any(bools):
            self.set()
        else:
            self.clear()

    def _orify(self, e):
        if not hasattr(e, "_set"):
            e._set = e.set
            e._clear = e.clear
            e._changed = []
            e.set = lambda: _or_set(e)
            e.clear = lambda: _or_clear(e)
        e._changed.append(self._changed)

    def add(self, event):
        if isinstance(event, _OrEvent):
            for e in event.events:
                self._orify(e)
            self.events.extend(event.events)
        else:
            self._orify(event)
            self.events.append(event)

    def __or__(self, other):
        return _or(self, other)


threading.Event.__or__ = _or
