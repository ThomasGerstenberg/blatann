

class AbstractGlucoseDatabase(object):
    def first_record(self):
        raise NotImplementedError()

    def last_record(self):
        raise NotImplementedError()

    def record_count(self, min_seq_num=None, max_seq_num=None):
        raise NotImplementedError()

    def get_records(self, min_seq_num=None, max_seq_num=None):
        raise NotImplementedError()

    def delete_records(self, min_seq_num=None, max_seq_num=None):
        raise NotImplementedError()
