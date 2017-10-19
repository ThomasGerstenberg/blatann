import re
from blatann.nrf.nrf_types import BLEUUID as _BLEUUID


class Uuid(object):
    def __init__(self, nrf_uuid=None):
        self.nrf_uuid = nrf_uuid

    def __eq__(self, other):
        return str(self) == str(other)


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
        elif isinstance(uuid16, Uuid16):
            uuid16 = uuid16.uuid
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
        if isinstance(uuid, str):
            uuid = int(uuid, 16)
        if not isinstance(uuid, (int, long)) or uuid > 0xFFFF:
            raise ValueError("UUID Must be a valid 16-bit integer")
        super(Uuid16, self).__init__(_BLEUUID(uuid))
        self.uuid = uuid

    def __str__(self):
        return "{:x}".format(self.uuid)
