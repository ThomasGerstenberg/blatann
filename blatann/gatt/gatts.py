from __future__ import annotations
import typing
from typing import Optional, List, Iterable
from collections import namedtuple
import logging


from blatann.gatt.gatts_attribute import GattsAttribute, GattsAttributeProperties
from blatann.gatt.managers import GattsOperationManager
from blatann.nrf import nrf_types, nrf_events
from blatann import gatt
from blatann.bt_sig.uuids import DescriptorUuid
from blatann.uuid import Uuid
from blatann.waitables.event_waitable import IdBasedEventWaitable, EventWaitable
from blatann.exceptions import InvalidOperationException, InvalidStateException
from blatann.event_type import EventSource, Event
from blatann.event_args import *
from blatann.services.ble_data_types import BleDataStream
from blatann.gatt import PresentationFormat

if typing.TYPE_CHECKING:
    from blatann.device import BleDevice
    from blatann.peer import Peer


logger = logging.getLogger(__name__)


_security_mapping = {
    gatt.SecurityLevel.NO_ACCESS: nrf_types.BLEGapSecModeType.NO_ACCESS,
    gatt.SecurityLevel.OPEN: nrf_types.BLEGapSecModeType.OPEN,
    gatt.SecurityLevel.JUST_WORKS: nrf_types.BLEGapSecModeType.ENCRYPTION,
    gatt.SecurityLevel.MITM: nrf_types.BLEGapSecModeType.MITM,
}


class GattsUserDescriptionProperties(GattsAttributeProperties):
    """
    Properties used to configure the User Description characteristic descriptor.

    The most basic, set-once, read-only usage of this is ``GattsUserDescriptionProperties("my description")``
    """
    def __init__(self, value: Union[bytes, str],
                 write: bool = False,
                 security_level: gatt.SecurityLevel = gatt.SecurityLevel.OPEN,
                 max_length: int = 0,
                 variable_length: bool = False):
        """
        :param value: The value to set the user description to
        :param write: Whether or not the client can write/update the user description
        :param security_level: The security level for reads/writes
        :param max_length: The max length the user description can be set to.
                           If not supplied or less than len(value), will use the greater of the two
        :param variable_length: Whether or not this description can vary in length
        """
        if isinstance(value, str):
            value = value.encode("utf8")
        max_length = max(max_length, len(value))
        super(GattsUserDescriptionProperties, self).__init__(True, write, security_level, max_length or len(value),
                                                             variable_length, False, False)
        self.value = value


class GattsCharacteristicProperties(gatt.CharacteristicProperties):
    """
    Properties for Gatt Server characeristics
    """
    def __init__(self, read=True, write=False, notify=False, indicate=False, broadcast=False,
                 write_no_response=False, signed_write=False, security_level=gatt.SecurityLevel.OPEN,
                 max_length=20, variable_length=True, sccd=False,
                 user_description: GattsUserDescriptionProperties = None,
                 presentation_format: PresentationFormat = None,
                 cccd_write_security_level=gatt.SecurityLevel.OPEN):
        super(GattsCharacteristicProperties, self).__init__(read, write, notify, indicate, broadcast,
                                                            write_no_response, signed_write)
        self.security_level = security_level
        self.max_len = max_length
        self.variable_length = variable_length
        self.user_description = user_description
        self.presentation = presentation_format
        self.sccd = sccd
        self.cccd_write_security_level = cccd_write_security_level


