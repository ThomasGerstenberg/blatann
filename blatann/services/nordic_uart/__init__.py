from blatann.services.nordic_uart.service import NordicUartServer as _Server, NordicUartClient as _Client
from blatann.services.nordic_uart.constants import (
    NORDIC_UART_SERVICE_UUID,
    NORDIC_UART_RX_CHARACTERISTIC_UUID,
    NORDIC_UART_TX_CHARACTERISTIC_UUID,
    NORDIC_UART_FEATURE_CHARACTERISTIC_UUID
)


def add_nordic_uart_service(gatts_database, max_characteristic_size=None):
    """
    Adds a Nordic UART service to the database

    :param gatts_database: The database to add the service to
    :type gatts_database: blatann.gatt.gatts.GattsDatabase
    :param max_characteristic_size: The size of the characteristic which determines the read/write chunk size.
                                    This should be tuned to the MTU size of the connection
    :return: The Nordic Uart Service
    :rtype: _Server
    """
    return _Server.add_to_database(gatts_database, max_characteristic_size)


def find_nordic_uart_service(gattc_database):
    """
    Finds a Nordic UART service in the given GATT client database

    :param gattc_database: the GATT client database to search
    :type gattc_database: blatann.gatt.gattc.GattcDatabase
    :return: The UART service if found, None if not found
    :rtype: _Client
    """
    return _Client.find_in_database(gattc_database)
