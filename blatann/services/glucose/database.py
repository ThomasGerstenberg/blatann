import logging
from threading import RLock
from blatann.services.glucose.data_types import GlucoseMeasurement
from blatann.services.glucose.racp import RacpResponseCode


logger = logging.getLogger(__name__)


class IGlucoseDatabase(object):
    """
    Defines the interface required for the Glucose Service to fetch records and record info
    """
    def first_record(self):
        """
        Gets the first (oldest) record in the database

        :return: The first record in the database, or None if no records in the database
        :rtype: GlucoseMeasurement
        """
        raise NotImplementedError()

    def last_record(self):
        """
        Gets the last (newest) record in the database

        :return: The last record in the database, or None if no records in the database
        :rtype: GlucoseMeasurement
        """
        raise NotImplementedError()

    def record_count(self, min_seq_num=None, max_seq_num=None):
        """
        Gets the number of records between the minimum and maximum sequence numbers provided.
        The min/max limits are inclusive.

        :param min_seq_num: The minimum sequence number to get. If None, no minimum is requested
        :param max_seq_num: The maximum sequence number to get. If None, no maximum is requested
        :return: The number of records that fit the parameters specified
        :rtype: int
        """
        raise NotImplementedError()

    def get_records(self, min_seq_num=None, max_seq_num=None):
        """
        Gets a list of the records between the minimum sequence and maximum sequence numbers provided.
        The min/max limits are inclusive.

        :param min_seq_num: The minimum sequence number to get. If None, no minimum is requested
        :param max_seq_num: The maximum sequence number to get. If None, no maximum is requested
        :return: The list of glucose measurement records that fit the parameters
        :rtype: list[GlucoseMeasurement]
        """
        raise NotImplementedError()

    def delete_records(self, min_seq_num=None, max_seq_num=None):
        """
        Deletes the records between the minimum sequence and maximum sequence numbers provided.
        The min/max limits are inclusive.

        :param min_seq_num: The minimum sequence number to get. If None, no minimum is requested
        :param max_seq_num: The maximum sequence number to get. If None, no maximum is requested
        :return: The response code to send back for the operation
        :rtype: RacpResponseCode
        """
        raise NotImplementedError()


class BasicGlucoseDatabase(IGlucoseDatabase):
    """
    Basic glucose database which simply stores the records in a sorted list, and provides a method for adding
    new records to the database.
    """
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
            records = [r for r in records if r.sequence_number >= min_seq_num]
        if max_seq_num is not None:
            records = [r for r in records if r.sequence_number <= max_seq_num]
        return records

    def delete_records(self, min_seq_num=None, max_seq_num=None):
        """
        See IGlucoseDatabase
        """
        with self._lock:
            records = self._get_records_in_range(min_seq_num, max_seq_num)
            logger.info("Deleting records between {} and {} - seqs: {}".format(min_seq_num, max_seq_num,
                                                                               [r.sequence_number for r in records]))
            for r in records:
                self._records.remove(r)
        return RacpResponseCode.success

    def record_count(self, min_seq_num=None, max_seq_num=None):
        """
        See IGlucoseDatabase
        """
        num_records = len(self._get_records_in_range(min_seq_num, max_seq_num))
        logger.info("Got record count between {} and {} -  {} records".format(min_seq_num, max_seq_num, num_records))
        return num_records

    def get_records(self, min_seq_num=None, max_seq_num=None):
        """
        See IGlucoseDatabase
        """
        records = self._get_records_in_range(min_seq_num, max_seq_num)
        logger.info("Getting records between {} and {} - seqs: {}".format(min_seq_num, max_seq_num,
                                                                          [r.sequence_number for r in records]))
        return records

    def first_record(self):
        """
        See IGlucoseDatabase
        """
        with self._lock:
            if self._records:
                record = self._records[0]
            else:
                record = None

        logger.info("Glucose DB: First record requested: {}".format(record))
        return record

    def last_record(self):
        """
        See IGlucoseDatabase
        """
        with self._lock:
            if self._records:
                record = self._records[-1]
            else:
                record = None

        logger.info("Glucose DB: Last record requested: {}".format(record))
        return record

    def add_record(self, glucose_measurement):
        """
        Adds a record to the database. NOTE: the measurement's sequence number must be unique within the database

        :param glucose_measurement: The measurement to add
        :type glucose_measurement: GlucoseMeasurement
        """
        with self._lock:
            if glucose_measurement.sequence_number in [r.sequence_number for r in self._records]:
                raise ValueError("Database already contains a measurement with sequence number {}".format(glucose_measurement.sequence_number))
            self._records.append(glucose_measurement)
        self._sort()
