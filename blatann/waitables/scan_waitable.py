from queue import Queue
from typing import Iterable
from blatann.waitables.waitable import Waitable
from blatann.nrf.nrf_events import GapEvtTimeout, BLEGapTimeoutSrc, GapEvtAdvReport
from blatann.gap.advertise_data import ScanReport, ScanReportCollection


class ScanFinishedWaitable(Waitable):
    """
    Waitable that triggers when a scan operation completes. It also provides a mechanism to acquire the received scan reports
    in real-time
    """
    def __init__(self, ble_device):
        super(ScanFinishedWaitable, self).__init__()
        self.scanner = ble_device.scanner
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, GapEvtTimeout)
        self.scanner.on_scan_received.register(self._on_scan_report)
        self.ble_driver = ble_device.ble_driver
        self._scan_report_queue = Queue()

    @property
    def scan_reports(self) -> Iterable[ScanReport]:
        """
        Iterable which yields the scan reports in real-time as they're received.
        The iterable will block until scanning has timed out/finished
        """
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

    def wait(self, timeout: float = None, exception_on_timeout: bool = True) -> ScanReportCollection:
        """
        Waits for the scanning operation to complete then returns the scan report collection

        :param timeout: How long to wait for, in seconds
        :param exception_on_timeout: Flag whether or not to throw an exception if the operation timed out.
               If false and a timeout occurs, will return None
        :return: The scan report collection
        """
        return super(ScanFinishedWaitable, self).wait(timeout, exception_on_timeout)
