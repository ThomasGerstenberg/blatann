import enum

INVALID_HANDLE = 0x0000


class SecurityLevel(enum.Enum):
    NO_ACCESS = 0
    OPEN = 1
    JUST_WORKS = 2
    MITM = 3


class ServiceType(enum.Enum):
    PRIMARY = 1
    SECONDARY = 2


class CharacteristicProperties(object):
    def __init__(self, read=True, write=False, notify=False, indicate=False, broadcast=False,
                 security_level=SecurityLevel.OPEN, max_length=20, variable_length=True, prefer_indications=True):
        self.read = read
        self.write = write
        self.notify = notify
        self.indicate = indicate
        self.broadcast = broadcast
        self.security_level = security_level
        self.max_len = max_length
        self.variable_length = variable_length
        self.prefer_indications = prefer_indications


class CharacteristicDescriptor(object):
    class Type(enum.Enum):
        EXTENDED_PROPERTY = 0x2900
        USER_DESCRIPTION = 0x2901
        CLIENT_CHAR_CONFIG = 0x2902
        SERVER_CHAR_CONFIG = 0x2903
        PRESENTATION_FORMAT = 0x2904
        AGGREGATE_FORMAT = 0x2905

    def __init__(self, uuid, handle):
        self.uuid = uuid
        self.handle = handle


class Characteristic(object):
    def __init__(self, ble_device, peer, uuid):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self.uuid = uuid
        self.declaration_handle = INVALID_HANDLE
        self.value_handle = INVALID_HANDLE
        self.cccd_handle = INVALID_HANDLE

class Service(object):
    def __init__(self, ble_device, peer, uuid, service_type, start_handle=INVALID_HANDLE, end_handle=INVALID_HANDLE):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self.uuid = uuid
        self.service_type = service_type
        self.characteristics = []
        self.start_handle = start_handle
        # If a valid starting handle is given and not a valid ending handle, then the ending handle
        # is the starting handle
        if start_handle != INVALID_HANDLE and end_handle == INVALID_HANDLE:
            end_handle = start_handle
        self.end_handle = end_handle


class GattDatabase(object):
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self.services = []
