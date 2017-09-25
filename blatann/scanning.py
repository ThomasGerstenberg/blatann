from blatann.nrf import nrf_events, nrf_types
from blatann.event_type import Event, EventSource
from blatann.waitables import scan_waitable
from blatann import uuid


class ScanParameters(nrf_types.BLEGapScanParams):
    pass


class ScanEntry(object):
    def __init__(self, adv_report):
        """
        :type adv_report: nrf_events.GapEvtAdvReport
        """
        self.peer_address = adv_report.peer_addr
        self.advertise_data = adv_report.adv_data.records.copy()
        self._update_device_name()

    def _update_device_name(self):
        if nrf_types.BLEAdvData.Types.complete_local_name in self.advertise_data:
            self.device_name = str(bytearray(self.advertise_data[nrf_types.BLEAdvData.Types.complete_local_name]))
        elif nrf_types.BLEAdvData.Types.short_local_name in self.advertise_data:
            self.device_name = str(bytearray(self.advertise_data[nrf_types.BLEAdvData.Types.short_local_name]))
        else:
            self.device_name = str(self.peer_address)

    def update(self, adv_report):
        """
        :type adv_report: nrf_events.GapEvtAdvReport
        """
        if adv_report.peer_addr != self.peer_address:
            print("Peer address doesn't match")
            return
        self.advertise_data.update(adv_report.adv_data.records)
        self._update_device_name()

    def __repr__(self):
        return "{!r}: {}".format(self.device_name, self.advertise_data)


class AdvertisingReportCollection(object):
    def __init__(self):
        self.all_scans = []
        self.scans_by_peer_address = {}

    def clear(self):
        self.all_scans = []

    def add(self, scan_event):
        """
        :type scan_event: nrf_events.GapEvtAdvReport
        """
        scan_entry = ScanEntry(scan_event)
        self.all_scans.append(scan_entry)
        if scan_event.peer_addr in self.scans_by_peer_address.keys():
            self.scans_by_peer_address[scan_event.peer_addr].update(scan_event)
        else:
            self.scans_by_peer_address[scan_event.peer_addr] = scan_entry


class Scanner(object):
    def __init__(self, ble_device):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.ble_device = ble_device
        self._default_scan_params = ScanParameters(200, 150, 10)
        self.scanning = False
        ble_device.ble_driver.event_subscribe(self._on_advertise_report_event, nrf_events.GapEvtAdvReport)
        self.scan_report = AdvertisingReportCollection()

    def set_default_scan_params(self, interval_ms=200, window_ms=150, timeout_seconds=10):
        self._default_scan_params.interval_ms = interval_ms
        self._default_scan_params.window_ms = window_ms
        self._default_scan_params.timeout_s = timeout_seconds

    def start_scan(self, scan_parameters=None, clear_scan_reports=True):
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
        if not self.scanning:
            return
        self.scanning = False
        self.ble_device.ble_driver.ble_gap_scan_stop()

    def _on_advertise_report_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtAdvReport
        """
        self.scan_report.add(event)
