from blatann.waitables.waitable import Waitable


class EventWaitable(Waitable):
    def __init__(self, event):
        """
        :type event: blatann.event_type.Event
        """
        super(EventWaitable, self).__init__()
        self._event = event
        self._event.register(self._on_event)

    def _on_event(self, *args):
        self._event.deregister(self._on_event)
        self._notify(args)

    def _on_timeout(self):
        self._event.deregister(self._on_event)
