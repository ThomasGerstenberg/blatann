from __future__ import annotations
import os
import logging
import pickle
import json
import typing
from typing import List, Optional

import blatann
from blatann.gap.bond_db import BondDatabase, BondDbEntry, BondDatabaseLoader
from blatann.gap.gap_types import PeerAddress
from blatann.nrf.nrf_types import BLEGapMasterId

logger = logging.getLogger(__name__)


system_default_db_base_filename = os.path.join(os.path.dirname(blatann.__file__), ".user", "bonding_db")
user_default_db_base_filename = os.path.join(os.path.expanduser("~"), ".blatann", "bonding_db")
special_bond_db_filemap = {
    "user": user_default_db_base_filename,
    "system": system_default_db_base_filename
}


class DatabaseStrategy:
    """
    Abstract base class defining the methods and properties for serializing/deserializing bond databases
    into different formats
    """
    @property
    def file_extension(self) -> str:
        """
        The file extension that this strategy can serialize/deserialize
        """
        raise NotImplementedError

    def load(self, filename: str) -> DefaultBondDatabase:
        """
        Loads/deserializes a database file

        :param filename: Name of the file to deserialize
        :return: The loaded bond database
        """
        raise NotImplementedError

    def save(self, filename: str, db: DefaultBondDatabase):
        """
        Saves/serializes a database to a file

        :param filename: Filename to save the database to
        :param db: The database object serialize
        """
        raise NotImplementedError


class JsonDatabaseStrategy(DatabaseStrategy):
    """
    Strategy for serializing/deseriralizing bond databases in JSON format
    """
    @property
    def file_extension(self) -> str:
        return ".json"

    def load(self, filename) -> DefaultBondDatabase:
        with open(filename, "r") as f:
            data = json.load(f)
        records = [BondDbEntry.from_dict(e) for e in data["records"]]
        return DefaultBondDatabase(records)

    def save(self, filename: str, db: DefaultBondDatabase):
        data = {"records": [r.to_dict() for r in db]}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)


class PickleDatabaseStrategy(DatabaseStrategy):
    """
    Strategy for serializing/deserializing bond databases in pickle format
    """
    @property
    def file_extension(self) -> str:
        return ".pkl"

    def load(self, filename) -> DefaultBondDatabase:
        with open(filename, "rb") as f:
            db = pickle.load(f)
            # Check if records are old entries missing own_db. If so, add it in
            for record in db:
                if not hasattr(record, "own_addr"):
                    print("Adding own_addr")
                    record.own_addr = None
            return db

    def save(self, filename, db: DefaultBondDatabase):
        with open(filename, "wb") as f:
            pickle.dump(db, f)


database_strategies = [
    PickleDatabaseStrategy(),
    JsonDatabaseStrategy()
]
"""List of supported database strategies"""


database_strategies_by_extension: typing.Dict[str, DatabaseStrategy] = {
    s.file_extension: s for s in database_strategies
}
"""Mapping of database file extensions to their respective strategies"""


