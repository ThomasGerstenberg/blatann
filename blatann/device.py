import logging
from threading import Lock

from blatann import peer, exceptions
from blatann.gap import advertising, scanning
from blatann.gatt import gatts
from blatann.nrf import nrf_events, nrf_types
from blatann.nrf.nrf_driver import NrfDriver
from blatann.nrf.nrf_observers import NrfDriverObserver
from blatann.uuid import Uuid, Uuid16, Uuid128
from blatann.waitables.connection_waitable import PeripheralConnectionWaitable

logger = logging.getLogger(__name__)


class _EventLogger(NrfDriverObserver):
    def __init__(self, ble_driver):
        ble_driver.observer_register(self)
        self._suppressed_events = []
        self._lock = Lock()

    def suppress(self, *nrf_event_types):
        with self._lock:
            for e in nrf_event_types:
                if e not in self._suppressed_events:
                    self._suppressed_events.append(e)

    def on_driver_event(self, nrf_driver, event):
        with self._lock:
            if type(event) not in self._suppressed_events:
                logger.debug("Got NRF Driver event: {}".format(event))


class _UuidManager(object):
    def __init__(self, ble_driver):
        """

        :type ble_driver: pc_ble_driver_py.nrf_driver.NrfDriver
        """
        self.ble_driver = ble_driver
        self.registered_vs_uuids = []

    def register_uuid(self, uuid):
        if isinstance(uuid, Uuid16):
            return  # Don't need to register standard 16-bit UUIDs
        elif isinstance(uuid, Uuid128):
            # Check if the base is already registered. If so, do nothing
            for registered_base in self.registered_vs_uuids:
                if uuid.uuid_base == registered_base.base:
                    uuid.nrf_uuid = nrf_types.BLEUUID(uuid.uuid16, registered_base)
                    return
            # Not registered, create a base
            base = nrf_types.BLEUUIDBase(uuid.uuid_base)
            self.ble_driver.ble_vs_uuid_add(base)
            self.registered_vs_uuids.append(base)
            uuid.nrf_uuid = nrf_types.BLEUUID(uuid.uuid16, base)
        elif isinstance(uuid, nrf_types.BLEUUID):
            self.ble_driver.ble_vs_uuid_add(uuid.base)
            self.registered_vs_uuids.append(uuid.base)
        elif isinstance(uuid, nrf_types.BLEUUIDBase):
            self.ble_driver.ble_vs_uuid_add(uuid)
            self.registered_vs_uuids.append(uuid.base)
        else:
            raise ValueError("uuid must be a 16-bit or 128-bit UUID")

    def nrf_uuid_to_uuid(self, nrf_uuid):
        """
        :type nrf_uuid: BLEUUID
        :rtype: Uuid
        """
        if nrf_uuid.base.type == 0:
            raise ValueError("UUID Not registered: {}".format(nrf_uuid))
        if nrf_uuid.base.type == nrf_types.BLEUUIDBase.BLE_UUID_TYPE_BLE:
            return Uuid16(nrf_uuid.get_value())
        base = None
        for uuid_base in self.registered_vs_uuids:
            if nrf_uuid.base.type == uuid_base.type:
                base = uuid_base

        if base is None:
            raise ValueError("Unable to find registered 128-bit uuid: {}".format(nrf_uuid))
        return Uuid128.combine_with_base(nrf_uuid.value, base.base)


