from threading import RLock
from blatann.services.glucose.data_types import GlucoseMeasurement, GlucoseContext


class AbstractGlucoseDatabase(object):
    def first_record(self):
        raise NotImplementedError()

    def last_record(self):
        raise NotImplementedError()

    def record_count(self, min_seq_num=None, max_seq_num=None):
        raise NotImplementedError()

    def get_records(self, min_seq_num=None, max_seq_num=None):
        """
        :param min_seq_num:
        :param max_seq_num:
        :rtype: list of GlucoseMeasurement
        """
        raise NotImplementedError()

    def delete_records(self, min_seq_num=None, max_seq_num=None):
        raise NotImplementedError()


class BasicGlucoseDatabase(AbstractGlucoseDatabase):
    def __init__(self, init_records=None):
        self._records = []  # type: list[GlucoseMeasurement]
        if init_records is not None:
            self._records = init_records
        self._lock = RLock()

    def _sort(self):
        with self._lock:
            self._records = sorted(self._records, key=lambda r: r.sequence_number)

    def _get_records_in_range(self, min_seq_num, max_seq_num):
        with self._lock:
            records = self._records[:]

        if min_seq_num is not None:
            records = filter(lambda r: r.sequence_number >= min_seq_num, records)
        if max_seq_num is not None:
            records = filter(lambda r: r.sequence_number <= max_seq_num, records)
        return records

    def delete_records(self, min_seq_num=None, max_seq_num=None):
        with self._lock:
            records = self._get_records_in_range(min_seq_num, max_seq_num)
            for r in records:
                self._records.remove(r)

    def record_count(self, min_seq_num=None, max_seq_num=None):
        return len(self._get_records_in_range(min_seq_num, max_seq_num))

    def get_records(self, min_seq_num=None, max_seq_num=None):
        records = self._get_records_in_range(min_seq_num, max_seq_num)
        return records

    def first_record(self):
        with self._lock:
            if self._records:
                return self._records[0]

    def last_record(self):
        with self._lock:
            if self._records:
                return self._records[-1]

    def add_record(self, glucose_measurement):
        """
        :type glucose_measurement: GlucoseMeasurement
        """
        with self._lock:
            if glucose_measurement.sequence_number in [r.sequence_number for r in self._records]:
                raise ValueError("Database already contains a measurement with sequence number {}".format(glucose_measurement.sequence_number))
            self._records.append(glucose_measurement)
        self._sort()

