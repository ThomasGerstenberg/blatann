import queue
from blatann.waitables.waitable import Waitable
from blatann.nrf.nrf_events import GapEvtTimeout, BLEGapTimeoutSrc, GapEvtAdvReport


class ScanFinishedWaitable(Waitable):
    def __init__(self, ble_device):
        self._callback = None
        self._queue = queue.Queue()
        self.scanner = ble_device.scanner
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, GapEvtTimeout)

    def _event_occurred(self, ble_driver):
        ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)
        self._queue.put(self.scanner.scan_report)
        if self._callback:
            self._callback(self.scanner.scan_report)

    def _on_timeout_event(self, ble_driver, event):
        """
        :type event: GapEvtTimeout
        """
        if event.src == BLEGapTimeoutSrc.scan:
            self._event_occurred(ble_driver)

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
