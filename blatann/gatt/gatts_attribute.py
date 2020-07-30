from __future__ import annotations

import typing
import binascii
import logging
from collections import namedtuple

from blatann.exceptions import InvalidOperationException
from blatann.gatt import Attribute
from blatann.services.ble_data_types import BleDataStream
from blatann.event_args import WriteEventArgs
from blatann.nrf import nrf_events, nrf_types
from blatann.event_type import EventSource, Event
from blatann import gatt
from blatann.uuid import Uuid

if typing.TYPE_CHECKING:
    from blatann.peer import Peer
    from blatann.device import BleDevice
    from blatann.gatt.gatts import GattsCharacteristic

logger = logging.getLogger(__name__)


class GattsAttributeProperties(object):
    def __init__(self, read=True, write=False, security_level=gatt.SecurityLevel.OPEN,
                 max_length=20, variable_length=True, read_auth=False, write_auth=False):
        self.read = read
        self.write = write
        self.security_level = security_level
        self.max_len = max_length
        self.variable_length = variable_length
        self.read_auth = read_auth
        self.write_auth = write_auth


class GattsAttribute(Attribute):
    """
    Represents the server-side interface of a single attribute which lives inside a Characteristic.
    """
    _QueuedChunk = namedtuple("QueuedChunk", ["offset", "data"])

    def __init__(self, ble_device: BleDevice, peer: Peer, parent: GattsCharacteristic,
                 uuid: Uuid, handle: int, properties: GattsAttributeProperties,
                 initial_value=b"", string_encoding="utf8"):
        super(GattsAttribute, self).__init__(uuid, handle, initial_value, string_encoding)
        self._ble_device = ble_device
        self._peer = peer
        self._parent = parent
        self._properties = properties
        # Events
        self._on_write = EventSource("Write Event", logger)
        self._on_read = EventSource("Read Event", logger)
        # Subscribed events
        if properties.write:
            self._ble_device.ble_driver.event_subscribe(self._on_gatts_write, nrf_events.GattsEvtWrite)
        if properties.read_auth or properties.write_auth:
            self._ble_device.ble_driver.event_subscribe(self._on_rw_auth_request,
                                                        nrf_events.GattsEvtReadWriteAuthorizeRequest)
        # Internal state tracking stuff
        self._write_queued = False
        self._read_in_process = False
        self._queued_write_chunks = []

    @property
    def parent(self) -> GattsCharacteristic:
        """
        **Read Only**

        Gets the parent characteristic which owns this attribute
        """
        return self._parent

    @property
    def max_length(self) -> int:
        """
        **Read Only**

        The max possible length data the attribute can be set to
        """
        return self._properties.max_len

    @property
    def read_in_process(self) -> bool:
        """
        **Read Only**

        Gets whether or not the client is in the process of reading out this attribute
        """
        return self._read_in_process

    """
    Public Methods
    """

    def set_value(self, value):
        """
        Sets the value of the attribute.

        :param value: The value to set to. Must be an iterable type such as a str, bytes, or list of uint8 values, or a BleDataStream object.
                      Length must be less than the attribute's max length.
                      If a str is given, it will be encoded using the string_encoding property.
        :raises: InvalidOperationException if value length is too long
        """
        if isinstance(value, BleDataStream):
            value = value.value
        if isinstance(value, str):
            value = value.encode(self.string_encoding)
        if len(value) > self.max_length:
            raise InvalidOperationException("Attempted to set value of {} with length greater than max "
                                            "(got {}, max {})".format(self.uuid, len(value), self.max_length))

        v = nrf_types.BLEGattsValue(value)
        self._ble_device.ble_driver.ble_gatts_value_set(self._peer.conn_handle, self._handle, v)
        self._value = value

    def get_value(self) -> bytes:
        """
        Fetches the attribute's value from hardware and updates the local copy.
        This isn't often necessary and should instead use the value property to avoid unnecessary reads from the hardware.
        """
        v = nrf_types.BLEGattsValue(b"")
        self._ble_device.ble_driver.ble_gatts_value_get(self._peer.conn_handle, self._handle, v)
        self._value = bytes(bytearray(v.value))
        return self._value

    """
    Events
    """

    @property
    def on_write(self) -> Event[GattsAttribute, WriteEventArgs]:
        """
        Event generated whenever a client writes to this attribute.

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_write

    @property
    def on_read(self) -> Event[GattsAttribute, None]:
        """
        Event generated whenever a client requests to read from this attribute. At this point, the application
        may choose to update the value of the attribute to a new value using set_value.

        .. note:: This will only be triggered if the attribute was configured with the read_auth property

        A good example of using this is a "system time" characteristic which reports the application's current system time in seconds.
        Instead of updating this characteristic every second, it can be "lazily" updated only when read.

        NOTE: if there are multiple handlers subscribed to this and each set the value differently, it may cause
        undefined behavior.

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_read

    """
    Event Handlers
    """

    def _on_gatts_write(self, driver, event):
        """
        :type event: nrf_events.GattsEvtWrite
        """
        if event.attribute_handle != self._handle:
            return
        self._value = bytes(bytearray(event.data))
        self._on_write.notify(self, WriteEventArgs(self._value))

    def _on_write_auth_request(self, write_event):
        """
        :type write_event: nrf_events.GattsEvtWrite
        """
        if write_event.write_op in [nrf_events.BLEGattsWriteOperation.exec_write_req_cancel,
                                    nrf_events.BLEGattsWriteOperation.exec_write_req_now]:
            self._execute_queued_write(write_event.write_op)
            # Reply should already be handled in database since this can span multiple attributes and services
            return

        if write_event.attribute_handle != self._handle:
            # Handle is not for this attribute, do nothing
            return

        # Build out the reply
        params = nrf_types.BLEGattsAuthorizeParams(nrf_types.BLEGattStatusCode.success, True,
                                                   write_event.offset, write_event.data)
        reply = nrf_types.BLEGattsRwAuthorizeReplyParams(write=params)

        # Check that the write length is valid
        if write_event.offset + len(write_event.data) > self._properties.max_len:
            params.gatt_status = nrf_types.BLEGattStatusCode.invalid_att_val_length
            self._ble_device.ble_driver.ble_gatts_rw_authorize_reply(write_event.conn_handle, reply)
        else:
            # Send reply before processing write, in case user sets data in gatts_write handler
            try:
                self._ble_device.ble_driver.ble_gatts_rw_authorize_reply(write_event.conn_handle, reply)
            except Exception as e:
                pass
            if write_event.write_op == nrf_events.BLEGattsWriteOperation.prep_write_req:
                self._write_queued = True
                self._queued_write_chunks.append(self._QueuedChunk(write_event.offset, write_event.data))
            elif write_event.write_op in [nrf_events.BLEGattsWriteOperation.write_req,
                                          nrf_types.BLEGattsWriteOperation.write_cmd]:
                self._on_gatts_write(None, write_event)

        # TODO More logic

    def _on_read_auth_request(self, read_event):
        """
        :type read_event: nrf_events.GattsEvtRead
        """
        if read_event.attribute_handle != self._handle:
            # Don't care about handles outside of this attribute
            return

        params = nrf_types.BLEGattsAuthorizeParams(nrf_types.BLEGattStatusCode.success, False, read_event.offset)
        reply = nrf_types.BLEGattsRwAuthorizeReplyParams(read=params)
        if read_event.offset > len(self._value):
            params.gatt_status = nrf_types.BLEGattStatusCode.invalid_offset
        else:
            self._read_in_process = True
            # If the client is reading from the beginning, notify handlers in case an update needs to be made
            if read_event.offset == 0:
                self._on_read.notify(self)
            self._read_in_process = False

        self._ble_device.ble_driver.ble_gatts_rw_authorize_reply(read_event.conn_handle, reply)

    def _on_rw_auth_request(self, driver, event):
        if not self._peer:
            logger.warning("Got RW request when peer not connected: {}".format(event.conn_handle))
            return
        if event.read:
            self._on_read_auth_request(event.read)
        elif event.write:
            self._on_write_auth_request(event.write)
        else:
            logging.error("auth request was not read or write???")

    def _execute_queued_write(self, write_op):
        if not self._write_queued:
            return

        self._write_queued = False
        if write_op == nrf_events.BLEGattsWriteOperation.exec_write_req_cancel:
            logger.info("Cancelling write request, char: {}".format(self._uuid))
        else:
            logger.info("Executing write request, char: {}".format(self._uuid))
            # TODO Assume that it was assembled properly. Error handling should go here
            new_value = bytearray()
            for chunk in self._queued_write_chunks:
                new_value += bytearray(chunk.data)
            logger.debug("New value: 0x{}".format(binascii.hexlify(new_value)))
            self._ble_device.ble_driver.ble_gatts_value_set(self._peer.conn_handle, self._handle,
                                                            nrf_types.BLEGattsValue(new_value))
            self._value = bytes(new_value)
            self._on_write.notify(self, WriteEventArgs(self._value))
        self._queued_write_chunks = []
