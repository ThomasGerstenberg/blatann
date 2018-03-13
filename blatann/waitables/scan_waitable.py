from blatann.waitables.waitable import Waitable
from blatann.nrf.nrf_events import GapEvtTimeout, BLEGapTimeoutSrc, GapEvtAdvReport


class ScanFinishedWaitable(Waitable):
    def __init__(self, ble_device):
        super(ScanFinishedWaitable, self).__init__()
        self.scanner = ble_device.scanner
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, GapEvtTimeout)
        self.ble_driver = ble_device.ble_driver

    def _event_occurred(self, ble_driver):
        ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)
        self._notify(self.scanner.scan_report)

    def _on_timeout(self):
        self.ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)

    def _on_timeout_event(self, ble_driver, event):
        """
        :type event: GapEvtTimeout
        """
        if event.src == BLEGapTimeoutSrc.scan:
            self._event_occurred(ble_driver)

    def wait(self, timeout=None, exception_on_timeout=True):
        """
        :rtype: blatann.gap.scanning.ScanReportCollection
        """
        return super(ScanFinishedWaitable, self).wait(timeout, exception_on_timeout)
