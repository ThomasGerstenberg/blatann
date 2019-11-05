from enum import Enum
import logging
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util

logger = logging.getLogger(__name__)

BLE_CONN_HANDLE_INVALID = driver.BLE_CONN_HANDLE_INVALID

NoneType = type(None)


class BLEUUIDBase(object):
    BLE_UUID_TYPE_BLE = driver.BLE_UUID_TYPE_BLE

    def __init__(self, vs_uuid_base=None, uuid_type=None):
        assert isinstance(vs_uuid_base, (list, NoneType)), 'Invalid argument type'
        assert isinstance(uuid_type, (int, NoneType)), 'Invalid argument type'
        if vs_uuid_base is None:
            self.base = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00,
                         0x80, 0x00, 0x00, 0x80, 0x5F, 0x9B, 0x34, 0xFB]
            self.def_base = True
        else:
            self.base = vs_uuid_base
            self.def_base = False

        if uuid_type is None and self.def_base:
            self.type = driver.BLE_UUID_TYPE_BLE
        else:
            self.type = uuid_type if uuid_type is not None else 0

    def __eq__(self, other):
        if not isinstance(other, BLEUUIDBase):
            return False
        if self.base != other.base:
            return False
        if self.type != other.type:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_c(cls, uuid):
        if uuid.type == driver.BLE_UUID_TYPE_BLE:
            return cls(uuid_type=uuid.type)
        else:
            return cls([0] * 16, uuid_type=uuid.type)  # TODO: Hmmmm? [] or [None]*16? what?

    @classmethod
    def from_uuid128_array(cls, uuid128_array):
        msb_list = uuid128_array[::-1]
        return cls(msb_list)

    def to_c(self):
        lsb_list = self.base[::-1]
        self.__array = util.list_to_uint8_array(lsb_list)
        uuid = driver.ble_uuid128_t()
        uuid.uuid128 = self.__array.cast()
        return uuid


class BLEUUID(object):
    class Standard(Enum):
        unknown = 0x0000
        service_primary = 0x2800
        service_secondary = 0x2801
        characteristic = 0x2803
        cccd = 0x2902
        battery_level = 0x2A19
        heart_rate = 0x2A37

    def __init__(self, value, base=BLEUUIDBase()):
        assert isinstance(base, BLEUUIDBase), 'Invalid argument type'
        self.base = base
        if self.base.def_base:
            try:
                self.value = value if isinstance(value, BLEUUID.Standard) else BLEUUID.Standard(value)
            except ValueError:
                self.value = value
        else:
            self.value = value

    def get_value(self):
        if isinstance(self.value, BLEUUID.Standard):
            return self.value.value
        return self.value

    def as_array(self):
        base_and_value = self.base.base[:]
        base_and_value[2] = (self.get_value() >> 8) & 0xff
        base_and_value[3] = (self.get_value() >> 0) & 0xff
        return base_and_value

    def __str__(self):
        if isinstance(self.value, BLEUUID.Standard):
            return '0x{:04X} ({})'.format(self.value.value, self.value)
        elif self.base.type == driver.BLE_UUID_TYPE_BLE and self.base.def_base:
            return '0x{:04X}'.format(self.value)
        else:
            base_and_value = self.base.base[:]
            base_and_value[2] = (self.value >> 8) & 0xff
            base_and_value[3] = (self.value >> 0) & 0xff
            return '0x{}'.format(''.join(['{:02X}'.format(i) for i in base_and_value]))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, BLEUUID.Standard):
            return self.get_value() == other.value
        if not isinstance(other, BLEUUID):
            return False
        if not self.base == other.base:
            return False
        if not self.value == other.value:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def from_c(cls, uuid):
        return cls(value=uuid.uuid, base=BLEUUIDBase.from_c(uuid))  # TODO: Is this correct?

    @classmethod
    def from_uuid128(cls, uuid128):
        uuid = util.uint8_array_to_list(uuid128.uuid, 16)
        return cls.from_array(uuid)

    def to_c(self):
        assert self.base.type is not None, 'Vendor specific UUID not registered'
        uuid = driver.ble_uuid_t()
        if isinstance(self.value, BLEUUID.Standard):
            uuid.uuid = self.value.value
        else:
            uuid.uuid = self.value
        uuid.type = self.base.type
        return uuid

    @classmethod
    def from_array(cls, uuid_array_lt):
        base = list(reversed(uuid_array_lt))
        uuid = (base[2] << 8) + base[3]
        base[2] = 0
        base[3] = 0
        return cls(value=uuid, base=BLEUUIDBase(base, 0))