class BleDevice(NrfDriverObserver):
    def __init__(self, comport="COM1", baud=115200):
        self.ble_driver = NrfDriver(comport, baud)
        self.event_logger = _EventLogger(self.ble_driver)
        self.ble_driver.observer_register(self)
        self.ble_driver.event_subscribe(self._on_user_mem_request, nrf_events.EvtUserMemoryRequest)
        self._ble_configuration = self.ble_driver.ble_enable_params_setup()

        self.client = peer.Client(self)
        self.connected_peripherals = {}
        self.connecting_peripheral = None

        self.uuid_manager = _UuidManager(self.ble_driver)
        self.advertiser = advertising.Advertiser(self, self.client)
        self.scanner = scanning.Scanner(self)
        self._db = gatts.GattsDatabase(self, self.client)
        self._default_conn_params = peer.DEFAULT_CONNECTION_PARAMS

    def configure(self, vendor_specific_uuid_count=10, service_changed=False, max_connected_peripherals=1,
                  max_connected_clients=1, max_secured_peripherals=1,
                  attribute_table_size=nrf_types.driver.BLE_GATTS_ATTR_TAB_SIZE_DEFAULT):
        self._ble_configuration = nrf_types.BLEEnableParams(vendor_specific_uuid_count, service_changed,
                                                            max_connected_clients, max_connected_peripherals,
                                                            max_secured_peripherals, attribute_table_size)

    def open(self):
        self.ble_driver.open()
        self.ble_driver.ble_enable(self._ble_configuration)

    def close(self):
        self.ble_driver.close()

    def __del__(self):
        self.close()

    @property
    def database(self):
        """
        Gets the local database instance that is accessed by connected clients

        :return: The local database
        :rtype: gatts.GattsDatabase
        """
        return self._db

    def connect(self, peer_address, connection_params=None):
        """
        Initiates a connection to a peripheral peer with the specified connection parameters, or uses the default
        connection parameters if not specified. The connection will not be complete until the returned waitable
        either times out or reports the newly connected peer

        :param peer_address: The address of the peer to connect to
        :type peer_address: peer.PeerAddress
        :param connection_params: Optional connection parameters to use. If not specified, uses the set default
        :type connection_params: peer.ConnectionParameters
        :return: A Waitable which can be used to wait until the connection is successful or times out. Waitable returns
                 a peer.Peripheral object
        :rtype: PeripheralConnectionWaitable
        """
        if peer_address in self.connected_peripherals.keys():
            raise exceptions.InvalidStateException("Already connected to {}".format(peer_address))
        if self.connecting_peripheral is not None:
            raise exceptions.InvalidStateException("Cannot initiate a new connection while connecting to another")

        if not connection_params:
            connection_params = self._default_conn_params

        self.connecting_peripheral = peer.Peripheral(self, peer_address, connection_params)
        periph_connection_waitable = PeripheralConnectionWaitable(self, self.connecting_peripheral)
        self.ble_driver.ble_gap_connect(peer_address)
        return periph_connection_waitable

    def set_default_peripheral_connection_params(self, min_interval_ms, max_interval_ms, timeout_ms, slave_latency=0):
        """
        Sets the default connection parameters for all subsequent connection attempts to peripherals.
        Refer to the Bluetooth specifications for the valid ranges

        :param min_interval_ms: The minimum desired connection interval, in milliseconds
        :param max_interval_ms: The maximum desired connection interval, in milliseconds
        :param timeout_ms: The connection timeout period, in milliseconds
        :param slave_latency: The connection slave latency
        """
        self._default_conn_params = peer.ConnectionParameters(min_interval_ms, max_interval_ms,
                                                              timeout_ms, slave_latency)

    def _on_user_mem_request(self, nrf_driver, event):
        # Only action that can be taken
        self.ble_driver.ble_user_mem_reply(event.conn_handle)

    def on_driver_event(self, nrf_driver, event):
        if isinstance(event, nrf_events.GapEvtConnected):
            conn_params = peer.ConnectionParameters(event.conn_params.min_conn_interval_ms,
                                                    event.conn_params.max_conn_interval_ms,
                                                    event.conn_params.conn_sup_timeout_ms,
                                                    event.conn_params.slave_latency)
            if event.role == nrf_events.BLEGapRoles.periph:
                self.client.peer_connected(event.conn_handle, event.peer_addr, conn_params)
            else:
                if self.connecting_peripheral.peer_address != event.peer_addr:
                    logger.warning("Mismatching address between connecting peripheral and peer event: "
                                   "{} vs {}".format(self.connecting_peripheral.address, event.peer_addr))
                else:
                    self.connected_peripherals[self.connecting_peripheral.peer_address] = self.connecting_peripheral
                    self.connecting_peripheral.peer_connected(event.conn_handle, event.peer_addr, conn_params)
                self.connecting_peripheral = None
        if isinstance(event, nrf_events.GapEvtTimeout):
            if event.src == nrf_events.BLEGapTimeoutSrc.conn:
                self.connecting_peripheral = None
        if isinstance(event, nrf_events.GapEvtDisconnected):
            for peer_address, p in self.connected_peripherals.items():
                if p.conn_handle == event.conn_handle:
                    del self.connected_peripherals[peer_address]
                    return

