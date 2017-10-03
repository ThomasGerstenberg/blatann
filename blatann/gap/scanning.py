import logging

from blatann import exceptions
from blatann.gap import advertising
from blatann.nrf import nrf_events, nrf_types
from blatann.waitables import scan_waitable

logger = logging.getLogger(__name__)


class ScanParameters(nrf_types.BLEGapScanParams):
    pass


class ScanReport(object):
    def __init__(self, adv_report):
        """
        :type adv_report: nrf_events.GapEvtAdvReport
        """
        self.peer_address = adv_report.peer_addr
        self._current_advertise_data = adv_report.adv_data.records.copy()
        self.advertise_data = advertising.AdvertisingData.from_ble_adv_records(self._current_advertise_data)

    @property
    def device_name(self):
        return self.advertise_data.local_name or str(self.peer_address)

    def update(self, adv_report):
        """
        :type adv_report: nrf_events.GapEvtAdvReport
        """
        if adv_report.peer_addr != self.peer_address:
            raise exceptions.InvalidOperationException("Peer address doesn't match")
        self._current_advertise_data.update(adv_report.adv_data.records)
        self.advertise_data = advertising.AdvertisingData.from_ble_adv_records(self._current_advertise_data.copy())

    def __repr__(self):
        return "{}: {}".format(self.device_name, self.advertise_data)


class ScanReportCollection(object):
    """
    Collection of all the advertising data and scan reports found in a scanning session
    """
    def __init__(self, ble_device):
        self._all_scans = []
        self._scans_by_peer_address = {}
        ble_device.ble_driver.event_subscribe(self._on_scan_report, nrf_events.GapEvtAdvReport)

    @property
    def advertising_peers_found(self):
        """
        Gets the list of scans which have been combined and condensed into a list where each entry is a unique peer

        :return: The list of scan reports, with each being a unique peer
        :rtype: list of ScanReport
        """
        return self._scans_by_peer_address.values()

    @property
    def all_scan_reports(self):
        """
        Gets the list of all scanned advertising data found.

        :return: The list of all scan reports
        :rtype: list of ScanReport
        """
        return self._all_scans

    def clear(self):
        """
        Clears out all of the scan reports cached
        """
        self._all_scans = []
        self._scans_by_peer_address = {}

    def _on_scan_report(self, driver, scan_event):
        """
        :type event: nrf_events.GapEvtAdvReport
        """
        scan_entry = ScanReport(scan_event)
        self._all_scans.append(scan_entry)
        if scan_event.peer_addr in self._scans_by_peer_address.keys():
            self._scans_by_peer_address[scan_event.peer_addr].update(scan_event)
        else:
            self._scans_by_peer_address[scan_event.peer_addr] = scan_entry


class Scanner(object):
    def __init__(self, ble_device):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.ble_device = ble_device
        self._default_scan_params = ScanParameters(200, 150, 10)
        self.scanning = False
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self.scan_report = ScanReportCollection(ble_device)

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
                 Waitable returns a AdvertisingReportCollection of the advertising packets found
        :rtype: scan_waitable.ScanFinishedWaitable
        """
        if self.scanning:
            self.stop()
        if clear_scan_reports:
            self.scan_report.clear()
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

    def _on_timeout_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.scan:
            self.scanning = False
