from __future__ import annotations

import asyncio
import queue
import threading
from typing import Iterable

from blatann.gap.advertise_data import ScanReport, ScanReportCollection
from blatann.nrf import nrf_events, nrf_types
from blatann.waitables.waitable import Waitable


class ScanFinishedWaitable(Waitable):
    """
    Waitable that triggers when a scan operation completes. It also provides a mechanism to acquire the received scan reports
    in real-time
    """
    def __init__(self, ble_device):
        super().__init__()
        self.scanner = ble_device.scanner
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self.scanner.on_scan_received.register(self._on_scan_report)
        self.ble_driver = ble_device.ble_driver
        self._scan_report_queue = queue.Queue()
        self._event_loop: asyncio.AbstractEventLoop = None
        self._lock = threading.Lock()

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

    @property
    async def scan_reports_async(self) -> Iterable[ScanReport]:
        """
        Async iterable which yields the scan reports in real-time as they're received.
        The iterable will block until scanning has timed out/finished.

        .. warning::
            This method is experimental!
        """
        # Copy any reports received before calling this to the asyncio queue
        with self._lock:
            existing_queue = self._scan_report_queue
            self._scan_report_queue = asyncio.Queue()
            self._event_loop = asyncio.get_event_loop()
            while True:
                try:
                    item = existing_queue.get_nowait()
                    self._scan_report_queue.put_nowait(item)
                except queue.Empty:
                    break

        scan_report = await self._scan_report_queue.get()
        while scan_report:
            yield scan_report
            scan_report = await self._scan_report_queue.get()

    def _event_occurred(self, ble_driver):
        ble_driver.event_unsubscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self.scanner.on_scan_received.deregister(self._on_scan_report)
        self._notify(self.scanner.scan_report)

    def _on_timeout(self):
        self.ble_driver.event_unsubscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self.scanner.on_scan_received.deregister(self._on_scan_report)

    def _add_item(self, scan_report):
        with self._lock:
            q = self._scan_report_queue
            if self._event_loop:
                asyncio.run_coroutine_threadsafe(q.put(scan_report), self._event_loop)
            else:
                q.put(scan_report)

    def _on_scan_report(self, device, scan_report):
        self._add_item(scan_report)

    def _on_timeout_event(self, ble_driver, event: nrf_events.GapEvtTimeout):
        if event.src == nrf_types.BLEGapTimeoutSrc.scan:
            self._event_occurred(ble_driver)
            self._add_item(None)

    def wait(self, timeout: float = None, exception_on_timeout: bool = True) -> ScanReportCollection:
        """
        Waits for the scanning operation to complete then returns the scan report collection

        :param timeout: How long to wait for, in seconds
        :param exception_on_timeout: Flag if to throw an exception if the operation timed out.
               If false and a timeout occurs, will return None
        :return: The scan report collection
        """
        return super().wait(timeout, exception_on_timeout)
