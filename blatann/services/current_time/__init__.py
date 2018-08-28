from blatann.services.current_time.constants import (CURRENT_TIME_SERVICE_UUID,
                                                     CURRENT_TIME_CHARACTERISTIC_UUID,
                                                     LOCAL_TIME_INFO_CHARACTERISTIC_UUID,
                                                     REFERENCE_INFO_CHARACTERISTIC_UUID)
from blatann.services.current_time.data_types import *
from blatann.services.current_time.service import CurrentTimeServer as _CurrentTimeServer


def add_current_time_service(gatts_database, enable_writes=False,
                             enable_local_time_info=False, enable_reference_info=False):
    """
    Adds a Current Time service to the given GATT server database

    :param gatts_database: The database to add the service to
    :type gatts_database: blatann.gatt.gatts.GattsDatabase
    :param enable_writes: Makes the Current time and Local Time info characteristics writable so
                          clients/centrals can update the server's time
    :param enable_local_time_info: Enables the Local Time characteristic in the service
    :param enable_reference_info:  Enables the Reference Info characteristic in the service
    :return: The Current Time service
    :rtype: _CurrentTimeServer
    """
    return _CurrentTimeServer.add_to_database(gatts_database, enable_writes,
                                              enable_local_time_info, enable_reference_info)