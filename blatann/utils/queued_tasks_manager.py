import threading
import queue
import logging


logger = logging.getLogger(__name__)


class QueuedTasksManagerBase(object):
    """
    Handles queuing of tasks that can only be done one at a time
    """
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
                    self._handle_task_failure(task, e)

    def _task_completed(self, task):
        with self._lock:
            task = self._get_next()
            while task:
                try:
                    task_complete = self._handle_task(task)
                    if not task_complete:
                        break
                except Exception as e:
                    logger.exception(e)
                    self._handle_task_failure(task, e)

            if not task:
                self._in_process.clear()

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

    def _handle_task_failure(self, task, e):
        raise NotImplementedError()

    def _handle_task_cleared(self, task, reason):
        raise NotImplementedError()

