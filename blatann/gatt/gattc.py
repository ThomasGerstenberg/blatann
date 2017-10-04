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
        :type ble_device: blatann.BleDevice
        :type peer: blatann.peer.Peripheral
        :type reader: GattcReader
        :type writer: GattcWriter
        :type uuid: blatann.uuid.Uuid
        :type properties: gatt.CharacteristicProperties
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

    """
    Properties
    """

    @property
    def value(self):
        """
        The current value of the characteristic

        :return: The last known value of the characteristic
        """
        return self._value

    @property
    def readable(self):
        return self._properties.read

    @property
    def writable(self):
        return self._properties.write

    @property
    def subscribable(self):
        """
        Gets if the characteristic can be subscribed to
        """
        return self._properties.notify or self._properties.indicate

    @property
    def subscribed(self):
        """
        Gets if the characteristic is currently subscribed to
        """
        return self.cccd_state != gatt.SubscriptionState.NOT_SUBSCRIBED

    """
    Event Handlers
    """

    def subscribe(self, on_notification_handler, prefer_indications=False):
        """
        Subscribes to the characteristic's indications or notifications, depending on what's available and the
        prefer_indications setting. Returns a Waitable that executes when the subscription on the peripheral finishes.

        The Waitable returns three parameters: (GattcCharacteristic this, gatt.GattStatusCode, gatt.SubscriptionState)

        :param on_notification_handler: The handler to be called when an indication or notification is received from
        the peripheral. Must take three parameters: (GattcCharacteristic this, gatt.GattNotificationType, bytearray data)
        :param prefer_indications: If the peripheral supports both indications and notifications,
                                   will subscribe to indications instead of notifications
        :return: A Waitable that will fire when the subscription finishes
        :rtype: blatann.waitables.Waitable
        :raises: InvalidOperationException if the characteristic cannot be subscribed to (does not support indications or notifications
        """
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
        """
        Unsubscribes from indications and notifications from the characteristic and clears out all handlers
        for the characteristic's on_notification event handler. Returns a Waitable that executes when the unsubscription
        finishes.

        The Waitable returns three parameters: (GattcCharacteristic this, gatt.GattStatusCode, gatt.SubscriptionState)

        :return:
        """
        if not self.subscribable:
            raise InvalidOperationException("Characteristic {} is not subscribable".format(self.uuid))
        value = gatt.SubscriptionState.NOT_SUBSCRIBED
        self.writer.write(self.cccd_handle, gatt.SubscriptionState.to_buffer(value))
        self._on_notification_event.clear_handlers()

        return EventWaitable(self._on_cccd_write_complete_event)

    def read(self):
        """
        Initiates a read of the characteristic and returns a Waitable that executes when the read finishes with
        the data read.

        The Waitable returns three parameters: (GattcCharacteristic this, gatt.GattStatusCode, bytearray data)

        :return: A waitable that will fire when the read finishes
        :rtype: blatann.waitables.Waitable
        :raises: InvalidOperationException if characteristic not readable
        """
        if not self.readable:
            raise InvalidStateException("Characteristic {} is not readable".format(self.uuid))
        self.reader.read(self.value_handle)
        return EventWaitable(self._on_read_complete_event)

    def write(self, data):
        """
        Initiates a write of the data provided to the characteristic and returns a Waitable that executes
        when the write completes.

        The Waitable returns three parameters: (GattcCharacteristic this, gatt.GattStatusCode status, bytearray data)

        :param data: The data to write. Can be a string, bytearray, or anything that can be converted to a bytearray
        :return: A waitable that returns when the write finishes
        :rtype: blatann.waitables.Waitable
        :raises: InvalidOperationException if characteristic is not writable
        """
        if not self.writable:
            raise InvalidStateException("Characteristic {} is not writable".format(self.uuid))
        self.writer.write(self.value_handle, bytearray(data))
        return EventWaitable(self._on_write_complete_event)

    """
    Event Handlers
    """

    def _read_complete(self, handle, status, data):
        """
        Handler for GattcReader.on_read_complete.
        Dispatches the on_read_complete event and updates the internal value if read was successful

        :param handle: The handle the read completed on
        :param status: The status of the read
        :param data: The data read
        """
        if handle == self.value_handle:
            if status == nrf_types.BLEGattStatusCode.success:
                self._value = data
            self._on_read_complete_event.notify(self, status, self._value)

    def _write_complete(self, handle, status, data):
        """
        Handler for GattcWriter.on_write_complete. Dispatches on_write_complete or on_cccd_write_complete
        depending on the handle the write finished on.

        :param handle: The attribute handle the write completed on
        :param status: The status of the write
        :param data: The data written
        """
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
        Handler for GattcEvtHvx. Dispatches the on_notifiaction_event to listeners

        :type event: nrf_events.GattcEvtHvx
        """
        if event.conn_handle != self.peer.conn_handle or event.attr_handle != self.value_handle:
            return
        if event.hvx_type == nrf_events.BLEGattHVXType.indication:
            self.ble_device.ble_driver.ble_gattc_hv_confirm(event.conn_handle, event.attr_handle)
        self._value = bytearray(event.data)
        self._on_notification_event.notify(self, self._value)

    """
    Factory methods
    """

    @classmethod
    def from_discovered_characteristic(cls, ble_device, peer, reader, writer, nrf_characteristic):
        """
        Internal factory method used to create a new characteristic from a discovered nRF Characteristic

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
        Gets the list of characteristics within the service

        :rtype: list of GattcCharacteristic
        """
        return self._characteristics

    def find_characteristic(self, characteristic_uuid):
        """
        Finds the characteristic matching the given UUID inside the service. If not found, returns None

        :param characteristic_uuid: The UUID of the characteristic to find
        :type characteristic_uuid: blatann.uuid.Uuid
        :return: The characteristic if found, otherwise None
        :rtype: GattcCharacteristic
        """
        for c in self.characteristics:
            if c.uuid == characteristic_uuid:
                return c

    @classmethod
    def from_discovered_service(cls, ble_device, peer, reader, writer, nrf_service):
        """
        Internal factory method used to create a new service from a discovered nRF Service.
        Also takes care of creating and adding all characteristics within the service

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
    """
    Represents a remote GATT Database which lives on a connected peripheral. Contains all discovered services,
    characteristics, and descriptors
    """
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
        """
        Finds the characteristic matching the given UUID inside the database. If not found, returns None

        :param service_uuid: The UUID of the service to find
        :type service_uuid: blatann.uuid.Uuid
        :return: The service if found, otherwise None
        :rtype: GattcService
        """
        for s in self.services:
            if s.uuid == service_uuid:
                return s

    def find_characteristic(self, characteristic_uuid):
        """
        Finds the characteristic matching the given UUID inside the database. If not found, returns None

        :param characteristic_uuid: The UUID of the characteristic to find
        :type characteristic_uuid: blatann.uuid.Uuid
        :return: The characteristic if found, otherwise None
        :rtype: GattcCharacteristic
        """
        for c in self.iter_characteristics():
            if c.uuid == characteristic_uuid:
                return c

    def iter_characteristics(self):
        """
        Iterates through all the characteristics in the database

        :return: An iterable of the characterisitcs in the database
        :rtype: collections.Iterable[GattcCharacteristic]
        """
        for s in self.services:
            for c in s.characteristics:
                yield c

    def add_discovered_services(self, nrf_services):
        """
        Adds the discovered NRF services from the service_discovery module.
        Used for internal purposes primarily.

        :param nrf_services: The discovered services with all the characteristics and descriptors
        :type nrf_services: list of nrf_types.BLEGattService
        """
        for service in nrf_services:
            self.services.append(GattcService.from_discovered_service(self.ble_device, self.peer,
                                                                      self._reader, self._writer, service))
