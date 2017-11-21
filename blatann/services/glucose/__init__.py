from blatann.services.glucose.constants import GLUCOSE_SERVICE_UUID
from blatann.services.glucose.data_types import *
from blatann.services.glucose.database import IGlucoseDatabase, BasicGlucoseDatabase
from blatann.services.glucose.service import GlucoseServer as _GlucoseServer
from blatann.gatt import SecurityLevel


def add_glucose_server(gatts_database, glucose_database, security_level=SecurityLevel.OPEN):
    return _GlucoseServer.add_to_database(gatts_database, glucose_database, security_level)
