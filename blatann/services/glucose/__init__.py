from blatann.gatt import SecurityLevel
from blatann.services.glucose.constants import GLUCOSE_SERVICE_UUID
from blatann.services.glucose.data_types import *
from blatann.services.glucose.database import IGlucoseDatabase, BasicGlucoseDatabase

from blatann.services.glucose.service import GlucoseServer as _GlucoseServer


def add_glucose_service(gatts_database, glucose_database, security_level=SecurityLevel.OPEN):
    """
    Adds the Glucose bluetooth service to the Gatt Server database

    :param gatts_database: The GATT database to add the service to
    :type gatts_database: blatann.gatt.gatts.GattsDatabase
    :param glucose_database: The database which holds the glucose measurements
    :type glucose_database: IGlucoseDatabase
    :param security_level: The security level for the record-access control point of the service
    :type security_level: SecurityLevel
    """
    return _GlucoseServer.add_to_database(gatts_database, glucose_database, security_level)
