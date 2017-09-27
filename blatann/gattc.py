import logging
from blatann.event_type import EventSource, Event
from blatann.nrf.nrf_types.gatt import BLE_GATT_HANDLE_INVALID
from blatann import gatt

logger = logging.getLogger(__name__)


class GattcCharacteristic(gatt.Characteristic):
    pass


class GattcService(gatt.Service):
    pass


class GattcDatabase(gatt.GattDatabase):
    def __init__(self, ble_device, peer):
        super(GattcDatabase, self).__init__(ble_device, peer)


