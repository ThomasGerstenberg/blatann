import re
from blatann.nrf.nrf_types import BLEUUIDBase, BLEUUID


class UuidManager(object):
    def __init__(self, ble_driver, max_vs_uuids=10):
        """

        :type ble_driver: pc_ble_driver_py.nrf_driver.NrfDriver
        """
        self.ble_driver = ble_driver
        self.registered_vs_uuids = []

    def register_uuid(self, uuid):
        if isinstance(uuid, Uuid16):
            return  # Don't need to register standard 16-bit UUIDs
        elif isinstance(uuid, Uuid128):
            # Check if the base is already registered. If so, do nothing
            for registered_base in self.registered_vs_uuids:
                if uuid.uuid_base == registered_base.base:
                    uuid.nrf_uuid = BLEUUID(uuid.uuid16, registered_base)
                    return
            # Not registered, create a base
            base = BLEUUIDBase(uuid.uuid_base)
            self.ble_driver.ble_vs_uuid_add(base)
            self.registered_vs_uuids.append(base)
            uuid.nrf_uuid = BLEUUID(uuid.uuid16, base)
        elif isinstance(uuid, BLEUUID):
            self.ble_driver.ble_vs_uuid_add(uuid.base)
            self.registered_vs_uuids.append(uuid.base)
        elif isinstance(uuid, BLEUUIDBase):
            self.ble_driver.ble_vs_uuid_add(uuid)
            self.registered_vs_uuids.append(uuid.base)
        else:
            raise ValueError("uuid must be a 16-bit or 128-bit UUID")

    def nrf_uuid_to_uuid(self, nrf_uuid):
        """
        :type nrf_uuid: BLEUUID
        :rtype: Uuid
        """
        if nrf_uuid.base.type == 0:
            raise ValueError("UUID Not registered: {}".format(nrf_uuid))
        if nrf_uuid.base.type == BLEUUIDBase.BLE_UUID_TYPE_BLE:
            return Uuid16(nrf_uuid.get_value())
        base = None
        for uuid_base in self.registered_vs_uuids:
            if nrf_uuid.base.type == uuid_base.type:
                base = uuid_base

        if base is None:
            raise ValueError("Unable to find registered 128-bit uuid: {}".format(nrf_uuid))
        return Uuid128.combine_with_base(nrf_uuid.value, base.base)


class Uuid(object):
    def __init__(self, nrf_uuid=None):
        self.nrf_uuid = nrf_uuid


class Uuid128(Uuid):
    def __init__(self, uuid):
        super(Uuid128, self).__init__()
        if isinstance(uuid, str):
            self.uuid_str = uuid.lower()
            self.uuid = self._validate_uuid_str(uuid)
        elif isinstance(uuid, list):
            self.uuid = uuid
            self.uuid_str = self._validate_uuid_list(uuid)
        else:
            raise ValueError("UUID Must be of string or list type")
        self.nrf_uuid = None

    def _validate_uuid_str(self, uuid):
        r = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        if not r.match(uuid):
            raise ValueError("Invalid UUID String. Must be in format of '00112233-aabb-ccdd-eeff-445566778899")
        return [ord(o) for o in uuid.replace("-", "").decode("hex")]

    def _validate_uuid_list(self, uuid):
        if len(uuid) != 16:
            raise ValueError("UUID Must be 16 bytes long")
        uuid = "".join(chr(u) for u in uuid).encode("hex")
        uuid_sections = uuid[:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32]

        return "{}-{}-{}-{}-{}".format(*uuid_sections)

    @property
    def uuid_base(self):
        uuid_base = self.uuid[:]
        uuid_base[2] = 0
        uuid_base[3] = 0
        return uuid_base

    @property
    def uuid16(self):
        return self.uuid[2] << 8 | self.uuid[3]

    def new_uuid_from_base(self, uuid16):
        if isinstance(uuid16, str):
            uuid16 = int(uuid16, 16)
        if not isinstance(uuid16, (int, long)) or uuid16 > 0xFFFF:
            raise ValueError("UUID must be specified as a 16-bit number (0 - 0xFFFF) or a 4 character hex-string")
        uuid = self.uuid_base
        uuid[2] = uuid16 >> 8 & 0xFF
        uuid[3] = uuid16 & 0xFF
        return Uuid128(uuid)

    @classmethod
    def combine_with_base(cls, uuid16, uuid128_base):
        uuid_base = Uuid128(uuid128_base)
        return uuid_base.new_uuid_from_base(uuid16)

    def __str__(self):
        return self.uuid_str


class Uuid16(Uuid):
    def __init__(self, uuid):
        if not isinstance(uuid, (int, long)) or uuid > 0xFFFF:
            raise ValueError("UUID Must be a valid 16-bit integer")
        super(Uuid16, self).__init__(BLEUUID(uuid))
        self.uuid = uuid

    def __str__(self):
        return "{:x}".format(self.uuid)


if __name__ == '__main__':
    u = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
    u2 = Uuid128([0xde, 0xad, 0xbe, 0xef, 0x00, 0x11, 0x23, 0x45, 0x66, 0x79, 0xab, 0x12, 0xcc, 0xd4, 0xf5, 0x50])
    pass
