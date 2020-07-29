import threading
import queue
import logging


logger = logging.getLogger(__name__)


class QueuedTasksManagerBase(object):
    """
    Handles queuing of tasks that can only be done one at a time
    """
    class TaskFailure:
        def __init__(self, reason=None, ignore_stack_trace=False, clear_all=False):
            self.ignore_stack_trace = ignore_stack_trace
            self.clear_all = clear_all
            self.reason = reason

    def __init__(self):
        self._queue = queue.Queue()
        self._in_process = threading.Event()
        self._lock = threading.RLock()

    def _add_task(self, task):
        with self._lock:
            if self._in_process.is_set():
                self._queue.put(task)
            else:
                try:
                    task_complete = self._handle_task(task)
                    if not task_complete:
                        self._in_process.set()
                except Exception as e:
                    self._process_exception(task, e)

    def _task_completed(self, task):
        with self._lock:
            task = self._get_next()
            while task:
                try:
                    task_complete = self._handle_task(task)
                    if not task_complete:
                        break
                except Exception as e:
                    self._process_exception(task, e)
                task = self._get_next()

            if not task:
                self._in_process.clear()

    def _process_exception(self, task, e):
        action = self._handle_task_failure(task, e)
        if not action.ignore_stack_trace:
            logger.exception(e)
        if action.clear_all:
            self._clear_all(action.reason)

    def _get_next(self):
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _clear_all(self, reason):
        with self._lock:
            task = self._get_next()
            while task:
                self._handle_task_cleared(task, reason)
                task = self._get_next()
            self._in_process.clear()

    def clear_all(self):
        raise NotImplementedError()

    def _handle_task(self, task):
        raise NotImplementedError()

    def _handle_task_failure(self, task, e) -> TaskFailure:
        raise NotImplementedError()

    def _handle_task_cleared(self, task, reason):
        raise NotImplementedError()

