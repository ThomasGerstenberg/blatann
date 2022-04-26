import random
from blatann import BleDevice
from blatann.gap import AdvertisingData
from blatann.gatt.gattc import GattcCharacteristic
from blatann.gatt.gatts import GattsCharacteristic
from blatann.nrf.nrf_types import conn_interval_range
from blatann.peer import Peripheral, Client, ConnectionParameters
from blatann.uuid import generate_random_uuid128


class PeriphConn(object):
    def __init__(self):
        self.dev: BleDevice = None
        self.peer: Client = None


class CentralConn(object):
    def __init__(self):
        self.dev: BleDevice = None
        self.peer: Peripheral = None

    @property
    def db(self):
        return self.peer.database


def setup_connection(periph_conn: PeriphConn, central_conn: CentralConn,
                     conn_params=None, discover_services=True):
    if conn_params is None:
        conn_params = ConnectionParameters(conn_interval_range.min, conn_interval_range.min, 4000)
    periph_conn.dev.set_default_peripheral_connection_params(conn_params.max_conn_interval_ms,
                                                             conn_params.max_conn_interval_ms,
                                                             conn_params.conn_sup_timeout_ms)
    periph_conn.dev.advertiser.set_advertise_data(AdvertisingData(flags=0x06, local_name="Blatann Test"))
    adv_addr = periph_conn.dev.address

    # Start advertising, then initiate connection from central.
    # Once central reports its connected wait for the peripheral to be connected before continuing
    waitable = periph_conn.dev.advertiser.start(timeout_sec=30)
    central_conn.peer = central_conn.dev.connect(adv_addr, conn_params).wait(10)

    periph_conn.peer = waitable.wait(10)

    if discover_services:
        central_conn.peer.discover_services().wait(10)


def rand_bytes(n):
    return bytes(random.randint(0, 255) for _ in range(n))