# TODO 04.16.2019: Replace pickling with something more secure
class DefaultBondDatabaseLoader(BondDatabaseLoader):
    def __init__(self, filename="user"):
        if filename in special_bond_db_filemap:
            base_filename = special_bond_db_filemap[filename]
            self.filename = self.migrate_to_json(base_filename)
        else:
            self.filename = filename
        self.strategy = None

    def _get_strategy(self):
        if self.strategy is None:
            file_ext = os.path.splitext(self.filename)[1]
            if file_ext not in database_strategies_by_extension:
                raise ValueError(f"Unsupported file type '{file_ext}'. "
                                 f"Supported extensions: {', '.join(database_strategies_by_extension.keys())}")
            self.strategy = database_strategies_by_extension[file_ext]
        return self.strategy

    def migrate_to_json(self, base_filename):
        pkl_file = base_filename + ".pkl"
        json_file = base_filename + ".json"
        # If the pickle file doesn't exist, it's either already been migrated to JSON
        # or never existed at all. Either way use JSON
        if not os.path.exists(pkl_file):
            return json_file

        migration_required = False
        if os.path.exists(json_file):
            if os.path.getmtime(pkl_file) > os.path.getmtime(json_file):
                logger.warning("Both pickle and json bond databases exist, pickle file is newer."
                               "The existing json bond database will be overwritten")
                migration_required = True
        else:
            migration_required = True
        # Pickle file exists. If JSON file does not exist, load the db using the pickler,
        # then save it out using the json
        if migration_required:
            migrate_bond_database(pkl_file, json_file)
        os.remove(pkl_file)
        return json_file

    def _create_dirs(self):
        dirname = os.path.dirname(self.filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def load(self) -> DefaultBondDatabase:
        if not os.path.exists(self.filename):
            return DefaultBondDatabase()

        strategy = self._get_strategy()
        try:
            db = strategy.load(self.filename)
            return db
        except Exception as e:
            logger.exception("Failed to load Bond DB '{}'".format(self.filename))
            return DefaultBondDatabase()

    def save(self, db: DefaultBondDatabase):
        strategy = self._get_strategy()
        self._create_dirs()
        logger.info(f"Saving bond database to {self.filename}")
        strategy.save(self.filename, db)


class DefaultBondDatabase(BondDatabase):
    def __init__(self, records: List[BondDbEntry] = None):
        self._records = records or []
        self.current_id = 0

    def __iter__(self):
        for r in self._records:
            yield r

    def create(self):
        db_entry = BondDbEntry(self.current_id)
        self.current_id += 1
        return db_entry

    def add(self, db_entry):
        if not isinstance(db_entry, BondDbEntry):
            raise ValueError(db_entry)
        # Verify there isn't already an entry with the same ID
        for r in self:
            if r.id == db_entry.id:
                raise ValueError("There already exists an entry with id {}".format(r.id))
        self._records.append(db_entry)

    def update(self, db_entry):
        if not isinstance(db_entry, BondDbEntry):
            raise ValueError(db_entry)
        # TODO

    def delete(self, db_entry):
        if not isinstance(db_entry, BondDbEntry):
            raise ValueError(db_entry)

        for i, entry in enumerate(self._records):
            if entry.id == db_entry.id:
                del self._records[i]
                return

    def delete_all(self):
        self._records = []

    def find_entry(self, own_address: PeerAddress,
                   peer_address: PeerAddress,
                   peer_is_client: bool,
                   master_id: BLEGapMasterId = None) -> Optional[BondDbEntry]:
        """
        Attempts to find a bond entry which satisfies the parameters provided

        :param own_address: The local device's BLE address
        :param peer_address: The peer's BLE address
        :param peer_is_client: Flag indicating the role of the peer.
                               True if the peer is a client/central, False if the peer is a server/peripheral
        :param master_id: If during a security info request, this is the Master ID provided by the peer to search for
        :return: The first entry that satisfies the above parameters, or None if no entry was found
        """
        for record in self._records:
            if record.matches_peer(own_address, peer_address, peer_is_client, master_id):
                return record

        return None


def migrate_bond_database(from_file: str, to_file: str):
    """
    Migrates a bond database file from one format to another.

    For supported extensions/formats, check ``database_strategies_by_extension.keys()``

    :param from_file: File to migrate from
    :param to_file: File to migrate to
    """
    from_ext = os.path.splitext(from_file)[1]
    to_ext = os.path.splitext(to_file)[1]
    supported_extensions = ", ".join(database_strategies_by_extension.keys())
    if from_ext not in database_strategies_by_extension:
        raise ValueError(f"Unsupported file extension '{from_ext}'. Supported extensions: {supported_extensions}")
    if to_ext not in database_strategies_by_extension:
        raise ValueError(f"Unsupported file_extension '{to_ext}'. Supported extensions: {supported_extensions}")
    load_strategy = database_strategies_by_extension[from_ext]
    save_strategy = database_strategies_by_extension[to_ext]
    logger.info(f"Migrating Bond DB '{from_file}' to '{to_file}'")
    db = load_strategy.load(from_file)
    save_strategy.save(to_file, db)
