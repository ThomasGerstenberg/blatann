from __future__ import annotations
import re
import binascii
import secrets
from typing import List, Union

from blatann.nrf.nrf_types import BLEUUID as _BLEUUID


class Uuid(object):
    """
    Base class for UUIDs
    """
    def __init__(self, nrf_uuid=None, description=""):
        self.nrf_uuid = nrf_uuid
        self.description = description

    def __eq__(self, other):
        return str(self) == str(other)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        raise NotImplementedError()

    @property
    def descriptive_string(self) -> str:
        return f"{self.description} ({self})" if self.description else str(self)


class Uuid128(Uuid):
    """
    Represents a 128-bit UUID
    """
    def __init__(self, uuid: Union[str, bytes, List[int]], description=""):
        """
        :param uuid: The UUID to use.
                     If uuid is a string, must be in the format '00112233-aabb-ccdd-eeff-445566778899'.
                     If uuid is bytes, value should be 16 bytes long, big-endian format
                     if uuid is a list of integers, value should be 16 bytes long, all integer values must be <= 255, big-endian format
        :param description: Optional description to provide for the UUID
        """
        super(Uuid128, self).__init__(description=description)
        if isinstance(uuid, str):
            self.uuid_str = uuid.lower()
            self.uuid = self._validate_uuid_str(uuid)
        elif isinstance(uuid, list):
            self.uuid = uuid
            self.uuid_str = self._validate_uuid_list(uuid)
        elif isinstance(uuid, bytes):
            self.uuid = list(uuid)
            self.uuid_str = self._validate_uuid_list(uuid)
        else:
            raise ValueError("UUID Must be of string or list type")
        self.nrf_uuid = None

    def _validate_uuid_str(self, uuid):
        r = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        if not r.match(uuid):
            raise ValueError("Invalid UUID String. Must be in format of '00112233-aabb-ccdd-eeff-445566778899'")
        return binascii.unhexlify(uuid.replace("-", ""))

    def _validate_uuid_list(self, uuid):
        if len(uuid) != 16:
            raise ValueError("UUID Must be 16 bytes long")
        uuid = binascii.hexlify(bytes(uuid)).decode("ascii")
        uuid_sections = uuid[:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32]

        return "{}-{}-{}-{}-{}".format(*uuid_sections)

    @property
    def uuid_base(self) -> List[int]:
        """
        **Read Only**

        The base of the 128-bit UUID which can be used to create other UUIDs with the same base
        """
        uuid_base = list(self.uuid[:])
        uuid_base[2] = 0
        uuid_base[3] = 0
        return uuid_base

    @property
    def uuid16(self) -> int:
        """
        **Read Only**

        The 16-bit representation of the 128-bit UUID
        """
        return self.uuid[2] << 8 | self.uuid[3]

    def new_uuid_from_base(self, uuid16: Union[str, int, Uuid16]) -> Uuid128:
        """
        Creates a new 128-bit UUID with the same base as this UUID, replacing out the 16-bit individual identifier with the value provided

        :param uuid16: The new 16-bit UUID to append to the base. Should either be a 16-bit integer,
                       a hex string of the value (without the leading '0x'), or a Uuid16 object
        :return: The newly created UUID
        """
        if isinstance(uuid16, str):
            uuid16 = int(uuid16, 16)
        elif isinstance(uuid16, Uuid16):
            uuid16 = uuid16.uuid
        if not isinstance(uuid16, int) or uuid16 > 0xFFFF:
            raise ValueError("UUID must be specified as a 16-bit number (0 - 0xFFFF) or a 4 character hex-string")
        uuid = self.uuid_base
        uuid[2] = uuid16 >> 8 & 0xFF
        uuid[3] = uuid16 & 0xFF
        return Uuid128(uuid)

    @classmethod
    def combine_with_base(cls,
                          uuid16: Union[str, int, Uuid16],
                          uuid128_base: Union[str, bytes, List[int]]) -> Uuid128:
        """
        Combines a 16-bit UUID with a 128-bit UUID base and returns the new UUID

        :param uuid16: The 16-bit UUID to use. See new_uuid_from_base for format.
        :param uuid128_base: The 128-bit base UUID to use. See __init__ for format.
        :return: The created UUID
        """
        uuid_base = Uuid128(uuid128_base)
        return uuid_base.new_uuid_from_base(uuid16)

    def __str__(self):
        return self.uuid_str

    def __hash__(self):
        return int.from_bytes(self.uuid, byteorder="big", signed=False)


class Uuid16(Uuid):
    """
    Represents a 16-bit "short form" UUID
    """
    def __init__(self, uuid: Union[str, int], description=""):
        """
        :param uuid: The UUID to use. Should either be a 16-bit integer value or a hex string of the value (without the leading '0x')
        :param description: Optional description to provide for the UUID
        """
        if isinstance(uuid, str):
            uuid = int(uuid, 16)
        if isinstance(uuid, _BLEUUID.Standard):
            uuid = uuid.value
        if not isinstance(uuid, int) or uuid > 0xFFFF:
            raise ValueError("UUID Must be a valid 16-bit integer")
        super(Uuid16, self).__init__(_BLEUUID(uuid), description)
        self.uuid = uuid

    def __str__(self):
        return "{:x}".format(self.uuid)

    def __hash__(self):
        return self.uuid


def generate_random_uuid16() -> Uuid16:
    """
    Generates a random 16-bit UUID

    :return: The generated 16-bit UUID
    """
    return Uuid16(secrets.randbits(16))


def generate_random_uuid128() -> Uuid128:
    """
    Generates a random 128-bit UUID

    :return: The generated 128-bit UUID
    """
    return Uuid128(list(secrets.randbits(128).to_bytes(16, "little")))
