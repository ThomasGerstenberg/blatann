from blatann.nrf import nrf_observers, nrf_events, nrf_types
from blatann import gatts, peer


class PeripheralManager(nrf_observers.NrfDriverObserver):
    def __init__(self, ble_device):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.ble_device = ble_device
        self.ble_device.ble_driver.observer_register(self)
        self.peer = peer.Peer()
        self._db = gatts.GattsDatabase(self.ble_device, self.peer)
        self._restart_adv_on_disconnect = True

    def __del__(self):
        self.ble_device.ble_driver.observer_unregister(self)

    def set_advertise_data(self, advertise_data=nrf_types.BLEAdvData(), scan_data=nrf_types.BLEAdvData()):
        self.ble_device.ble_driver.ble_gap_adv_data_set(advertise_data, scan_data)

    def advertise(self, adv_interval_ms=100, timeout_sec=0, restart_on_disconnect=True):
        params = nrf_types.BLEGapAdvParams(adv_interval_ms, timeout_sec)
        self._restart_adv_on_disconnect = restart_on_disconnect
        self.ble_device.ble_driver.ble_gap_adv_start(params)

    def stop_advertising(self):
        self._restart_adv_on_disconnect = False
        self.ble_device.ble_driver.ble_gap_adv_stop()

    @property
    def database(self):
        return self._db

    def on_driver_event(self, nrf_driver, event):
        if isinstance(event, nrf_events.GapEvtConnected):
            if event.role == nrf_events.BLEGapRoles.periph:
                self.peer.peer_connected(event.conn_handle, event.peer_addr)
