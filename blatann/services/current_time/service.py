from __future__ import annotations
import datetime
import logging
import pytz.reference

from blatann.event_type import EventSource, Event
from blatann.exceptions import InvalidOperationException
from blatann.event_args import DecodedReadCompleteEventArgs, DecodedWriteEventArgs
from blatann.services.decoded_event_dispatcher import DecodedReadWriteEventDispatcher
from blatann.services.current_time.constants import *
from blatann.services.current_time.data_types import *
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties
from blatann.waitables.event_waitable import IdBasedEventWaitable, EventWaitable

logger = logging.getLogger(__name__)


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
        self._current_time_read_callback = self._on_characteristic_read_auto
        self._time_delta = datetime.timedelta()

        self._on_current_time_write_event = EventSource("Current Time Write Event")
        self._on_local_time_info_write_event = EventSource("Local Time Info Write Event")

        self._current_time_dispatcher = DecodedReadWriteEventDispatcher(self, CurrentTime,
                                                                        self._on_current_time_write_event, logger)
        self._local_time_dispatcher = DecodedReadWriteEventDispatcher(self, LocalTimeInfo,
                                                                      self._on_local_time_info_write_event, logger)

        cur_time_char_props = GattsCharacteristicProperties(read=True, notify=True, write=is_writable,
                                                            variable_length=False, max_length=CurrentTime.encoded_size())
        self._cur_time_char = service.add_characteristic(CURRENT_TIME_CHARACTERISTIC_UUID, cur_time_char_props)
        self._cur_time_char.on_read.register(self._on_current_time_read)
        self._cur_time_char.on_write.register(self._current_time_dispatcher)

        if enable_local_time_info_char:
            local_time_props = GattsCharacteristicProperties(read=True, notify=True, write=is_writable,
                                                             variable_length=False, max_length=LocalTimeInfo.encoded_size())
            self._local_time_char = service.add_characteristic(LOCAL_TIME_INFO_CHARACTERISTIC_UUID, local_time_props)
            self.set_local_time_info()
            self._local_time_char.on_write.register(self._local_time_dispatcher)

        if enable_ref_time_info_char:
            ref_time_props = GattsCharacteristicProperties(read=True, notify=False, write=False,
                                                           variable_length=False, max_length=ReferenceTimeInfo.encoded_size())
            self._ref_time_char = service.add_characteristic(REFERENCE_INFO_CHARACTERISTIC_UUID, ref_time_props)
            self.set_reference_info()

        self.set_time(datetime.datetime.utcfromtimestamp(0))

    def _on_characteristic_read_auto(self):
        return datetime.datetime.now() + self._time_delta

    def _on_current_time_read(self, char, event_args):
        dt = CurrentTime(self._current_time_read_callback())
        self._cur_time_char.set_value(dt.encode())

    def _on_current_time_write(self, char, event_args):
        logger.info(event_args)

    def _on_local_time_write(self, char, event_args):
        logger.info(event_args)

    @property
    def is_writable(self) -> bool:
        """
        Gets whether or not the service was configured to allow writes to the Current Time and Local Time Info
        characteristics
        """
        return self._is_writable

    @property
    def has_local_time_info(self) -> bool:
        """
        Gets whether or not the service was configured to show the Local Time Info characteristic
        """
        return self._has_local_time_info

    @property
    def has_reference_time_info(self) -> bool:
        """
        Gets whether or not the service was configured to show the Reference Time Info characteristic
        """
        return self._has_ref_time_info

    @property
    def on_current_time_write(self) -> Event[CurrentTimeServer, DecodedWriteEventArgs[CurrentTime]]:
        """
        Event that is triggered when a client writes to the Current Time Characteristic.
        Event emits a DecodedWriteEventArgs argument where the value is of type current_time.CurrentTime
        """
        return self._on_current_time_write_event

    @property
    def on_local_time_info_write(self) -> Event[CurrentTimeServer, DecodedWriteEventArgs[LocalTimeInfo]]:
        """
        Event that is triggered when a client writes to the Local Time Info Characteristic (if present).
        Event emits a DecodedWriteEventArgs argument where the value is of type current_time.LocalTimeInfo
        """
        return self._on_local_time_info_write_event

    def configure_automatic(self):
        """
        Configures the current time and local time info (if present) to use the system time
        """
        now = datetime.datetime.now()

        adj_reason = AdjustmentReason(AdjustmentReasonType.manual_time_update,
                                      AdjustmentReasonType.dst_change,
                                      AdjustmentReasonType.time_zone_change)
        self.set_time(adjustment_reason=adj_reason)

        if self.has_local_time_info:
            local_timezone = pytz.reference.LocalTimezone()
            offset = local_timezone.utcoffset(now).total_seconds()
            dst = local_timezone.dst(now).total_seconds()
            # Get the actual offset by subtracting the DST
            offset -= dst
            dst_enum = DaylightSavingsTimeOffset.from_seconds(dst)

            self.set_local_time_info(offset/3600.0, dst_enum)

    def set_time(self, date=None, adjustment_reason=None, characteristic_read_callback=None):
        """
        Manually sets the time to report to the client.

        If characteristic_read_callback is supplied,
        the function is called for future reads on that characteristic to fetch the current time
        If characteristic_read_callback is None,
        future reads will be based off of the base datetime given and the time passed

        :param date: The new base date to set the characteristic to. Future characteristic reads will base its time
                     off of this value if characteristic_read_callback is not supplied.
                     If the date is not supplied, will use the current system time
                     (same as configure_automatic but doesn't configure local time info)
        :type date: datetime.datetime
        :param adjustment_reason: Optional reason to give for the adjustment
        :type adjustment_reason: AdjustmentReason
        :param characteristic_read_callback: Optional callback to fetch subsequent time values.
                                             Function signature should take no parameters and return a datetime object
        """
        if date is None:
            date = datetime.datetime.now()
            self._time_delta = datetime.timedelta()
        else:
            delta = date - datetime.datetime.now()
            if abs(delta.total_seconds()) < 1:
                delta = datetime.timedelta()
            self._time_delta = delta
        if characteristic_read_callback:
            self._current_time_read_callback = characteristic_read_callback
        else:
            self._current_time_read_callback = self._on_characteristic_read_auto

        dt = CurrentTime(date, adjustment_reason)
        self._cur_time_char.set_value(dt.encode(), True)

    def set_local_time_info(self, timezone_hrs=0.0, dst_offset=DaylightSavingsTimeOffset.standard_time):
        """
        Sets the local time info characteristic data. Only valid if has_local_time_info is True

        :param timezone_hrs: The timezone to report, in hours
        :param dst_offset: The daylight savings time offset
        :type dst_offset: DaylightSavingsTimeOffset
        :raises: InvalidOperationException if the service was not configured with the local time info
        """
        if not self.has_local_time_info:
            raise InvalidOperationException("Current Time service was not initialized with local time info")
        lt = LocalTimeInfo(timezone_hrs, dst_offset)
        self._local_time_char.set_value(lt.encode(), True)

    def set_reference_info(self, time_source=TimeSource.unknown, accuracy=TimeAccuracy.unknown,
                           hours_since_update=None):
        """
        Sets the time reference info characteristic data. Only valid if has_reference_time_info is True

        :param time_source: The time source to use
        :type time_source: TimeSource
        :param accuracy: The accuracy to report
        :type accuracy: TimeAccuracy
        :param hours_since_update: The number of hours since time reference has been updated
        :raises: InvalidOperationException if the service was not configured with the reference info
        """
        if not self.has_reference_time_info:
            raise InvalidOperationException("Current Time service was not initialized with reference info")
        ri = ReferenceTimeInfo(time_source, accuracy, hours_since_update)
        self._ref_time_char.set_value(ri.encode(), False)

    @classmethod
    def add_to_database(cls, gatts_database, is_writable=False,
                        enable_local_time_info_char=False, enable_ref_time_info_char=False):
        service = gatts_database.add_service(CURRENT_TIME_SERVICE_UUID)
        return cls(service, is_writable, enable_local_time_info_char, enable_ref_time_info_char)


