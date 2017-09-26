from blatann.nrf import nrf_events, nrf_types
from blatann.waitables.connection_waitable import ConnectionWaitable
from blatann.event_type import Event, EventSource


class AdvertisingData(nrf_types.BLEAdvData):
    pass


class Advertiser(object):
    ADVERTISE_FOREVER = 0

    def __init__(self, ble_device, client):
        """
        :type ble_device: blatann.device.BleDevice
        :type client: blatann.peer.Client
        """
        self.ble_device = ble_device
        self.advertising = False
        self._auto_restart = False
        self.client = client
        self.ble_device.ble_driver.event_subscribe(self._handle_adv_timeout, nrf_events.GapEvtTimeout)
        self.ble_device.ble_driver.event_subscribe(self._handle_disconnect, nrf_events.GapEvtDisconnected)
        self._on_advertising_timeout = EventSource("Advertising Timeout")
        self._advertise_interval = 100
        self._timeout = self.ADVERTISE_FOREVER

    @property
    def on_advertising_timeout(self):
        return self._on_advertising_timeout

    def set_advertise_data(self, advertise_data=AdvertisingData(), scan_data=AdvertisingData()):
        self.ble_device.ble_driver.ble_gap_adv_data_set(advertise_data, scan_data)

    def set_default_advertise_params(self, advertise_interval, timeout_seconds):
        self._advertise_interval = advertise_interval
        self._timeout = timeout_seconds

    def start(self, adv_interval_ms=None, timeout_sec=None, auto_restart=False):
        """
        Starts advertising with the given parameters. If none given, will use the default

        :param adv_interval_ms: The interval at which to send out advertise packets, in milliseconds
        :param timeout_sec: The duration which to advertise for
        :param auto_restart: Flag indicating that advertising should restart automatically when the timeout expires, or
                             when the client disconnects
        :return: A waitable that will expire either when the timeout occurs, or a client connects.
                 Waitable Returns a peer.Client() object
        """
        if self.advertising:
            self.stop()
        if adv_interval_ms is None:
            adv_interval_ms = self._advertise_interval
        if timeout_sec is None:
            timeout_sec = self._timeout
        self._timeout = timeout_sec
        self._advertise_interval = adv_interval_ms

        params = nrf_types.BLEGapAdvParams(adv_interval_ms, timeout_sec)
        self._auto_restart = auto_restart
        self.ble_device.ble_driver.ble_gap_adv_start(params)
        self.advertising = True
        return ConnectionWaitable(self.ble_device, self.client)

    def stop(self):
        if not self.advertising:
            return
        self.advertising = False
        self._auto_restart = False
        self.ble_device.ble_driver.ble_gap_adv_stop()

    def _handle_adv_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.advertising:
            self.advertising = False
            self._on_advertising_timeout.notify()
            if self._auto_restart:
                print("Restarting")
                self.start()

    def _handle_disconnect(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if event.conn_handle == self.client.conn_handle and self._auto_restart:
            self.start()
