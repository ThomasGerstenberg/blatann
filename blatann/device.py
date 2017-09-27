from blatann.nrf.nrf_driver import NrfDriver
from blatann.nrf.nrf_observers import NrfDriverObserver
from blatann.nrf import nrf_events, nrf_event_sync

from blatann import uuid, advertising, scanning, peer, gatts, exceptions
from blatann.waitables.connection_waitable import ConnectionWaitable


class BleDevice(NrfDriverObserver):
    def __init__(self, comport="COM1"):
        self.ble_driver = NrfDriver(comport)
        self.ble_driver.observer_register(self)
        self.ble_driver.event_subscribe(self._on_user_mem_request, nrf_events.EvtUserMemoryRequest)
        self.ble_driver.open()
        # TODO: BLE Configuration
        self.ble_driver.ble_enable()

        self.client = peer.Client(self)
        self.connected_peripherals = {}
        self.connecting_peripheral = None

        self.uuid_manager = uuid.UuidManager(self.ble_driver)
        self.advertiser = advertising.Advertiser(self, self.client)
        self.scanner = scanning.Scanner(self)
        self._db = gatts.GattsDatabase(self, self.client)
        self._default_conn_params = peer.DEFAULT_CONNECTION_PARAMS

    def __del__(self):
        self.ble_driver.observer_unregister(self)
        self.ble_driver.close()

    @property
    def database(self):
        return self._db

    def connect(self, peer_address, connection_params=None):
        if peer_address in self.connected_peripherals.keys():
            raise exceptions.InvalidStateException("Already connected to {}".format(peer_address))
        if self.connecting_peripheral is not None:
            raise exceptions.InvalidStateException("Cannot initiate a new connection while connecting to another")

        if not connection_params:
            connection_params = self._default_conn_params

        self.connecting_peripheral = peer.Peripheral(self, peer_address, connection_params)
        self.ble_driver.ble_gap_connect(peer_address)
        return ConnectionWaitable(self, self.connecting_peripheral, nrf_events.BLEGapRoles.central)

    def set_default_peripheral_connection_params(self, min_interval_ms, max_interval_ms, timeout_ms, slave_latency=0):
        self._default_conn_params = peer.ConnectionParameters(min_interval_ms, max_interval_ms, timeout_ms, slave_latency)

    def _on_user_mem_request(self, nrf_driver, event):
        # Only action that can be taken
        self.ble_driver.ble_user_mem_reply(event.conn_handle)

    def on_driver_event(self, nrf_driver, event):
        print("Got driver event: {}".format(event))
        if isinstance(event, nrf_events.GapEvtConnected):
            if event.role == nrf_events.BLEGapRoles.periph:
                self.client.peer_connected(event.conn_handle, event.peer_addr)
            else:
                if self.connecting_peripheral.peer_address != event.peer_addr:
                    print("Mismatching address between connecting peripheral and peer event: "
                          "{} vs {}".format(self.connecting_peripheral.address, event.peer_addr))
                else:
                    self.connected_peripherals[self.connecting_peripheral.peer_address] = self.connecting_peripheral
                    self.connecting_peripheral.peer_connected(event.conn_handle, event.peer_addr)
                self.connecting_peripheral = None

        if isinstance(event, nrf_events.GapEvtTimeout):
            if event.src == nrf_events.BLEGapTimeoutSrc.conn:
                self.connecting_peripheral = None


