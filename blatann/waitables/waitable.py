import queue
from blatann.exceptions import TimeoutError


class Waitable(object):
    def __init__(self, n_args=1):
        self._queue = queue.Queue()
        self._callback = None
        self._n_args = n_args
        if n_args < 1:
            raise ValueError()

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
        if self._n_args == 1:
            return None
        return [None] * self._n_args

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


class EmptyWaitable(Waitable):
    """
    Waitable class which will immediately return the args provided when waited on
    or when a callback function is registered
    """
    def __init__(self, *args):
        super(EmptyWaitable, self).__init__(len(args))
        self._args = args

    def wait(self, timeout=None, exception_on_timeout=True):
        return self._args

    def then(self, func_to_execute):
        func_to_execute(*self._args)
        return self