class CurrentTimeClient(object):

    def __init__(self, gattc_service):
        """
        :type gattc_service: blatann.gatt.gattc.GattcService
        """
        self._service = gattc_service
        self._current_time_char = gattc_service.find_characteristic(CURRENT_TIME_CHARACTERISTIC_UUID)
        self._local_time_info_char = gattc_service.find_characteristic(LOCAL_TIME_INFO_CHARACTERISTIC_UUID)
        self._ref_info_char = gattc_service.find_characteristic(REFERENCE_INFO_CHARACTERISTIC_UUID)
        self._on_current_time_updated_event = EventSource("Current Time Update Event")
        self._on_local_time_info_updated_event = EventSource("Local Time Info Update Event")
        self._on_reference_info_updated_event = EventSource("Reference Info Update Event")

        self._current_time_dispatcher = DecodedReadWriteEventDispatcher(self, CurrentTime,
                                                                        self._on_current_time_updated_event, logger)
        self._local_time_dispatcher = DecodedReadWriteEventDispatcher(self, LocalTimeInfo,
                                                                      self._on_local_time_info_updated_event, logger)
        self._ref_time_dispatcher = DecodedReadWriteEventDispatcher(self, ReferenceTimeInfo,
                                                                    self._on_reference_info_updated_event, logger)

    @property
    def on_current_time_updated(self) -> Event[CurrentTimeClient, DecodedReadCompleteEventArgs[CurrentTime]]:
        """
        Event triggered when the server has updated its current time
        """
        return self._on_current_time_updated_event

    @property
    def on_local_time_info_updated(self) -> Event[CurrentTimeClient, DecodedReadCompleteEventArgs[LocalTimeInfo]]:
        """
        Event triggered when the server has updated its local time info
        """
        return self._on_local_time_info_updated_event

    @property
    def on_reference_info_updated(self) -> Event[CurrentTimeClient, DecodedReadCompleteEventArgs[ReferenceTimeInfo]]:
        """
        Event triggered when the server has updated its reference time info
        """
        return self._on_reference_info_updated_event

    @property
    def has_local_time_info(self) -> bool:
        return self._local_time_info_char is not None

    @property
    def has_reference_info(self) -> bool:
        return self._ref_info_char is not None

    @property
    def can_enable_notifications(self) -> bool:
        return self._current_time_char.subscribable

    @property
    def can_set_current_time(self) -> bool:
        return self._current_time_char.writable

    @property
    def can_set_local_time_info(self) -> bool:
        if not self.has_local_time_info:
            return False
        return self._local_time_info_char.writable

    def read_time(self) -> EventWaitable[CurrentTimeClient, DecodedReadCompleteEventArgs[CurrentTime]]:
        """
        Reads the time from the server
        """
        self._current_time_char.read().then(self._current_time_dispatcher)
        return EventWaitable(self._on_current_time_updated_event)

    def set_time(self, date, adjustment_reason=None):
        """
        Sets the time on the server to the datetime provided

        :type date: datetime.datetime
        :type adjustment_reason: AdjustmentReason
        """
        dt = CurrentTime(date, adjustment_reason)
        return self._current_time_char.write(dt.encode())
