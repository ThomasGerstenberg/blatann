from blatann.nrf.nrf_driver import NrfDriver
from blatann.nrf.nrf_observers import NrfDriverObserver
from blatann.nrf import nrf_events, nrf_event_sync

from blatann import peripheral, uuid


class BleDevice(NrfDriverObserver):
    def __init__(self, comport="COM1"):
        self.ble_driver = NrfDriver(comport)
        self.ble_driver.observer_register(self)
        self.ble_driver.open()
        self.ble_driver.ble_enable()

        self.peripheral = peripheral.PeripheralManager(self)
        self.uuid_manager = uuid.UuidManager(self.ble_driver)
        self.active_connections = []

    def __del__(self):
        self.ble_driver.observer_unregister(self)
        self.ble_driver.close()

    def on_driver_event(self, nrf_driver, event):
        print("Got driver event: {}".format(event))
        if isinstance(event, nrf_events.GapEvtConnected):
            print("Connected")

    def wait_for_connection(self, timeout=30):
        with nrf_event_sync.EventSync(self.ble_driver, nrf_events.GapEvtConnected) as sync:
            event = sync.get(timeout=timeout)
        return event