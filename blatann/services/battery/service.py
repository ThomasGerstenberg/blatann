from __future__ import annotations
import binascii
import logging
from blatann.services.battery.constants import *
from blatann.services.battery.data_types import *
from blatann.event_type import EventSource, Event
from blatann.event_args import DecodedReadCompleteEventArgs, ReadCompleteEventArgs, GattOperationCompleteReason
from blatann.waitables import EventWaitable
from blatann.gatt import SecurityLevel, GattStatusCode
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties


logger = logging.getLogger(__name__)


class BatteryServer(object):
    def __init__(self, service, enable_notifications=False, security_level=SecurityLevel.OPEN):
        """
        :type service: GattsService
        :param enable_notifications:
        :param security_level:
        """
        self._service = service

        battery_level_char_props = GattsCharacteristicProperties(read=True, notify=enable_notifications,
                                                                 variable_length=False,
                                                                 max_length=BatteryLevel.encoded_size(),
                                                                 security_level=security_level)
        self._batt_characteristic = service.add_characteristic(BATTERY_LEVEL_CHARACTERISTIC_UUID,
                                                               battery_level_char_props)

    def set_battery_level(self, battery_percent: int, notify_client=True):
        """
        Sets the new battery level in the service

        :param battery_percent: The new battery percent
        :param notify_client: Whether or not to notify the connected client with the updated value
        """
        battery_percent = int(battery_percent)
        if battery_percent < 0 or battery_percent > 100:
            raise ValueError("Battery % must be between 0 and 100, got {}".format(battery_percent))
        notify_client = notify_client and self._batt_characteristic.notifiable
        return self._batt_characteristic.set_value(BatteryLevel.encode(battery_percent), notify_client)

    @classmethod
    def add_to_database(cls, gatts_database, enable_notifications=False, security_level=SecurityLevel.OPEN):
        """
        :type gatts_database: blatann.gatt.gatts.GattsDatabase
        """
        service = gatts_database.add_service(BATTERY_SERVICE_UUID)
        return BatteryServer(service, enable_notifications, security_level)


class BatteryClient(object):
    def __init__(self, gattc_service):
        """
        :type gattc_service: blatann.gatt.gattc.GattcService
        """
        self._service = gattc_service
        self._batt_characteristic = gattc_service.find_characteristic(BATTERY_LEVEL_CHARACTERISTIC_UUID)
        self._on_battery_level_updated_event = EventSource("Battery Level Update Event")

    def read(self) -> EventWaitable[BatteryClient, DecodedReadCompleteEventArgs[int]]:
        """
        Reads the Battery level characteristic.

        :return: A waitable for when the read completes, which waits for the on_battery_level_update_event to be
                 emitted
        """
        self._batt_characteristic.read().then(self._on_read_complete)
        return EventWaitable(self._on_battery_level_updated_event)

    @property
    def on_battery_level_updated(self) -> Event[BatteryClient, DecodedReadCompleteEventArgs[int]]:
        """
        Event that is generated whenever the battery level on the peripheral is updated, whether
        it is by notification or from reading the characteristic itself.

        The DecodedReadCompleteEventArgs value given is the integer battery percent received. If the read failed
        or failed to decode, the value will be equal to the raw bytes received.
        """
        return self._on_battery_level_updated_event

    @property
    def can_enable_notifications(self) -> bool:
        """
        Checks if the battery level characteristic allows notifications to be subscribed to

        :return: True if notifications can be enabled, False if not
        """
        return self._batt_characteristic.subscribable

    def enable_notifications(self):
        """
        Enables notifications for the battery level characteristic. Note: this function will raise an exception
        if notifications aren't possible

        :return: a Waitable which waits for the write to finish
        """
        return self._batt_characteristic.subscribe(self._on_battery_level_notification)

    def disable_notifications(self):
        """
        Disables notifications for the battery level characteristic. Note: this function will raise an exception
        if notifications aren't possible

        :return: a Waitable which waits for the write to finish
        """
        return self._batt_characteristic.unsubscribe()

    def _on_battery_level_notification(self, characteristic, event_args):
        """
        :param characteristic:
        :type event_args: blatann.event_args.NotificationReceivedEventArgs
        :return:
        """
        decoded_value = None
        try:
            stream = ble_data_types.BleDataStream(event_args.value)
            decoded_value = BatteryLevel.decode(stream)
        except Exception as e:  # TODO not so generic
            logger.error("Failed to decode Battery Level, stream: [{}]".format(binascii.hexlify(event_args.value)))
            logger.exception(e)

        decoded_event_args = DecodedReadCompleteEventArgs.from_notification_complete_event_args(event_args, decoded_value)
        self._on_battery_level_updated_event.notify(self, decoded_event_args)

    def _on_read_complete(self, characteristic, event_args):
        """
        :param characteristic:
        :type event_args: blatann.event_args.ReadCompleteEventArgs
        """
        decoded_value = None
        if event_args.status == GattStatusCode.success:
            try:
                stream = ble_data_types.BleDataStream(event_args.value)
                decoded_value = BatteryLevel.decode(stream)
            except Exception as e:  # TODO not so generic
                logger.error("Failed to decode Battery Level, stream: [{}]".format(binascii.hexlify(event_args.value)))
                logger.exception(e)

        decoded_event_args = DecodedReadCompleteEventArgs.from_read_complete_event_args(event_args, decoded_value)
        self._on_battery_level_updated_event.notify(self, decoded_event_args)

    @classmethod
    def find_in_database(cls, gattc_database):
        """
        :type gattc_database: blatann.gatt.gattc.GattcDatabase
        :rtype: BatteryClient
        """
        service = gattc_database.find_service(BATTERY_SERVICE_UUID)
        if service:
            return BatteryClient(service)
