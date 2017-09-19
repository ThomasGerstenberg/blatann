import threading
from blatann.nrf import nrf_types
from blatann import gatt

_security_mapping = {
    gatt.SecurityLevel.NO_ACCESS: nrf_types.BLEGapSecModeType.NO_ACCESS,
    gatt.SecurityLevel.OPEN: nrf_types.BLEGapSecModeType.OPEN,
    gatt.SecurityLevel.JUST_WORKS: nrf_types.BLEGapSecModeType.ENCRYPTION,
    gatt.SecurityLevel.MITM: nrf_types.BLEGapSecModeType.MITM,

}


class GattsCharacteristic(gatt.Characteristic):
    def __init__(self, ble_device, peer, uuid, properties, value="", prefer_indications=True):
        super(GattsCharacteristic, self).__init__(ble_device, peer, uuid)
        self.properties = properties
        self.value = value
        self.prefer_indications = prefer_indications
        self._handler_lock = threading.Lock()
        self._on_write_handlers = []
        self._on_read_handlers = []

    def set_value(self, value, notify_client=False):
        pass

    def register_on_write(self, on_write):
        with self._handler_lock:
            self._on_write_handlers.append(on_write)

    def deregister_on_write(self, on_write):
        with self._handler_lock:
            if on_write in self._on_write_handlers:
                self._on_write_handlers.remove(on_write)


class GattsService(gatt.Service):
    def add_characteristic(self, uuid, properties, initial_value=""):
        """

        :type uuid: blatann.uuid.Uuid
        :type properties: gatt.CharacteristicProperties
        :param initial_value:
        :return:
        """
        c = GattsCharacteristic(self.ble_device, self.peer, uuid, properties, initial_value)
        # Register UUID
        self.ble_device.uuid_manager.register_uuid(uuid)

        # Create property structure
        props = nrf_types.BLECharacteristicProperties(properties.broadcast, properties.read, False, properties.write,
                                                      properties.notify, properties.indicate, False)
        # Create cccd metadata if notify/indicate enabled
        if properties.notify or properties.indicate:
            cccd_metadata = nrf_types.BLEGattsAttrMetadata(read_auth=False, write_auth=False)
        else:
            cccd_metadata = None

        char_md = nrf_types.BLEGattsCharMetadata(props, cccd_metadata=cccd_metadata)
        security = _security_mapping[properties.security_level]
        attr_metadata = nrf_types.BLEGattsAttrMetadata(security, security)
        attribute = nrf_types.BLEGattsAttribute(uuid.nrf_uuid, attr_metadata, properties.max_len, initial_value)

        handles = nrf_types.BLEGattsCharHandles()  # Populated in call
        self.ble_device.ble_driver.ble_gatts_characteristic_add(self.start_handle, char_md, attribute, handles)

        c.value_handle = handles.value_handle
        c.cccd_handle = handles.cccd_handle
        self.characteristics.append(c)


class GattsDatabase(gatt.GattDatabase):
    def __init__(self, ble_device, peer):
        super(GattsDatabase, self).__init__(ble_device, peer)

    def add_service(self, uuid, service_type=gatt.ServiceType.PRIMARY):
        # Register UUID
        self.ble_device.uuid_manager.register_uuid(uuid)
        handle = nrf_types.BleGattHandle()
        # Call code to add service to driver
        self.ble_device.ble_driver.ble_gatts_service_add(service_type.value, uuid.nrf_uuid, handle)
        service = GattsService(self.ble_device, self.peer, uuid, service_type, handle.handle)
        service.start_handle = handle.handle
        service.end_handle = handle.handle
        self.services.append(service)
        return service

