from queue import Queue
from typing import Iterable
from blatann.waitables.waitable import Waitable
from blatann.nrf.nrf_events import GapEvtTimeout, BLEGapTimeoutSrc, GapEvtAdvReport
from blatann.gap.advertise_data import ScanReport, ScanReportCollection


class ScanFinishedWaitable(Waitable):
    def __init__(self, ble_device):
        super(ScanFinishedWaitable, self).__init__()
        self.scanner = ble_device.scanner
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, GapEvtTimeout)
        self.scanner.on_scan_received.register(self._on_scan_report)
        self.ble_driver = ble_device.ble_driver
        self._scan_report_queue = Queue()

    @property
    def scan_reports(self) -> Iterable[ScanReport]:
        scan_report = self._scan_report_queue.get()
        while scan_report:
            yield scan_report
            scan_report = self._scan_report_queue.get()

    def _event_occurred(self, ble_driver):
        ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)
        self.scanner.on_scan_received.deregister(self._on_scan_report)
        self._notify(self.scanner.scan_report)

    def _on_timeout(self):
        self.ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)
        self.scanner.on_scan_received.deregister(self._on_scan_report)

    def _on_scan_report(self, device, scan_report):
        self._scan_report_queue.put(scan_report)

    def _on_timeout_event(self, ble_driver, event):
        """
        :type event: GapEvtTimeout
        """
        if event.src == BLEGapTimeoutSrc.scan:
            self._event_occurred(ble_driver)
            self._scan_report_queue.put(None)

    def wait(self, timeout=None, exception_on_timeout=True) -> ScanReportCollection:
        return super(ScanFinishedWaitable, self).wait(timeout, exception_on_timeout)
