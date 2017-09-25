from blatann.nrf import nrf_events, nrf_types
from blatann.waitables.connected_waitable import ConnectionWaitable
from blatann.event_type import Event, EventSource


class AdvertisingData(nrf_types.BLEAdvData):
    pass


class Advertiser(object):
    def __init__(self, ble_device, client):
        """
        :type ble_device: blatann.device.BleDevice
        :type client: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.advertising = False
        self._restart_adv_on_disconnect = False
        self.client = client
        self.ble_device.ble_driver.event_subscribe(self._handle_adv_timeout, nrf_events.GapEvtTimeout)
        self._on_advertising_timeout = EventSource("Advertising Timeout")

    @property
    def on_advertising_timeout(self):
        return self._on_advertising_timeout

    def set_advertise_data(self, advertise_data=AdvertisingData(), scan_data=AdvertisingData()):
        self.ble_device.ble_driver.ble_gap_adv_data_set(advertise_data, scan_data)

    def start(self, adv_interval_ms=100, timeout_sec=0, restart_on_disconnect=True):
        if self.advertising:
            self.stop()
        params = nrf_types.BLEGapAdvParams(adv_interval_ms, timeout_sec)
        self._restart_adv_on_disconnect = restart_on_disconnect
        self.ble_device.ble_driver.ble_gap_adv_start(params)
        self.advertising = True
        return ConnectionWaitable(self.ble_device, self.client)

    def stop(self):
        if not self.advertising:
            return
        self.advertising = False
        self.ble_device.ble_driver.ble_gap_adv_stop()

    def _handle_adv_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.advertising:
            self.advertising = False
            self._on_advertising_timeout.notify()
