from __future__ import annotations
import logging
from typing import List, Optional, Iterable

from blatann import gatt
from blatann.gatt.gattc_attribute import GattcAttribute
from blatann.gatt.managers import GattcOperationManager
from blatann.bt_sig.uuids import Uuid, DeclarationUuid, DescriptorUuid
from blatann.event_type import EventSource, Event
from blatann.gatt.reader import GattcReader
from blatann.gatt.writer import GattcWriter
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable, IdBasedEventWaitable
from blatann.exceptions import InvalidOperationException
from blatann.event_args import *


logger = logging.getLogger(__name__)


class GattcCharacteristic(gatt.Characteristic):
    """
    Represents a characteristic that lives within a service in the server's GATT database.

    This class is normally not instantiated directly and instead created when the database is discovered
    via :meth:`Peer.discover_services() <blatann.peer.Peer.discover_services>`
    """
    def __init__(self, ble_device, peer, uuid: Uuid,
                 properties: gatt.CharacteristicProperties,
                 decl_attr: GattcAttribute,
                 value_attr: GattcAttribute,
                 cccd_attr: GattcAttribute = None,
                 attributes: List[GattcAttribute] = None):
        super(GattcCharacteristic, self).__init__(ble_device, peer, uuid, properties)
        self._decl_attr = decl_attr
        self._value_attr = value_attr
        self._cccd_attr = cccd_attr
        self._on_notification_event = EventSource("On Notification", logger)
        self._attributes = tuple(sorted(attributes, key=lambda d: d.handle)) or ()
        self.peer = peer

        self._on_read_complete_event = EventSource("On Read Complete", logger)
        self._on_write_complete_event = EventSource("Write Complete", logger)
        self._on_cccd_write_complete_event = EventSource("CCCD Write Complete", logger)

        self._value_attr.on_read_complete.register(self._read_complete)
        self._value_attr.on_write_complete.register(self._write_complete)
        if self._cccd_attr:
            self._cccd_attr.on_write_complete.register(self._cccd_write_complete)

        self.peer.driver_event_subscribe(self._on_indication_notification, nrf_events.GattcEvtHvx)

    """
    Properties
    """

    @property
    def declaration_attribute(self) -> GattcAttribute:
        """
        **Read Only**

        Gets the declaration attribute of the characteristic
        """
        return self._decl_attr

    @property
    def value_attribute(self) -> GattcAttribute:
        """
        **Read Only**

        Gets the value attribute of the characteristic
        """
        return self._value_attr

    @property
    def value(self) -> bytes:
        """
        **Read Only**

        The current value of the characteristic. This is updated through read, write, and notify operations
        """
        return self._value_attr.value

    @property
    def readable(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic can be read from
        """
        return self._properties.read

    @property
    def writable(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic can be written to
        """
        return self._properties.write

    @property
    def writable_without_response(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic accepts write commands that don't require a confirmation response
        """
        return self._properties.write_no_response

    @property
    def subscribable(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic can be subscribed to
        """
        return self._properties.notify or self._properties.indicate

    @property
    def subscribable_indications(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic can be subscribed to using indications
        """
        return self._properties.indicate

    @property
    def subscribable_notifications(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic can be subscribed to using notifications
        """
        return self._properties.notify

    @property
    def subscribed(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic is currently subscribed to
        """
        return self.cccd_state != gatt.SubscriptionState.NOT_SUBSCRIBED

    @property
    def attributes(self) -> Iterable[GattcAttribute]:
        """
        **Read Only**

        Returns the list of all attributes/descriptors that reside in the characteristic.
        This includes the declaration attribute, value attribute, and descriptors (CCCD, Name, etc.)
        """
        return self._attributes

    @property
    def string_encoding(self) -> str:
        """
        The default method for encoding strings into bytes when a string is provided as a value

        :getter: Gets the current string encoding for the characteristic
        :setter: Sets the string encoding for the characteristic
        """
        return self._value_attr.string_encoding

    @string_encoding.setter
    def string_encoding(self, encoding):
        self._value_attr.string_encoding = encoding

    """
    Events
    """

    @property
    def on_read_complete(self) -> Event[GattcCharacteristic, ReadCompleteEventArgs]:
        """
        Event that is raised when a read operation from the characteristic is completed
        """
        return self._on_read_complete_event

    @property
    def on_write_complete(self) -> Event[GattcCharacteristic, WriteCompleteEventArgs]:
        """
        Event that is raised when a write operation to the characteristic is completed
        """
        return self._on_write_complete_event

    @property
    def on_notification_received(self) -> Event[GattcCharacteristic, NotificationReceivedEventArgs]:
        """
        Event that is raised when an indication or notification is received on the characteristic
        """
        return self._on_notification_event

    """
    Public Methods
    """

    def subscribe(self, on_notification_handler: Callable[[GattcCharacteristic, NotificationReceivedEventArgs], None],
                  prefer_indications=False) -> EventWaitable[GattcCharacteristic, SubscriptionWriteCompleteEventArgs]:
        """
        Subscribes to the characteristic's indications or notifications, depending on what's available and the
        prefer_indications setting. Returns a Waitable that triggers when the subscription on the peripheral finishes.

        :param on_notification_handler: The handler to be called when an indication or notification is received from
            the peripheral. Must take two parameters: (GattcCharacteristic this, NotificationReceivedEventArgs event args)
        :param prefer_indications: If the peripheral supports both indications and notifications,
            will subscribe to indications instead of notifications
        :return: A Waitable that will trigger when the subscription finishes
        :raises: InvalidOperationException if the characteristic cannot be subscribed to
            (characteristic does not support indications or notifications)
        """
        if not self.subscribable:
            raise InvalidOperationException("Cannot subscribe to Characteristic {}".format(self.uuid))
        if prefer_indications and self._properties.indicate or not self._properties.notify:
            value = gatt.SubscriptionState.INDICATION
        else:
            value = gatt.SubscriptionState.NOTIFY
        self._on_notification_event.register(on_notification_handler)
        waitable = self._cccd_attr.write(gatt.SubscriptionState.to_buffer(value))
        return IdBasedEventWaitable(self._on_cccd_write_complete_event, waitable.id)

    def unsubscribe(self) -> EventWaitable[GattcCharacteristic, SubscriptionWriteCompleteEventArgs]:
        """
        Unsubscribes from indications and notifications from the characteristic and clears out all handlers
        for the characteristic's on_notification event handler. Returns a Waitable that triggers when the unsubscription
        finishes.

        :return: A Waitable that will trigger when the unsubscription operation finishes
        :raises: InvalidOperationException if characteristic cannot be subscribed to
            (characteristic does not support indications or notifications)
        """
        if not self.subscribable:
            raise InvalidOperationException("Cannot subscribe to Characteristic {}".format(self.uuid))
        value = gatt.SubscriptionState.NOT_SUBSCRIBED
        waitable = self._cccd_attr.write(gatt.SubscriptionState.to_buffer(value))
        self._on_notification_event.clear_handlers()

        return IdBasedEventWaitable(self._on_cccd_write_complete_event, waitable.id)

    def read(self) -> EventWaitable[GattcCharacteristic, ReadCompleteEventArgs]:
        """
        Initiates a read of the characteristic and returns a Waitable that triggers when the read finishes with
        the data read.

        :return: A waitable that will trigger when the read finishes
        :raises: InvalidOperationException if characteristic not readable
        """
        if not self.readable:
            raise InvalidOperationException("Characteristic {} is not readable".format(self.uuid))
        waitable = self._value_attr.read()
        return IdBasedEventWaitable(self._on_read_complete_event, waitable.id)

    def write(self, data) -> EventWaitable[GattcCharacteristic, WriteCompleteEventArgs]:
        """
        Performs a write request of the data provided to the characteristic and returns a Waitable that triggers
        when the write completes and the confirmation response is received from the other device.

        :param data: The data to write. Can be a string, bytes, or anything that can be converted to bytes
        :type data: str or bytes or bytearray
        :return: A waitable that returns when the write finishes
        :raises: InvalidOperationException if characteristic is not writable
        """
        if not self.writable:
            raise InvalidOperationException("Characteristic {} is not writable".format(self.uuid))
        if isinstance(data, str):
            data = data.encode(self.string_encoding)
        waitable = self._value_attr.write(bytes(data), True)
        return IdBasedEventWaitable(self._on_write_complete_event, waitable.id)

    def write_without_response(self, data) -> EventWaitable[GattcCharacteristic, WriteCompleteEventArgs]:
        """
        Performs a write command, which does not require the peripheral to send a confirmation response packet.
        This is a faster but lossy operation in the case that the packet is dropped/never received by the peer.
        This returns a waitable that triggers when the write is transmitted to the peripheral device.

        .. note:: Data sent without responses must fit within a single MTU minus 3 bytes for the operation overhead.

        :param data: The data to write. Can be a string, bytes, or anything that can be converted to bytes
        :type data: str or bytes or bytearray
        :return: A waitable that returns when the write finishes
        :raises: InvalidOperationException if characteristic is not writable without responses
        """
        if not self.writable_without_response:
            raise InvalidOperationException("Characteristic {} does not accept "
                                            "writes without responses".format(self.uuid))
        if isinstance(data, str):
            data = data.encode(self.string_encoding)
        waitable = self._value_attr.write(bytes(data), False)
        return IdBasedEventWaitable(self._on_write_complete_event, waitable.id)

    def find_descriptor(self, uuid: Uuid) -> Optional[GattcAttribute]:
        """
        Searches for the descriptor/attribute matching the UUID provided and returns the attribute.
        If not found, returns None.
        If multiple attributes with the same UUID exist in the characteristic, this returns the first attribute found.

        :param uuid: The UUID to search for
        :return: THe descriptor attribute, if found
        """
        for attr in self._attributes:
            if attr.uuid == uuid:
                return attr

    """
    Event Handlers
    """

    def _read_complete(self, sender: GattcAttribute, event_args: ReadCompleteEventArgs):
        """
        Handler for GattcAttribute.on_read_complete.
        Dispatches the on_read_complete event and updates the internal value if read was successful
        """
        self._on_read_complete_event.notify(self, event_args)

    def _write_complete(self, sender: GattcAttribute, event_args: WriteCompleteEventArgs):
        """
        Handler for value_attribute.on_write_complete. Dispatches on_write_complete.
        """
        self._on_write_complete_event.notify(self, event_args)

    def _cccd_write_complete(self, sender: GattcAttribute, event_args: WriteCompleteEventArgs):
        """
        Handler for cccd_attribute.on_write_complete. Dispatches on_cccd_write_complete.
        """
        if event_args.status == nrf_types.BLEGattStatusCode.success:
            self.cccd_state = gatt.SubscriptionState.from_buffer(bytearray(event_args.value))
        args = SubscriptionWriteCompleteEventArgs(event_args.id, self.cccd_state,
                                                  event_args.status, event_args.reason)
        self._on_cccd_write_complete_event.notify(self, args)

    def _on_indication_notification(self, driver, event):
        """
        Handler for GattcEvtHvx. Dispatches the on_notification_event to listeners

        :type event: nrf_events.GattcEvtHvx
        """
        if (event.conn_handle != self.peer.conn_handle or
                event.attr_handle != self._value_attr.handle):
            return

        is_indication = False
        if event.hvx_type == nrf_events.BLEGattHVXType.indication:
            is_indication = True
            self.ble_device.ble_driver.ble_gattc_hv_confirm(event.conn_handle, event.attr_handle)

        # Update the value attribute with the data that was provided
        self._value_attr.update(bytearray(event.data))
        self._on_notification_event.notify(self, NotificationReceivedEventArgs(self.value, is_indication))

    """
    Factory methods
    """

    @classmethod
    def from_discovered_characteristic(cls, ble_device, peer, read_write_manager, nrf_characteristic):
        """
        Internal factory method used to create a new characteristic from a discovered nRF Characteristic

        :meta private:
        :type ble_device: blatann.BleDevice
        :type peer: blatann.peer.Peer
        :type read_write_manager: GattcOperationManager
        :type nrf_characteristic: nrf_types.BLEGattCharacteristic
        """
        char_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_characteristic.uuid)
        properties = gatt.CharacteristicProperties.from_nrf_properties(nrf_characteristic.char_props)

        # Create the declaration and value attributes to start
        decl_attr = GattcAttribute(DeclarationUuid.characteristic, nrf_characteristic.handle_decl,
                                   read_write_manager, nrf_characteristic.data_decl)
        value_attr = GattcAttribute(char_uuid, nrf_characteristic.handle_value,
                                    read_write_manager, nrf_characteristic.data_value)
        cccd_attr = None

        attributes = [decl_attr, value_attr]

        for nrf_desc in nrf_characteristic.descs:
            # Already added the handle and value attributes, skip them here
            if nrf_desc.handle in [nrf_characteristic.handle_decl, nrf_characteristic.handle_value]:
                continue

            attr_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_desc.uuid)
            attr = GattcAttribute(attr_uuid, nrf_desc.handle, read_write_manager)

            if attr_uuid == DescriptorUuid.cccd:
                cccd_attr = attr
            attributes.append(attr)

        return GattcCharacteristic(ble_device, peer, char_uuid, properties,
                                   decl_attr, value_attr, cccd_attr, attributes)


class GattcService(gatt.Service):
    """
    Represents a service that lives within the server's GATT database.

    This class is normally not instantiated directly and instead created when the database is discovered
    via :meth:`Peer.discover_services() <blatann.peer.Peer.discover_services>`
    """
    @property
    def characteristics(self) -> List[GattcCharacteristic]:
        """
        Gets the list of characteristics within the service
        """
        return self._characteristics

    def find_characteristic(self, characteristic_uuid: Uuid) -> Optional[GattcCharacteristic]:
        """
        Finds the characteristic matching the given UUID inside the service. If not found, returns None.
        If multiple characteristics with the same UUID exist within the service, this will return the first one found.

        :param characteristic_uuid: The UUID of the characteristic to find
        :return: The characteristic if found, otherwise None
        """
        for c in self.characteristics:
            if c.uuid == characteristic_uuid:
                return c

    @classmethod
    def from_discovered_service(cls, ble_device, peer, read_write_manager, nrf_service):
        """
        Internal factory method used to create a new service from a discovered nRF Service.
        Also takes care of creating and adding all characteristics within the service

        :meta private:
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        :type read_write_manager: GattcOperationManager
        :type nrf_service: nrf_types.BLEGattService
        """
        service_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_service.uuid)
        service = GattcService(ble_device, peer, service_uuid, gatt.ServiceType.PRIMARY,
                               nrf_service.start_handle, nrf_service.end_handle)
        for c in nrf_service.chars:
            char = GattcCharacteristic.from_discovered_characteristic(ble_device, peer, read_write_manager, c)
            service.characteristics.append(char)
        return service


class GattcDatabase(gatt.GattDatabase):
    """
    Represents a remote GATT Database which lives on a connected peripheral. Contains all discovered services,
    characteristics, and descriptors
    """
    def __init__(self, ble_device, peer, write_no_resp_queue_size=1):
        super(GattcDatabase, self).__init__(ble_device, peer)
        self._writer = GattcWriter(ble_device, peer)
        self._reader = GattcReader(ble_device, peer)
        self._read_write_manager = GattcOperationManager(ble_device, peer, self._reader, self._writer, write_no_resp_queue_size)

    @property
    def services(self) -> List[GattcService]:
        """
        Gets the list of services within the database
        """
        return self._services

    def find_service(self, service_uuid: Uuid) -> Optional[GattcService]:
        """
        Finds the service matching the given UUID inside the database. If not found, returns None.
        If multiple services with the same UUID exist in the database, this will return the first service found.

        :param service_uuid: The UUID of the service to find
        :return: The service if found, otherwise None
        """
        for s in self.services:
            if s.uuid == service_uuid:
                return s

    def find_characteristic(self, characteristic_uuid) -> Optional[GattcCharacteristic]:
        """
        Finds the characteristic matching the given UUID inside the database. If not found, returns None.
        If multiple characteristics with the same UUID exist in the database, this will return the first characteristic found.

        :param characteristic_uuid: The UUID of the characteristic to find
        :type characteristic_uuid: blatann.uuid.Uuid
        :return: The characteristic if found, otherwise None
        :rtype: GattcCharacteristic
        """
        for c in self.iter_characteristics():
            if c.uuid == characteristic_uuid:
                return c

    def iter_characteristics(self) -> Iterable[GattcCharacteristic]:
        """
        Iterates through all the characteristics in the database

        :return: An iterable of the characterisitcs in the database
        """
        for s in self.services:
            for c in s.characteristics:
                yield c

    def add_discovered_services(self, nrf_services):
        """
        Adds the discovered NRF services from the service_discovery module.
        Used for internal purposes.

        :meta private:
        :param nrf_services: The discovered services with all the characteristics and descriptors
        :type nrf_services: List[nrf_types.BLEGattService]
        """
        for service in nrf_services:
            self.services.append(GattcService.from_discovered_service(self.ble_device, self.peer,
                                                                      self._read_write_manager, service))
