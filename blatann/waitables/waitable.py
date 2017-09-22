

class Waitable(object):
    def wait(self, timeout=None, exception_on_timeout=True):
        raise NotImplementedError

    def then(self, func_to_execute):
        raise NotImplementedError
