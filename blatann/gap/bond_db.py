
class BondDatabase(object):
    def __init__(self, bond_records):
        self.bond_records = bond_records

    def fetch(self, params_tbd):
        raise NotImplementedError()

    def save(self, bond_data):
        raise NotImplementedError()


class BondDatabaseLoader(object):
    @classmethod
    def loads(cls, bond_data):
        pass

    @classmethod
    def load(cls, filename):
        pass