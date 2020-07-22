import typing

if typing.TYPE_CHECKING:
    from blatann.peer import PeerAddress


class BondingData(object):
    def __init__(self, bonding_keyset):
        """
        :type bonding_keyset: blatann.nrf.nrf_types.smp.BLEGapSecKeyset
        """
        self.own_ltk = bonding_keyset.own_keys.enc_key
        self.peer_ltk = bonding_keyset.peer_keys.enc_key
        self.peer_id = bonding_keyset.peer_keys.id_key
        self.peer_sign = bonding_keyset.peer_keys.sign_key


class BondDbEntry(object):
    def __init__(self, entry_id=0):
        self.id = entry_id
        self.peer_addr: PeerAddress = None
        self.peer_is_client: bool = False
        self.bonding_data: BondingData = None
        self.name = ""


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

    def __iter__(self):
        """
        :rtype: list[BondDbEntry]
        """
        raise NotImplementedError()


class BondDatabaseLoader(object):
    def load(self):
        """
        :rtype: BondDatabase
        """
        raise NotImplementedError()
