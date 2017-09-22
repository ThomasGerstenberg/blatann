from blatann.nrf.nrf_driver import NrfDriver
from blatann.nrf.nrf_observers import NrfDriverObserver
from blatann.nrf import nrf_events, nrf_event_sync

from blatann import peripheral_manager, uuid


class BleDevice(NrfDriverObserver):
    def __init__(self, comport="COM1"):
        self.ble_driver = NrfDriver(comport)
        self.ble_driver.observer_register(self)
        self.ble_driver.event_subscribe(self._on_user_mem_request, nrf_events.EvtUserMemoryRequest)
        self.ble_driver.open()
        # TODO: BLE Configuration
        self.ble_driver.ble_enable()

        self.peripheral_manager = peripheral_manager.PeripheralManager(self)
        self.uuid_manager = uuid.UuidManager(self.ble_driver)
        self.active_connections = []

    def __del__(self):
        self.ble_driver.observer_unregister(self)
        self.ble_driver.close()

    def _on_user_mem_request(self, nrf_driver, event):
        # Only action that can be taken
        self.ble_driver.ble_user_mem_reply(event.conn_handle)

    def on_driver_event(self, nrf_driver, event):
        print("Got driver event: {}".format(event))
