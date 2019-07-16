import enum
import logging
import struct
from blatann.nrf.nrf_types.gatt import BLE_GATT_HANDLE_INVALID
from blatann.nrf import nrf_types
from blatann.gap.smp import SecurityLevel


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

"""
Status codes that can be returned during GATT Operations (reads, writes, etc.)
"""
GattStatusCode = nrf_types.BLEGattStatusCode

"""
The two notification types (notification, indication) used when a characteristic is notified from a peripheral
"""
GattNotificationType = nrf_types.BLEGattHVXType


class ServiceType(enum.Enum):
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


class Characteristic(object):
    """
    Abstract class that represents a BLE characteristic (both remote and local)
    """
    def __init__(self, ble_device, peer, uuid, properties):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        :type uuid: blatann.uuid.Uuid
        :type properties: CharacteristicProperties
        """
        self.ble_device = ble_device
        self.peer = peer
        self.uuid = uuid
        self.declaration_handle = BLE_GATT_HANDLE_INVALID
        self.value_handle = BLE_GATT_HANDLE_INVALID
        self.cccd_handle = BLE_GATT_HANDLE_INVALID
        self.cccd_state = SubscriptionState.NOT_SUBSCRIBED
        self._properties = properties

    def __repr__(self):
        return "Characteristic({}, {}".format(self.uuid, self._properties)


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
        self.start_handle = start_handle
        # If a valid starting handle is given and not a valid ending handle, then the ending handle
        # is the starting handle
        if start_handle != BLE_GATT_HANDLE_INVALID and end_handle == BLE_GATT_HANDLE_INVALID:
            end_handle = start_handle
        self.end_handle = end_handle

    def __repr__(self):
        return "Service({}, characteristics: [{}])".format(self.uuid,
                                                           "\n    ".join(str(c) for c in self._characteristics))


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

