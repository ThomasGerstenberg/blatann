from __future__ import annotations
import logging
from blatann.gap.advertise_data import ScanReport, ScanReportCollection
from blatann.nrf import nrf_events, nrf_types
from blatann.waitables import scan_waitable
from blatann.event_type import Event, EventSource

logger = logging.getLogger(__name__)


MIN_SCAN_INTERVAL_MS = nrf_types.scan_interval_range.min
MAX_SCAN_INTERVAL_MS = nrf_types.scan_interval_range.max
MIN_SCAN_WINDOW_MS = nrf_types.scan_window_range.min
MAX_SCAN_WINDOW_MS = nrf_types.scan_window_range.max
MIN_SCAN_TIMEOUT_S = nrf_types.scan_timeout_range.min
MAX_SCAN_TIMEOUT_S = nrf_types.scan_timeout_range.max


class ScanParameters(nrf_types.BLEGapScanParams):
    """
    Class which holds scanning parameters
    """
    def validate(self):
        self._validate(self.window_ms, self.interval_ms, self.timeout_s)

    def update(self, window_ms, interval_ms, timeout_s, active):
        self._validate(window_ms, interval_ms, timeout_s)
        self.window_ms = window_ms
        self.interval_ms = interval_ms
        self.timeout_s = timeout_s
        self.active = active

    def _validate(self, window_ms, interval_ms, timeout_s):
        # Check against absolute limits
        nrf_types.scan_window_range.validate(window_ms)
        nrf_types.scan_interval_range.validate(interval_ms)
        if timeout_s:
            nrf_types.scan_timeout_range.validate(timeout_s)
        # Verify that the window is not larger than the interval
        if window_ms > interval_ms:
            raise ValueError(f"Window cannot be greater than the interval (window: {window_ms}, interval: {interval_ms}")

    def __repr__(self):
        return f"ScanParameters(window: {self.window_ms}ms, interval: {self.interval_ms}ms, " \
               f"timeout: {self.timeout_s}s, active: {self.active})"


class Scanner(object):
    def __init__(self, ble_device):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.ble_device = ble_device
        self._default_scan_params = ScanParameters(200, 150, 10)
        self._is_scanning = False
        ble_device.ble_driver.event_subscribe(self._on_adv_report, nrf_events.GapEvtAdvReport)
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self.scan_report = ScanReportCollection()
        self._on_scan_received: EventSource[Scanner, ScanReport] = EventSource("On Scan Received", logger)
        self._on_scan_timeout: EventSource[Scanner, ScanReportCollection] = EventSource("On Scan Timeout")
        self._own_address = None

    @property
    def on_scan_received(self) -> Event[Scanner, ScanReport]:
        """
        Event that is raised whenever a scan report is received
        """
        return self._on_scan_received

    @property
    def on_scan_timeout(self) -> Event[Scanner, ScanReportCollection]:
        """
        Event that is raised when scanning completes/times out
        """
        return self._on_scan_timeout

    @property
    def is_scanning(self) -> bool:
        """
        **Read Only**

        Current state of scanning
        """
        return self._is_scanning

    def set_default_scan_params(self,
                                interval_ms: float = 200,
                                window_ms: float = 150,
                                timeout_seconds: int = 10,
                                active_scanning: bool = True):
        """
        Sets the default scan parameters so they do not have to be specified each time a scan is started.
        Reference the Bluetooth specification for valid ranges for parameters.

        :param interval_ms: The interval which to scan for advertising packets, in milliseconds
        :param window_ms: How long within a single scan interval to be actively listening for advertising packets,
                          in milliseconds
        :param timeout_seconds: How long to advertise for, in seconds
        :param active_scanning: Whether or not to fetch scan response packets from advertisers
        """
        self._default_scan_params.update(window_ms, interval_ms, timeout_seconds, active_scanning)

    def start_scan(self, scan_parameters: ScanParameters = None, clear_scan_reports=True) -> scan_waitable.ScanFinishedWaitable:
        """
        Starts a scan and returns a waitable for when the scan completes

        :param scan_parameters: Optional scan parameters. Uses default if not specified
        :param clear_scan_reports: Flag to clear out previous scan reports
        :return: A Waitable which will trigger once the scan finishes based on the timeout specified.
                 Waitable returns a ScanReportCollection of the advertising packets found
        """
        self.stop()
        # Cache the device's address on scan start
        self._own_address = self.ble_device.address
        if clear_scan_reports:
            self.scan_report = ScanReportCollection()
        if not scan_parameters:
            scan_parameters = self._default_scan_params
        else:
            # Make sure the scan parameters are valid
            scan_parameters.validate()
        self.ble_device.ble_driver.ble_gap_scan_start(scan_parameters)
        self._is_scanning = True
        return scan_waitable.ScanFinishedWaitable(self.ble_device)

    def stop(self):
        """
        Stops scanning
        """
        self._is_scanning = False

        try:
            self.ble_device.ble_driver.ble_gap_scan_stop()
        except:
            pass

    def _on_adv_report(self, driver, adv_report):
        bond_entry = self.ble_device.bond_db.find_entry(self._own_address, adv_report.peer_addr, peer_is_client=False)
        if bond_entry:
            resolved_peer_address = bond_entry.resolved_peer_address()
        else:
            resolved_peer_address = None
        scan_report = self.scan_report.update(adv_report, resolved_peer_address)
        self._on_scan_received.notify(self.ble_device, scan_report)

    def _on_timeout_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.scan:
            self._is_scanning = False
            self._on_scan_timeout.notify(self.ble_device, self.scan_report)
