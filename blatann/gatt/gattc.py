import logging
from blatann import gatt
from blatann.event_type import EventSource, Event
from blatann.gatt.reader import GattcReader
from blatann.gatt.writer import GattcWriter
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable
from blatann.exceptions import InvalidOperationException, InvalidStateException

logger = logging.getLogger(__name__)


class GattcCharacteristic(gatt.Characteristic):
    def __init__(self, ble_device, peer, reader, writer,
                 uuid, properties, declaration_handle, value_handle, cccd_handle=None):
        """
        :param ble_device:
        :param peer:
        :type reader: GattcReader
        :type writer: GattcWriter
        :param uuid:
        :param properties:
        :param declaration_handle:
        :param value_handle:
        :param cccd_handle:
        """
        super(GattcCharacteristic, self).__init__(ble_device, peer, uuid, properties)
        self.declaration_handle = declaration_handle
        self.value_handle = value_handle
        self.cccd_handle = cccd_handle
        self.reader = reader
        self.writer = writer
        self._value = ""

        self._on_notification_event = EventSource("On Notification", logger)
        self._on_read_complete_event = EventSource("On Read Complete", logger)
        self._on_write_complete_event = EventSource("Write Complete", logger)
        self._on_cccd_write_complete_event = EventSource("CCCD Write Complete", logger)

        self.writer.on_write_complete.register(self._write_complete)
        self.reader.on_read_complete.register(self._read_complete)
        self.ble_device.ble_driver.event_subscribe(self._on_indication_notification, nrf_events.GattcEvtHvx)

    @property
    def subscribable(self):
        return self._properties.notify or self._properties.indicate

    def subscribe(self, on_notification_handler, prefer_indications=False):
        if not self.subscribable:
            raise InvalidOperationException("Characteristic {} is not subscribable".format(self.uuid))
        if prefer_indications and self._properties.indicate or not self._properties.notify:
            value = gatt.SubscriptionState.INDICATION
        else:
            value = gatt.SubscriptionState.NOTIFY
        self._on_notification_event.register(on_notification_handler)
        self.writer.write(self.cccd_handle, gatt.SubscriptionState.to_buffer(value))
        return EventWaitable(self._on_cccd_write_complete_event)

    def unsubscribe(self):
        if not self.subscribable:
            raise InvalidOperationException("Characteristic {} is not subscribable".format(self.uuid))
        value = gatt.SubscriptionState.NOT_SUBSCRIBED
        self.writer.write(self.cccd_handle, gatt.SubscriptionState.to_buffer(value))
        return EventWaitable(self._on_cccd_write_complete_event)

    def read(self):
        self.reader.read(self.value_handle)
        return EventWaitable(self._on_read_complete_event)

    def write(self, data):
        self.writer.write(self.value_handle, data)
        return EventWaitable(self._on_write_complete_event)

    def _read_complete(self, handle, status, data):
        if handle == self.value_handle:
            if status == nrf_types.BLEGattStatusCode.success:
                self._value = data
            self._on_read_complete_event.notify(self, status, self._value)

    def _write_complete(self, handle, status, data):
        # Success, update the local value
        if handle == self.value_handle:
            if status == nrf_types.BLEGattStatusCode.success:
                self._value = data
            self._on_write_complete_event.notify(self, status, self._value)
        elif handle == self.cccd_handle:
            if status == nrf_types.BLEGattStatusCode.success:
                self.cccd_state = gatt.SubscriptionState.from_buffer(bytearray(data))
            self._on_cccd_write_complete_event.notify(self, status, self.cccd_state)

    def _on_indication_notification(self, driver, event):
        """
        :type event: nrf_events.GattcEvtHvx
        """
        if event.conn_handle != self.peer.conn_handle or event.attr_handle != self.value_handle:
            return
        if event.hvx_type == nrf_events.BLEGattHVXType.indication:
            self.ble_device.ble_driver.ble_gattc_hv_confirm(event.conn_handle, event.attr_handle)
        self._on_notification_event.notify(self, bytearray(event.data))

    @classmethod
    def from_discovered_characteristic(cls, ble_device, peer, reader, writer, nrf_characteristic):
        """
        :type nrf_characteristic: nrf_types.BLEGattCharacteristic
        """
        char_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_characteristic.uuid)
        properties = gatt.CharacteristicProperties.from_nrf_properties(nrf_characteristic.char_props)
        cccd_handle_list = [d.handle for d in nrf_characteristic.descs
                            if d.uuid == nrf_types.BLEUUID.Standard.cccd]
        cccd_handle = cccd_handle_list[0] if cccd_handle_list else None
        return GattcCharacteristic(ble_device, peer, reader, writer, char_uuid, properties,
                                   nrf_characteristic.handle_decl, nrf_characteristic.handle_value, cccd_handle)


class GattcService(gatt.Service):
    @property
    def characteristics(self):
        """
        :rtype: list of GattcCharacteristic
        """
        return self._characteristics

    def find_characteristic(self, characteristic_uuid):
        for c in self.characteristics:
            if c.uuid == characteristic_uuid:
                return c

    @classmethod
    def from_discovered_service(cls, ble_device, peer, reader, writer, nrf_service):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peripheral
        :type reader: GattcReader
        :type writer: GattcWriter
        :type nrf_service: nrf_types.BLEGattService
        """
        service_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_service.uuid)
        service = GattcService(ble_device, peer, service_uuid, gatt.ServiceType.PRIMARY,
                               nrf_service.start_handle, nrf_service.end_handle)
        for c in nrf_service.chars:
            char = GattcCharacteristic.from_discovered_characteristic(ble_device, peer, reader, writer, c)
            service.characteristics.append(char)
        return service


class GattcDatabase(gatt.GattDatabase):
    def __init__(self, ble_device, peer):
        super(GattcDatabase, self).__init__(ble_device, peer)
        self._writer = GattcWriter(ble_device, peer)
        self._reader = GattcReader(ble_device, peer)

    @property
    def services(self):
        """
        :rtype: list of GattcService
        """
        return self._services

    def find_service(self, service_uuid):
        for s in self.services:
            if s.uuid == service_uuid:
                return s

    def find_characteristic(self, characteristic_uuid):
        for c in self.iter_characteristics():
            if c.uuid == characteristic_uuid:
                return c

    def iter_characteristics(self):
        for s in self.services:
            for c in s.characteristics:
                yield c

    def add_discovered_services(self, nrf_services):
        """
        :type nrf_services: list of nrf_types.BLEGattService
        """
        for service in nrf_services:
            self.services.append(GattcService.from_discovered_service(self.ble_device, self.peer,
                                                                      self._reader, self._writer, service))
