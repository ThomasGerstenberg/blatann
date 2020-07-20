import os
import logging
import pickle
from typing import List

import blatann
from blatann.gap.bond_db import BondDatabase, BondDbEntry, BondDatabaseLoader


logger = logging.getLogger(__name__)


default_db_file = os.path.join(os.path.dirname(blatann.__file__), ".user", "bonding_db.pkl")


# TODO 04.16.2019: Replace pickling with something more secure
class DefaultBondDatabaseLoader(BondDatabaseLoader):
    def __init__(self, filename=default_db_file):
        self.filename = filename

    def load(self):
        if not os.path.exists(self.filename):
            return DefaultBondDatabase()
        try:
            with open(self.filename, "rb") as f:
                db = pickle.load(f)
                logger.info("Loaded Bond DB '{}'".format(self.filename))
                return db
        except Exception as e:
            logger.info("Failed to load Bond DB '{}' -  {}:{}".format(self.filename, type(e).__name__, e.message))
            return DefaultBondDatabase()

    def save(self, db):
        dirname = os.path.dirname(default_db_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.filename, "wb") as f:
            pickle.dump(db, f)


class DefaultBondDatabase(BondDatabase):
    def __init__(self):
        self._records: List[BondDbEntry] = []
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
