import threading
from typing import Generic, Optional, TypeVar
import queue
import logging


logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueuedTasksManagerBase(Generic[T]):
    """
    Handles queuing of tasks that can only be done one at a time
    """
    class TaskFailure:
        def __init__(self, reason=None, ignore_stack_trace=False, clear_all=False):
            self.ignore_stack_trace = ignore_stack_trace
            self.clear_all = clear_all
            self.reason = reason

    def __init__(self, max_processing_items_at_once=1):
        self._input_queue = queue.Queue()
        self._lock = threading.RLock()
        self._in_process_queue = queue.Queue(max_processing_items_at_once)

    def _add_task(self, task: T):
        with self._lock:
            # Cannot process any more tasks currently, add to input queue
            if self._in_process_queue.full():
                self._input_queue.put(task)
            else:
                try:
                    # Handle the task. If it's not complete put it in the in process queue
                    task_complete = self._handle_task(task)
                    if not task_complete:
                        self._in_process_queue.put_nowait(task)
                except Exception as e:
                    self._process_exception(task, e)

    def _pop_task_in_process(self) -> Optional[T]:
        # Pops the earliest task from the process queue, will be completed shortly
        with self._lock:
            return self._get_next(self._in_process_queue)

    def _task_completed(self, task: T):
        with self._lock:
            # Ensure the queue wasn't filled by another thread
            if self._in_process_queue.full():
                return
            # Start processing tasks from the input queue
            task = self._get_next(self._input_queue)
            while task:
                try:
                    task_complete = self._handle_task(task)
                    if not task_complete:
                        # Task is still in process, add to the queue and if full break out of the loop
                        self._in_process_queue.put_nowait(task)
                        if self._in_process_queue.full():
                            break
                except Exception as e:
                    self._process_exception(task, e)
                task = self._get_next(self._input_queue)

    def _process_exception(self, task: T, e: Exception):
        action = self._handle_task_failure(task, e)
        if not action.ignore_stack_trace:
            logger.exception(e)
        if action.clear_all:
            self._clear_all(action.reason)

    def _get_next(self, q: queue.Queue) -> Optional[T]:
        if not q:
            q = self._input_queue
        try:
            return q.get_nowait()
        except queue.Empty:
            return None

    def _clear_all(self, reason):
        with self._lock:
            # Clear the process queue, then clear the input queue
            task = self._get_next(self._in_process_queue)
            while task:
                self._handle_task_cleared(task, reason)
                task = self._get_next(self._in_process_queue)

            # Clear the input queue
            task = self._get_next(self._input_queue)
            while task:
                self._handle_task_cleared(task, reason)
                task = self._get_next(self._input_queue)

    def clear_all(self):
        raise NotImplementedError()

    def _handle_task(self, task: T):
        raise NotImplementedError()

    def _handle_task_failure(self, task: T, e: Exception) -> TaskFailure:
        raise NotImplementedError()

    def _handle_task_cleared(self, task: T, reason):
        raise NotImplementedError()
