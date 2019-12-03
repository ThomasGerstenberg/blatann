from __future__ import annotations
import logging
from blatann.gap.advertise_data import ScanReport, ScanReportCollection
from blatann.nrf import nrf_events, nrf_types
from blatann.waitables import scan_waitable
from blatann.event_type import Event, EventSource

logger = logging.getLogger(__name__)


class ScanParameters(nrf_types.BLEGapScanParams):
    pass


class Scanner(object):
    def __init__(self, ble_device):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.ble_device = ble_device
        self._default_scan_params = ScanParameters(200, 150, 10)
        self.scanning = False
        ble_device.ble_driver.event_subscribe(self._on_adv_report, nrf_events.GapEvtAdvReport)
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self.scan_report = ScanReportCollection()
        self._on_scan_received: EventSource[Scanner, ScanReport] = EventSource("On Scan Received", logger)
        self._on_scan_timeout: EventSource[Scanner, ScanReportCollection] = EventSource("On Scan Timeout")

    @property
    def on_scan_received(self) -> Event[Scanner, ScanReport]:
        """
        Event that is triggered whenever a scan report is received

        :return: An event which emits the Scanner and a ScanReport
        """
        return self._on_scan_received

    @property
    def on_scan_timeout(self) -> Event[Scanner, ScanReportCollection]:
        """
        Event that is triggered when scanning completes/times out
        """
        return self._on_scan_timeout

    def set_default_scan_params(self, interval_ms=200, window_ms=150, timeout_seconds=10):
        """
        Sets the default scan parameters so they do not have to be specified each time a scan is started.
        Reference the Bluetooth specification for valid ranges for parameters.

        :param interval_ms: The interval which to scan for advertising packets, in milliseconds
        :param window_ms: How long within a single scan interval to be actively listening for advertising packets,
                          in milliseconds
        :param timeout_seconds: How long to advertise for, in seconds
        """
        self._default_scan_params.interval_ms = interval_ms
        self._default_scan_params.window_ms = window_ms
        self._default_scan_params.timeout_s = timeout_seconds

    def start_scan(self, scan_parameters=None, clear_scan_reports=True):
        """
        Starts a scan and returns a waitable for when the scan completes

        :param scan_parameters: Optional scan parameters. Uses default if not specified
        :type scan_parameters: ScanParameters
        :param clear_scan_reports: Flag to clear out previous scan reports
        :return: A Waitable which will expire once the scan finishes based on the timeout specified.
                 Waitable returns a ScanReportCollection of the advertising packets found
        :rtype: scan_waitable.ScanFinishedWaitable
        """
        self.stop()
        if clear_scan_reports:
            self.scan_report = ScanReportCollection()
        if not scan_parameters:
            scan_parameters = self._default_scan_params
        self.ble_device.ble_driver.ble_gap_scan_start(scan_parameters)
        self.scanning = True
        return scan_waitable.ScanFinishedWaitable(self.ble_device)

    def stop(self):
        """
        Stops an active scan
        """
        if not self.scanning:
            return
        self.scanning = False

        try:
            self.ble_device.ble_driver.ble_gap_scan_stop()
        except:
            pass

    def _on_adv_report(self, driver, adv_report):
        scan_report = self.scan_report.update(adv_report)
        self._on_scan_received.notify(self.ble_device, scan_report)

    def _on_timeout_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.scan:
            self.scanning = False
            self._on_scan_timeout.notify(self.ble_device, self.scan_report)
