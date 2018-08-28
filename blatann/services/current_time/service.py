import datetime
import time
import pytz.reference
from blatann.exceptions import InvalidOperationException
from blatann.services.current_time.constants import *
from blatann.services.current_time.data_types import *
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties


class CurrentTimeServer(object):
    def __init__(self, service, is_writable=False,
                 enable_local_time_info_char=False, enable_ref_time_info_char=False):
        """
        :type service: GattsService
        :param is_writable:
        :param enable_local_time_info_char:
        :param enable_ref_time_info_char:
        """
        self._service = service
        self._is_writable = is_writable
        self._has_local_time_info = enable_local_time_info_char
        self._has_ref_time_info = enable_ref_time_info_char

        cur_time_char_props = GattsCharacteristicProperties(read=True, notify=True, write=is_writable,
                                                            variable_length=False, max_length=CurrentTime.encoded_size())
        self._cur_time_char = service.add_characteristic(CURRENT_TIME_CHARACTERISTIC_UUID, cur_time_char_props)
        self._cur_time_char.on_read.register(self._on_current_time_read)
        self.set_time(datetime.datetime.utcfromtimestamp(0))

        if enable_local_time_info_char:
            local_time_props = GattsCharacteristicProperties(read=True, notify=True, write=is_writable,
                                                             variable_length=False, max_length=LocalTimeInfo.encoded_size())
            self._local_time_char = service.add_characteristic(LOCAL_TIME_INFO_CHARACTERISTIC_UUID, local_time_props)
            self.set_local_time_info()

        if enable_ref_time_info_char:
            ref_time_props = GattsCharacteristicProperties(read=True, notify=False, write=False,
                                                           variable_length=False, max_length=ReferenceTimeInfo.encoded_size())
            self._ref_time_char = service.add_characteristic(REFERENCE_INFO_CHARACTERISTIC_UUID, ref_time_props)
            self.set_reference_info()

    def _on_characteristic_read_auto(self):
        return datetime.datetime.now()

    def _on_current_time_read(self, char, event_args):
        dt = CurrentTime(self._on_characteristic_read_auto())
        self._cur_time_char.set_value(dt.encode())

    @property
    def is_writable(self):
        return self._is_writable

    @property
    def has_local_time_info(self):
        return self._has_local_time_info

    @property
    def has_reference_time_info(self):
        return self._has_ref_time_info

    def configure_automatic(self):
        now = datetime.datetime.now()

        adj_reason = AdjustmentReason(AdjustmentReasonType.manual_time_update,
                                      AdjustmentReasonType.dst_change,
                                      AdjustmentReasonType.time_zone_change)
        self.set_time(now, adj_reason)

        if self.has_local_time_info:
            local_timezone = pytz.reference.LocalTimezone()
            offset = local_timezone.utcoffset(now).total_seconds()
            dst = local_timezone.dst(now).total_seconds()
            # Get the acutal offset by subtracting the DST
            offset -= dst

            # Figure out what DST enum to use
            dst_15_min_incrs = int((dst/3600.0)*4)
            try:
                dst_enum = DaylightSavingsTimeOffset(dst_15_min_incrs)
            except:
                dst_enum = DaylightSavingsTimeOffset.unknown

            self.set_local_time_info(offset/3600.0, dst_enum)

    def set_time(self, date, adjustment_reason=None):
        """
        :type date: datetime.datetime
        :type adjustment_reason: AdjustmentReason
        """
        dt = CurrentTime(date, adjustment_reason)
        self._cur_time_char.set_value(dt.encode(), True)

    def set_local_time_info(self, timezone_hrs=0.0, dst_offset=DaylightSavingsTimeOffset.standard_time):
        if not self.has_local_time_info:
            raise InvalidOperationException("Current Time service was not initialized with local time info")
        lt = LocalTimeInfo(timezone_hrs, dst_offset)
        self._local_time_char.set_value(lt.encode(), True)

    def set_reference_info(self, time_source=TimeSource.unknown, accuracy=TimeAccuracy.unknown, hours_since_update=None):
        if not self.has_reference_time_info:
            raise InvalidOperationException("Current Time service was not initialized with reference info")
        ri = ReferenceTimeInfo(time_source, accuracy, hours_since_update)
        self._ref_time_char.set_value(ri.encode(), False)

    @classmethod
    def add_to_database(cls, gatts_database, is_writable=False,
                        enable_local_time_info_char=False, enable_ref_time_info_char=False):
        service = gatts_database.add_service(CURRENT_TIME_SERVICE_UUID)
        return CurrentTimeServer(service, is_writable, enable_local_time_info_char, enable_ref_time_info_char)
