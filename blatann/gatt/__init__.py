import enum
import logging
import struct

from blatann.services.ble_data_types import BleCompoundDataType, Uint8, Int8, Uint16
from blatann.uuid import Uuid
from blatann.nrf.nrf_types.gatt import BLE_GATT_HANDLE_INVALID
from blatann.nrf import nrf_types
from blatann.gap.smp import SecurityLevel
from blatann.bt_sig.assigned_numbers import Format, Units, Namespace, NamespaceDescriptor


logger = logging.getLogger(__name__)

"""
The default MTU size that's used when a connection is established
"""
MTU_SIZE_DEFAULT = 23

"""
The minimum allowed MTU size
"""
MTU_SIZE_MINIMUM = 23

"""
The ideal MTU size to use when using the maximum link-layer Data Length Extension setting (251) 
"""
MTU_SIZE_FOR_MAX_DLE = 247

# Overhead counts for different ATT processes
WRITE_BYTE_OVERHEAD = 3
LONG_WRITE_BYTE_OVERHEAD = 5
NOTIFICATION_BYTE_OVERHEAD = 3
READ_BYTE_OVERHEAD = 1

# Maximum value for data length
DLE_MAX = 251
DLE_MIN = 27
DLE_OVERHEAD = 4

"""
Status codes that can be returned during GATT Operations (reads, writes, etc.)
"""
GattStatusCode = nrf_types.BLEGattStatusCode

"""
The two notification types (notification, indication) used when a characteristic is notified from a peripheral
"""
GattNotificationType = nrf_types.BLEGattHVXType


class ServiceType(enum.IntEnum):
    PRIMARY = 1
    SECONDARY = 2


class SubscriptionState(enum.IntEnum):
    """
    Defines the different subscription states/types for a characteristic
    """
    NOT_SUBSCRIBED = 0
    NOTIFY = 1
    INDICATION = 2

    @classmethod
    def to_buffer(cls, value):
        """
        Converts to a little-endian uint16 buffer to be written over BLE
        """
        return struct.pack("<H", value)

    @classmethod
    def from_buffer(cls, buf):
        """
        Converts from a little-endian uint16 buffer received over BLE to the subscription state
        """
        return cls(struct.unpack("<H", buf)[0])


class CharacteristicProperties(object):
    def __init__(self, read=True, write=False, notify=False, indicate=False, broadcast=False,
                 write_no_response=False, signed_write=False):
        self.read = read
        self.write = write
        self.notify = notify
        self.indicate = indicate
        self.broadcast = broadcast
        self.write_no_response = write_no_response
        self.signed_write = signed_write

    @classmethod
    def from_nrf_properties(cls, nrf_props):
        """
        :meta private:
        :type nrf_props: blatann.nrf.nrf_types.BLEGattCharacteristicProperties
        """
        return CharacteristicProperties(nrf_props.read, nrf_props.write, nrf_props.notify, nrf_props.indicate,
                                        nrf_props.broadcast, nrf_props.write_wo_resp, nrf_props.auth_signed_wr)

    def __repr__(self):
        props = [
            [self.read, "r"],
            [self.write, "w"],
            [self.notify, "n"],
            [self.indicate, "i"],
            [self.broadcast, "b"],
            [self.write_no_response, "wn"],
            [self.signed_write, "sw"],
        ]
        props = [c for is_set, c in props if is_set]
        return "CharProps({})".format(",".join(props))


class Attribute(object):
    """
    Represents a single attribute which lives inside a Characteristic (both remote and local)
    """
    def __init__(self, uuid: Uuid, handle: int, value=b"", string_encoding="utf8"):
        self._uuid = uuid
        self._handle = handle
        self._value = value or b""
        self._string_encoding = string_encoding

    @property
    def uuid(self) -> Uuid:
        """
        The attribute's UUID
        """
        return self._uuid

    @property
    def handle(self) -> int:
        """
        The attribute's handle
        """
        return self._handle

    @property
    def value(self) -> bytes:
        """
        Gets the current value of the attribute
        """
        return self._value

    @property
    def string_encoding(self) -> str:
        """
        The default method for encoding strings into bytes when a string is provided as a value
        """
        return self._string_encoding

    @string_encoding.setter
    def string_encoding(self, value: str):
        """
        The default method for encoding strings into bytes when a string is provided as a value
        """
        self._string_encoding = value

    def __repr__(self):
        return f"Attribute({self._handle}): {self._uuid.descriptive_string}"


class Characteristic(object):
    """
    Abstract class that represents a BLE characteristic (both remote and local).
    """
    def __init__(self, ble_device, peer, uuid, properties,
                 attributes=None,
                 default_string_encoding="utf8"):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        :type uuid: blatann.uuid.Uuid
        """
        self.ble_device = ble_device
        self.peer = peer
        self.uuid = uuid
        self.cccd_state = SubscriptionState.NOT_SUBSCRIBED
        self._properties = properties
        self._string_encoding = default_string_encoding
        self._attributes = attributes or []

    def __repr__(self):
        newline = "\n" + " " * 8
        attr_str = newline.join(str(d) for d in self._attributes)
        if attr_str:
            attr_str = newline + attr_str + "\n    "
        return f"Characteristic: {self.uuid.descriptive_string}, {self._properties}, attributes: [{attr_str}]"


class Service(object):
    """
    Abstract class that represents a BLE Service (both remote and local)
    """
    def __init__(self, ble_device, peer, uuid, service_type,
                 start_handle=BLE_GATT_HANDLE_INVALID, end_handle=BLE_GATT_HANDLE_INVALID):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self.uuid = uuid
        self.service_type = service_type
        self._characteristics = []
        self._attributes = []
        self.start_handle = start_handle
        # If a valid starting handle is given and not a valid ending handle, then the ending handle
        # is the starting handle
        if start_handle != BLE_GATT_HANDLE_INVALID and end_handle == BLE_GATT_HANDLE_INVALID:
            end_handle = start_handle
        self.end_handle = end_handle

    def __repr__(self):
        newline = "\n" + " " * 4
        char_str = newline.join(str(c) for c in self._characteristics)
        if char_str:
            char_str = newline + char_str + "\n"
        return f"Service: {self.uuid.descriptive_string} [{self.start_handle}-{self.end_handle}], characteristics: [{char_str}]"


class GattDatabase(object):
    """
    Abstract class that represents a BLE Database (both remote and local)
    """
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self._services = []

    def __repr__(self):
        return "Database(peer {}, services: [{}])".format(self.peer.conn_handle,
                                                          "\n  ".join(str(s) for s in self._services))


class PresentationFormat(BleCompoundDataType):
    data_stream_types = [Uint8, Int8, Uint16, Uint8, Uint16]

    def __init__(self, fmt: int, exponent: int, unit: int, namespace: int = 0, description: int = 0):
        self.format = fmt
        self.exponent = exponent
        self.unit = unit
        self.namespace = namespace
        self.description = description

    def encode(self):
        return self.encode_values(self.format, self.exponent, self.unit, self.namespace, self.description)

    @classmethod
    def decode(cls, stream):
        fmt, exponent, unit, namespace, description = super(PresentationFormat, cls).decode(stream)
        fmt = cls.try_get_enum(fmt, Format)
        unit = cls.try_get_enum(unit, Units)
        namespace = cls.try_get_enum(namespace, Namespace)
        description = cls.try_get_enum(description, NamespaceDescriptor)
        return PresentationFormat(fmt, exponent, unit, namespace, description)

    @staticmethod
    def try_get_enum(value, enum_type):
        try:
            return enum_type(value)
        except ValueError:
            print("Failed")
            return value