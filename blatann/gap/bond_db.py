from __future__ import annotations
import typing
import logging

from blatann.gap import smp_crypto
from blatann.nrf.nrf_types import (
    BLEGapAddr, BLEGapAddrTypes, BLEGapEncryptKey, BLEGapIdKey, BLEGapSignKey, BLEGapSecKeyset, BLEGapMasterId
)

if typing.TYPE_CHECKING:
    from blatann.gap.gap_types import PeerAddress


logger = logging.getLogger(__name__)


class BondingData(object):
    def __init__(self, own_ltk: BLEGapEncryptKey, peer_ltk: BLEGapEncryptKey,
                 peer_id: BLEGapIdKey, peer_sign: BLEGapSignKey):
        self.own_ltk = own_ltk
        self.peer_ltk = peer_ltk
        self.peer_id = peer_id
        self.peer_sign = peer_sign

    @classmethod
    def from_keyset(cls, bonding_keyset: BLEGapSecKeyset):
        return cls(
            bonding_keyset.own_keys.enc_key,
            bonding_keyset.peer_keys.enc_key,
            bonding_keyset.peer_keys.id_key,
            bonding_keyset.peer_keys.sign_key
        )

    def to_dict(self):
        return {
            "own_ltk": self.own_ltk.to_dict(),
            "peer_ltk": self.peer_ltk.to_dict(),
            "peer_id": self.peer_id.to_dict(),
            "peer_sign": self.peer_sign.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        own_ltk = BLEGapEncryptKey.from_dict(data["own_ltk"])
        peer_ltk = BLEGapEncryptKey.from_dict(data["peer_ltk"])
        peer_id = BLEGapIdKey.from_dict(data["peer_id"])
        peer_sign = BLEGapSignKey.from_dict(data["peer_sign"])
        return cls(own_ltk, peer_ltk, peer_id, peer_sign)


class BondDbEntry(object):
    def __init__(self, entry_id=0):
        self.id = entry_id
        self.own_addr: PeerAddress = None
        self.peer_addr: PeerAddress = None
        self.peer_is_client: bool = False
        self.bonding_data: BondingData = None
        self.name = ""

    def resolved_peer_address(self) -> PeerAddress:
        return self.bonding_data.peer_id.peer_addr

    def matches_peer(self, own_address: PeerAddress,
                     peer_address: PeerAddress,
                     peer_is_client: bool,
                     master_id: BLEGapMasterId = None) -> bool:
        # Wrong role
        if peer_is_client != self.peer_is_client:
            return False
        # Entry has own address and doesn't match.
        if (self.own_addr is not None and
                own_address is not None and
                self.own_addr != own_address):
            return False

        if self.peer_address_matches_or_resolves(peer_address):
            # If the bonding data is LESC, always return it.
            # Otherwise, if a master ID is provided to match against, it should be used
            if self.bonding_data.own_ltk.enc_info.lesc or not master_id:
                return True

        # Check master IDs
        if master_id:
            if self.bonding_data.own_ltk.master_id == master_id:
                logger.debug("Found matching record with own master ID")
                return True
            if self.bonding_data.peer_ltk.master_id == master_id:
                logger.debug("Found matching record with peer master ID")
                return True
        return False

    def peer_address_matches_or_resolves(self, peer_address: PeerAddress) -> bool:
        # Unresolvable, cannot match
        if peer_address.addr_type == BLEGapAddrTypes.random_private_non_resolvable:
            return False

        # If peer address is public or random static, check directly if they match (no IRK needed)
        if peer_address.addr_type in [BLEGapAddrTypes.random_static, BLEGapAddrTypes.public]:
            if self.peer_addr == peer_address:
                return True
        elif smp_crypto.private_address_resolves(peer_address, self.bonding_data.peer_id.irk):
            logger.debug("Resolved Peer address to {}".format(self.peer_addr))
            return True
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "own_addr": str(self.own_addr) if self.own_addr else None,
            "name": self.name,
            "peer_addr": str(self.peer_addr),
            "peer_is_client": self.peer_is_client,
            "bonding_data": self.bonding_data.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        entry = cls(data["id"])
        own_addr = data["own_addr"]
        entry.own_addr = BLEGapAddr.from_string(own_addr) if own_addr else None
        entry.peer_addr = BLEGapAddr.from_string(data["peer_addr"])
        entry.peer_is_client = data["peer_is_client"]
        entry.bonding_data = BondingData.from_dict(data["bonding_data"])
        return entry


class BondDatabase(object):
    def create(self) -> BondDbEntry:
        raise NotImplementedError()

    def add(self, db_entry: BondDbEntry):
        raise NotImplementedError()

    def update(self, db_entry: BondDbEntry):
        raise NotImplementedError()

    def delete(self, db_entry: BondDbEntry):
        raise NotImplementedError()

    def delete_all(self):
        raise NotImplementedError()

    def find_entry(self, own_address: PeerAddress,
                   peer_address: PeerAddress,
                   peer_is_client: bool,
                   master_id: BLEGapMasterId = None):
        raise NotImplementedError()

    def __iter__(self) -> typing.Collection[BondDbEntry]:
        raise NotImplementedError()


class BondDatabaseLoader(object):
    def load(self) -> BondDatabase:
        raise NotImplementedError()

    def save(self, db: BondDatabase):
        raise NotImplementedError()
