from blatann.gatt import SecurityLevel
from blatann.services.glucose.constants import GLUCOSE_SERVICE_UUID
from blatann.services.glucose.data_types import *
from blatann.services.glucose.database import IGlucoseDatabase, BasicGlucoseDatabase

from blatann.services.glucose.service import GlucoseServer as _GlucoseServer


def add_glucose_service(gatts_database, glucose_database, security_level=SecurityLevel.OPEN,
                        include_context_characteristic=True):
    """
    Adds the Glucose bluetooth service to the Gatt Server database

    :param gatts_database: The GATT database to add the service to
    :type gatts_database: blatann.gatt.gatts.GattsDatabase
    :param glucose_database: The database which holds the glucose measurements
    :type glucose_database: IGlucoseDatabase
    :param security_level: The security level for the record-access control point of the service
    :type security_level: SecurityLevel
    :param include_context_characteristic: flag whether or not to include the
                                           optional context characteristic in the service. If this is False,
                                           any context stored with glucose measurements will not be reported.
    """
    return _GlucoseServer.add_to_database(gatts_database, glucose_database, security_level,
                                          include_context_characteristic)
