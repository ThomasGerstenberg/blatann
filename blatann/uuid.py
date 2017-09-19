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
            return
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
        else:
            raise ValueError("uuid must be a 16-bit or 128-bit UUID")


class Uuid128(object):
    def __init__(self, uuid):
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

    def __str__(self):
        return self.uuid_str


class Uuid16(object):
    def __init__(self, uuid):
        if not isinstance(uuid, int) or uuid > 0xFFFF:
            raise ValueError("UUID Must be a valid 16-bit integer")
        self.uuid = uuid
        self.nrf_uuid = BLEUUID(uuid)

    def __str__(self):
        return "{:x}".format(self.uuid)


if __name__ == '__main__':
    u = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
    u2 = Uuid128([0xde, 0xad, 0xbe, 0xef, 0x00, 0x11, 0x23, 0x45, 0x66, 0x79, 0xab, 0x12, 0xcc, 0xd4, 0xf5, 0x50])
    pass