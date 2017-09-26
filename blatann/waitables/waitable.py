import queue


class Waitable(object):
    def __init__(self):
        self._queue = queue.Queue()
        self._callback = None

    def wait(self, timeout=None, exception_on_timeout=True):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            if exception_on_timeout:
                raise
        return None

    def then(self, func_to_execute):
        self._callback = func_to_execute
        return self

    def _notify(self, result):
        self._queue.put(result)
        if self._callback:
            self._callback(result)


