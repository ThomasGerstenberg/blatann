from blatann.nrf import nrf_events, nrf_types
from blatann.waitables.connected_waitable import ConnectionWaitable
from blatann.event_type import Event, EventSource


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

    def set_default_scan_params(self, interval_ms=200, window_ms=150, timeout_seconds=10):
        self._default_scan_params.interval_ms = interval_ms
        self._default_scan_params.window_ms = window_ms
        self._default_scan_params.timeout_s = timeout_seconds

    def start_scan(self, scan_parameters=None):
        if self.scanning:
            self.stop()
        if not scan_parameters:
            scan_parameters = self._default_scan_params
        self.ble_device.ble_driver.ble_gap_scan_start(scan_parameters)
        self.scanning = True

    def stop(self):
        if not self.scanning:
            return
        self.scanning = False
        self.ble_device.ble_driver.ble_gap_scan_stop()
