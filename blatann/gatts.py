import threading
from blatann.nrf import nrf_types
from blatann import gatt


class GattsCharacteristic(gatt.Characteristic):
    def __init__(self, ble_device, peer, uuid, properties, value=""):
        super(GattsCharacteristic, self).__init__(ble_device, peer, uuid)
        self.properties = properties
        self.value = value
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

    def register_on_read(self, on_read):
        with self._handler_lock:
            self._on_read_handlers.append(on_read)

    def deregister_on_read(self, on_read):
        with self._handler_lock:
            if on_read in self._on_read_handlers:
                self._on_read_handlers.remove(on_read)


class GattsService(gatt.Service):
    def add_characteristic(self, uuid, properties, initial_value=""):
        c = GattsCharacteristic(self.ble_device, self.peer, uuid, properties, initial_value)
        # Register UUID
        self.ble_device.uuid_manager.register_uuid(uuid)
        # Add characteristic to driver
        # TODO Fill out properties
        props = nrf_types.BLECharacteristicProperties(read=True)
        char_md = nrf_types.BLEGattsCharMetadata(props)
        attrs = nrf_types.BLEGattsAttribute(uuid.nrf_uuid, nrf_types.BLEGattsAttrMetadata(), 2)
        handles = nrf_types.BLEGattsCharHandles()
        self.ble_device.ble_driver.ble_gatts_characteristic_add(self.start_handle, char_md, attrs, handles)
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

