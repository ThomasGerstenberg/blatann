from blatann.services.battery.service import BatteryServer as _BatteryServer, BatteryClient as _BatteryClient, SecurityLevel
from blatann.services.battery.constants import BATTERY_SERVICE_UUID, BATTERY_LEVEL_CHARACTERISTIC_UUID


def add_battery_service(gatts_database, enable_notifications=False, security_level=SecurityLevel.OPEN):
    """
    Adds a battery service to the given GATT Server database

    :param gatts_database: The database to add the service to
    :type gatts_database: blatann.gatt.gatts.GattsDatabase
    :param enable_notifications: Whether or not the Battery Level characteristic allows notifications
    :param security_level: The security level to use for the service
    :return: The Battery service
    :rtype: _BatteryServer
    """
    return _BatteryServer.add_to_database(gatts_database, enable_notifications, security_level)


def find_battery_service(gattc_database):
    """
    Finds a battery service in the given GATT client database

    :param gattc_database: the GATT client database to search
    :type gattc_database: blatann.gatt.gattc.GattcDatabase
    :return: The Battery service if found, None if not found
    :rtype: _BatteryClient
    """
    return _BatteryClient.find_in_database(gattc_database)
