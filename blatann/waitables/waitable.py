import queue
from blatann.exceptions import TimeoutError


class Waitable(object):
    def __init__(self):
        self._queue = queue.Queue()
        self._callback = None

    def wait(self, timeout=None, exception_on_timeout=True):
        try:
            results = self._queue.get(timeout=timeout)
            if len(results) == 1:
                return results[0]
            return results
        except queue.Empty:
            self._on_timeout()
            if exception_on_timeout:
                raise TimeoutError("Timed out waiting for event to occur. "
                                   "Waitable type: {}".format(self.__class__.__name__))
        # TODO: This will fail if the waitable implementation normally returns more than one value and
        #       the caller tries to unpack
        return None

    def then(self, func_to_execute):
        self._callback = func_to_execute
        return self

    def _on_timeout(self):
        pass

    def _notify(self, *results):
        self._queue.put(results)
        if self._callback:
            self._callback(*results)


class GenericWaitable(Waitable):
    def notify(self, *results):
        self._notify(*results)
