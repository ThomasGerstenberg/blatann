import logging
from blatann.event_type import EventSource, Event
from blatann.nrf import nrf_types
from blatann import gatt

logger = logging.getLogger(__name__)


class GattcCharacteristic(gatt.Characteristic):
    def __init__(self, ble_device, peer, uuid, properties):
        super(GattcCharacteristic, self).__init__(ble_device, peer, uuid, properties)

    @classmethod
    def from_discovered_characteristic(cls, ble_device, peer, nrf_characteristic):
        """
        :type nrf_characteristic: nrf_types.BLEGattCharacteristic
        """
        char_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_characteristic.uuid)
        properties = gatt.CharacteristicProperties.from_nrf_properties(nrf_characteristic.char_props)
        return GattcCharacteristic(ble_device, peer, char_uuid, properties)


class GattcService(gatt.Service):
    @classmethod
    def from_discovered_service(cls, ble_device, peer, nrf_service):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peripheral
        :type nrf_service: nrf_types.BLEGattService
        """
        service_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_service.uuid)
        service = GattcService(ble_device, peer, service_uuid, gatt.ServiceType.PRIMARY,
                               nrf_service.start_handle, nrf_service.end_handle)
        for c in nrf_service.chars:
            service.characteristics.append(GattcCharacteristic.from_discovered_characteristic(ble_device, peer, c))
        return service


class GattcDatabase(gatt.GattDatabase):
    def __init__(self, ble_device, peer):
        super(GattcDatabase, self).__init__(ble_device, peer)

    def add_discovered_services(self, nrf_services):
        """
        :type nrf_services: list of nrf_types.BLEGattService
        """
        for service in nrf_services:
            self.services.append(GattcService.from_discovered_service(self.ble_device, self.peer, service))