class GattsCharacteristic(gatt.Characteristic):
    """
    Represents a single characteristic within a service. This class is usually not instantiated directly; it
    is added to a service through :meth:`GattsService.add_characteristic`
    """
    _QueuedChunk = namedtuple("QueuedChunk", ["offset", "data"])

    def __init__(self, ble_device: BleDevice,
                 peer: Peer,
                 uuid: Uuid,
                 properties: GattsCharacteristicProperties,
                 value_handle: int, cccd_handle: int, sccd_handle: int, user_desc_handle: int,
                 notification_manager: GattsOperationManager,
                 value=b"",
                 prefer_indications=True,
                 string_encoding="utf8"):
        super(GattsCharacteristic, self).__init__(ble_device, peer, uuid, properties, string_encoding)
        self._value = value
        self.prefer_indications = prefer_indications
        self._notification_manager = notification_manager

        value_attr_props = GattsAttributeProperties(properties.read, properties.write or properties.write_no_response,
                                                    properties.security_level, properties.max_len, properties.variable_length,
                                                    True, True)
        self._value_attr = GattsAttribute(self.ble_device, self.peer, self, uuid,
                                          value_handle, value_attr_props, value, string_encoding)
        self._attrs: List[GattsAttribute] = [self._value_attr]
        self._presentation_format = properties.presentation

        if cccd_handle != nrf_types.BLE_GATT_HANDLE_INVALID:
            cccd_props = GattsAttributeProperties(True, True, gatt.SecurityLevel.OPEN, 2, False, False, False)
            self._cccd_attr = GattsAttribute(self.ble_device, self.peer, self, DescriptorUuid.cccd,
                                             cccd_handle, cccd_props, b"\x00\x00")
            self._attrs.append(self._cccd_attr)
        else:
            self._cccd_attr = None
        if user_desc_handle != nrf_types.BLE_GATT_HANDLE_INVALID:
            self._user_desc_attr = GattsAttribute(self.ble_device, self.peer, self, DescriptorUuid.user_description, user_desc_handle,
                                                  properties.user_description, properties.user_description.value, string_encoding)
            self._attrs.append(self._user_desc_attr)
        else:
            self._user_desc_attr = None
        if sccd_handle != nrf_types.BLE_GATT_HANDLE_INVALID:
            sccd_props = GattsAttributeProperties(True, True, gatt.SecurityLevel.OPEN, 2, False, False, False)
            self._sccd_attr = GattsAttribute(self.ble_device, self.peer, self, DescriptorUuid.sccd,
                                             sccd_handle, sccd_props, b"\x00\x00")
            self._attrs.append(self._sccd_attr)

        # Events
        self._on_write = EventSource("Write Event", logger)
        self._on_read = EventSource("Read Event", logger)
        self._on_sub_change = EventSource("Subscription Change Event", logger)
        self._on_notify_complete = EventSource("Notification Complete Event", logger)
        # Subscribed events
        self.peer.on_disconnect.register(self._on_disconnect)
        self._value_attr.on_read.register(self._on_value_read)
        self._value_attr.on_write.register(self._on_value_write)
        if self._cccd_attr:
            self._cccd_attr.on_write.register(self._on_cccd_write)

    """
    Public Methods
    """

    def set_value(self, value, notify_client=False) -> Optional[IdBasedEventWaitable[GattsCharacteristic, NotificationCompleteEventArgs]]:
        """
        Sets the value of the characteristic.

        :param value: The value to set to. Must be an iterable type such as a str, bytes, or list of uint8 values,
                      or a BleDataStream object.
                      Length must be less than or equal to the characteristic's max length.
                      If a string is given, it will be encoded using the string_encoding property of the characteristic.
        :param notify_client: Flag whether or not to notify the client. If indications and notifications are not set up
                              for the characteristic, will raise an InvalidOperationException
        :raises: InvalidOperationException if value length is too long, or notify client set and characteristic
                 is not notifiable
        :raises: InvalidStateException if the client is not currently subscribed to the characteristic
        :return: If notify_client is true, this method will return the waitable for when the notification is sent to the client
        """
        if notify_client and not self.notifiable:
            raise InvalidOperationException("Cannot notify client. "
                                            "{} not set up for notifications or indications".format(self.uuid))

        self._value_attr.set_value(value)
        if notify_client and self.client_subscribed and not self._value_attr.read_in_process:
            return self.notify(None)

    def notify(self, data) -> IdBasedEventWaitable[GattsCharacteristic, NotificationCompleteEventArgs]:
        """
        Notifies the client with the data provided without setting the data into the characteristic value.
        If data is not provided (None), will notify with the currently-set value of the characteristic

        :param data: Optional data to notify the client with. If supplied, must be an iterable type such as a
                     str, bytes, or list of uint8 values, or a BleDataStream object.
                     Length must be less than or equal to the characteristic's max length.
                     If a string is given, it will be encoded using the string_encoding property of the characteristic.
        :raises: InvalidStateException if the client is not subscribed to the characteristic
        :raises: InvalidOperationException if the characteristic is not configured for notifications/indications
        :return: An EventWaitable that will trigger when the notification is successfully sent to the client. The waitable
                 also contains the ID of the sent notification which is used in the on_notify_complete event
        """
        if isinstance(data, BleDataStream):
            value = data.value
        if isinstance(data, str):
            value = data.encode(self.string_encoding)
        if not self.notifiable:
            raise InvalidOperationException("Cannot notify client. "
                                            "{} not set up for notifications or indications".format(self.uuid))
        if not self.client_subscribed:
            raise InvalidStateException("Client is not subscribed, cannot notify client")

        notification_id = self._notification_manager.notify(self, self._value_attr.handle,
                                                            self._on_notify_complete, data)
        return IdBasedEventWaitable(self._on_notify_complete, notification_id)

    def add_descriptor(self, uuid: Uuid, properties: GattsAttributeProperties,
                       initial_value=b"", string_encoding="utf8") -> GattsAttribute:
        """
        Creates and adds a descriptor to the characteristic

        .. note:: Due to limitations of the BLE stack, the CCCD, SCCD, User Description, Extended Properties,
           and Presentation Format descriptors cannot be added through this method. They must be added through the
           ``GattsCharacteristicProperties`` fields when creating the characteristic.

        :param uuid: The UUID of the descriptor to add, and cannot be the UUIDs of any of the reserved descriptor UUIDs in the note
        :param properties: The properties of the descriptor
        :param initial_value: The initial value to set the descriptor to
        :param string_encoding: The string encoding to use, if a string is set
        :return: the descriptor that was created and added to the characteristic
        """
        if isinstance(initial_value, str):
            initial_value = initial_value.encode(string_encoding)

        self.ble_device.uuid_manager.register_uuid(uuid)
        security = _security_mapping[properties.security_level]
        read_perm = security if properties.read else nrf_types.BLEGapSecModeType.NO_ACCESS
        write_perm = security if properties.write else nrf_types.BLEGapSecModeType.NO_ACCESS
        max_len = max(len(initial_value), properties.max_len)
        metadata = nrf_types.BLEGattsAttrMetadata(read_perm, write_perm, properties.variable_length,
                                                  read_auth=properties.read_auth, write_auth=properties.write_auth)
        attr = nrf_types.BLEGattsAttribute(uuid.nrf_uuid, metadata, max_len, initial_value)
        self.ble_device.ble_driver.ble_gatts_descriptor_add(self._value_attr.handle, attr)

        attr = GattsAttribute(self.ble_device, self.peer, self, uuid, attr.handle,
                              properties, initial_value, string_encoding)
        self._attrs.append(attr)
        return attr

    def add_constant_value_descriptor(self, uuid: Uuid, value: bytes,
                                      security_level=gatt.SecurityLevel.OPEN) -> GattsAttribute:
        """
        Adds a descriptor to the characteristic which is a constant, read-only value that cannot be updated
        after this call. This is a simplified parameter set built on top of :meth:`add_descriptor` for this common use-case.

        .. note:: See note on :meth:`add_descriptor()` for limitations on descriptors that can be added through this method.

        :param uuid: The UUID of the descriptor to add
        :param value: The value to set the descriptor to
        :param security_level: The security level for the descriptor
        :return: The descriptor that was created and added to the characteristic
        """
        props = GattsAttributeProperties(read=True, write=False, security_level=security_level,
                                         max_length=len(value), variable_length=False, write_auth=False, read_auth=False)
        return self.add_descriptor(uuid, props, value)

    """
    Properties
    """

    @property
    def max_length(self) -> int:
        """
        **Read Only**

        The max possible the value the characteristic can be set to
        """
        return self._properties.max_len

    @property
    def notifiable(self) -> bool:
        """
        **Read Only**

        Gets if the characteristic is set up to asynchonously notify clients via notifications or indications
        """
        return self._properties.indicate or self._properties.notify

    @property
    def value(self) -> bytes:
        """
        **Read Only**

        Gets the current value of the characteristic.
        Value is updated using :meth:`set_value`
        """
        return self._value

    @property
    def client_subscribed(self) -> bool:
        """
        **Read Only**

        Gets if the client is currently subscribed (notify or indicate) to this characteristic
        """
        return self.peer and self.cccd_state != gatt.SubscriptionState.NOT_SUBSCRIBED

    @property
    def attributes(self) -> Iterable[GattsAttribute]:
        """
        **Read Only**

        Gets all of the attributes and descriptors associated with this characteristic
        """
        return tuple(self._attrs)

    @property
    def user_description(self) -> Optional[GattsAttribute]:
        """
        **Read Only**

        Gets the User Description attribute for the characteristic if set in the properties.
        If the user description was not configured for the characteristic, returns ``None``
        """
        return self._user_desc_attr

    @property
    def sccd(self) -> Optional[GattsAttribute]:
        """
        **Read Only**

        Gets the Server Characteristic Configuration Descriptor (SCCD) attribute if set in the properties.
        If the SCCD was not configured for the characteristic, returns ``None``
        """
        return self._sccd_attr

    @property
    def presentation_format(self) -> Optional[PresentationFormat]:
        """
        **Read Only**

        Gets the presentation format that was set for the characteristic.
        If the presentation format was not configured for the characteristic, returns ``None``
        """
        return self._presentation_format

    @property
    def string_encoding(self) -> str:
        """
        The default method for encoding strings into bytes when a string is provided as a value

        :getter: Gets the string encoding in use
        :setter: Sets the string encoding to use
        """
        return self._value_attr.string_encoding

    @string_encoding.setter
    def string_encoding(self, value: str):
        self._value_attr.string_encoding = value

    """
    Events
    """

    @property
    def on_write(self) -> Event[GattsCharacteristic, WriteEventArgs]:
        """
        Event generated whenever a client writes to this characteristic.

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_write

    @property
    def on_read(self) -> Event[GattsCharacteristic, None]:
        """
        Event generated whenever a client requests to read from this characteristic. At this point, the application
        may choose to update the value of the characteristic to a new value using set_value.

        A good example of this is a "system time" characteristic which reports the applications system time in seconds.
        Instead of updating this characteristic every second, it can be "lazily" updated only when read from.

        NOTE: if there are multiple handlers subscribed to this and each set the value differently, it may cause
        undefined behavior.

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_read

    @property
    def on_subscription_change(self) -> Event[GattsCharacteristic, SubscriptionStateChangeEventArgs]:
        """
        Event that is generated whenever a client changes its subscription state of the characteristic
        (notify, indicate, none).

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_sub_change

    @property
    def on_notify_complete(self) -> Event[GattsCharacteristic, NotificationCompleteEventArgs]:
        """
        Event that is generated when a notification or indication sent to the client successfully

        :return: an event which can have handlers registered to and deregistered from
        """
        return self._on_notify_complete

    """
    Event Handling
    """

    def _on_cccd_write(self, sender, event_args):
        self.cccd_state = gatt.SubscriptionState.from_buffer(bytearray(event_args.value))
        self._on_sub_change.notify(self, SubscriptionStateChangeEventArgs(self.cccd_state))

    def _on_value_write(self, sender, event_args):
        self._on_write.notify(self, event_args)

    def _on_value_read(self, sender, event_args):
        self._on_read.notify(self, event_args)

    def _on_disconnect(self, peer, event_args):
        if self._cccd_attr and self.cccd_state != gatt.SubscriptionState.NOT_SUBSCRIBED:
            self.cccd_state = gatt.SubscriptionState.NOT_SUBSCRIBED


class GattsService(gatt.Service):
    """
    Represents a registered GATT service that lives locally on the device.

    This class is usually not instantiated directly and is instead created through :meth:`GattsDatabase.add_service`.
    """
    def __init__(self, ble_device: BleDevice,
                 peer: Peer,
                 uuid: Uuid,
                 service_type: int,
                 notification_manager: GattsOperationManager,
                 start_handle=gatt.BLE_GATT_HANDLE_INVALID, end_handle=gatt.BLE_GATT_HANDLE_INVALID):
        super(GattsService, self).__init__(ble_device, peer, uuid, service_type, start_handle, end_handle)
        self._notification_manager = notification_manager

    @property
    def characteristics(self) -> List[GattsCharacteristic]:
        """
        **Read Only**

        Gets the list of characteristics in this service.

        Characteristics are added through :meth:`add_characteristic`
        """
        return self._characteristics

    def add_characteristic(self, uuid: Uuid, properties: GattsCharacteristicProperties,
                           initial_value=b"", prefer_indications=True, string_encoding="utf8"):
        """
        Adds a new characteristic to the service

        :param uuid: The UUID of the characteristic to add
        :param properties: The characteristic's properties
        :param initial_value: The initial value of the characteristic. May be a string, bytearray, or list of ints
        :type initial_value: str or list or bytearray
        :param prefer_indications: Flag for choosing indication/notification if a characteristic has
                                   both indications and notifications available
        :param string_encoding: The encoding method to use when a string value is provided (utf8, ascii, etc.)
        :return: The characteristic just added to the service
        :rtype: GattsCharacteristic
        """
        if isinstance(initial_value, str):
            initial_value = initial_value.encode(string_encoding)
        # Register UUID
        self.ble_device.uuid_manager.register_uuid(uuid)

        # Create property structure
        props = nrf_types.BLEGattCharacteristicProperties(
            broadcast=properties.broadcast,
            read=properties.read,
            write_wo_resp=properties.write_no_response,
            write=properties.write,
            notify=properties.notify,
            indicate=properties.indicate,
            auth_signed_wr=False
        )

        char_md = nrf_types.BLEGattsCharMetadata(props)
        # Create cccd metadata if notify/indicate enabled
        if properties.notify or properties.indicate:
            char_md.cccd_metadata = nrf_types.BLEGattsAttrMetadata(write_permissions=_security_mapping[properties.cccd_write_security_level])

        if properties.sccd:
            char_md.sccd_metadata = nrf_types.BLEGattsAttrMetadata()

        if properties.presentation:
            pf = nrf_types.BLEGattsPresentationFormat(properties.presentation.format, properties.presentation.exponent,
                                                      properties.presentation.unit, properties.presentation.namespace,
                                                      properties.presentation.description)
            char_md.presentation_format = pf

        if properties.user_description:
            user_desc = properties.user_description
            user_desc_sec = _security_mapping[user_desc.security_level]
            user_desc_sec_w = user_desc_sec if user_desc.write else nrf_types.BLEGapSecModeType.NO_ACCESS
            char_md.user_desc_metadata = nrf_types.BLEGattsAttrMetadata(user_desc_sec, user_desc_sec_w,
                                                                        user_desc.variable_length,
                                                                        user_desc.read_auth, user_desc.write_auth)
            char_md.user_description = user_desc.value
            char_md.user_description_max_len = user_desc.max_len
            char_md.extended_props.writable_aux = user_desc.write

        security = _security_mapping[properties.security_level]
        attr_metadata = nrf_types.BLEGattsAttrMetadata(security, security, properties.variable_length,
                                                       read_auth=True, write_auth=True)
        attribute = nrf_types.BLEGattsAttribute(uuid.nrf_uuid, attr_metadata, properties.max_len, initial_value)

        handles = nrf_types.BLEGattsCharHandles()  # Populated in call
        self.ble_device.ble_driver.ble_gatts_characteristic_add(self.start_handle, char_md, attribute, handles)

        c = GattsCharacteristic(self.ble_device, self.peer, uuid, properties,
                                handles.value_handle, handles.cccd_handle, handles.sccd_handle, handles.user_desc_handle,
                                self._notification_manager, initial_value, prefer_indications, string_encoding)

        self.characteristics.append(c)
        return c


class GattsDatabase(gatt.GattDatabase):
    """
    Represents the entire GATT server that lives locally on the device which clients read from and write to
    """
    def __init__(self, ble_device, peer, notification_hardware_queue_size=1):
        super(GattsDatabase, self).__init__(ble_device, peer)
        self.ble_device.ble_driver.event_subscribe(self._on_rw_auth_request,
                                                   nrf_events.GattsEvtReadWriteAuthorizeRequest)
        self._notification_manager = GattsOperationManager(ble_device, peer, notification_hardware_queue_size)

    @property
    def services(self) -> List[GattsService]:
        """
        **Read Only**

        The list of services registered in the database
        """
        return self._services

    def iter_services(self) -> Iterable[GattsService]:
        """
        Iterates through all of the registered services in the database

        :return: Generator of the database's services
        """
        for s in self.services:
            yield s

    def add_service(self, uuid: Uuid, service_type=gatt.ServiceType.PRIMARY) -> GattsService:
        """
        Adds a service to the local database

        :param uuid: The UUID for the service
        :param service_type: The type of service (primary or secondary)
        :return: The added and newly created service
        """
        # Register UUID
        self.ble_device.uuid_manager.register_uuid(uuid)
        handle = nrf_types.BleGattHandle()
        # Call code to add service to driver
        self.ble_device.ble_driver.ble_gatts_service_add(service_type.value, uuid.nrf_uuid, handle)
        service = GattsService(self.ble_device, self.peer, uuid, service_type, self._notification_manager, handle.handle)
        service.start_handle = handle.handle
        service.end_handle = 0xFFFF
        if self.services:
            self.services[-1].end_handle = service.start_handle-1
        self.services.append(service)
        return service

    def clear_pending_notifications(self):
        """
        Clears all pending notifications that are queued to be sent to the client
        """
        self._notification_manager.clear_all()

    def _on_rw_auth_request(self, driver, event):
        """
        :type event: nrf_events.GattsEvtReadWriteAuthorizeRequest
        """
        if not event.write:
            return
        # execute writes can span multiple services and characteristics. Should only reply at the top-level here
        if event.write.write_op not in [nrf_events.BLEGattsWriteOperation.exec_write_req_now,
                                        nrf_events.BLEGattsWriteOperation.exec_write_req_cancel]:
            return
        params = nrf_types.BLEGattsAuthorizeParams(nrf_types.BLEGattStatusCode.success, False)
        reply = nrf_types.BLEGattsRwAuthorizeReplyParams(write=params)
        self.ble_device.ble_driver.ble_gatts_rw_authorize_reply(event.conn_handle, reply)
