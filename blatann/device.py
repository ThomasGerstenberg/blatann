import logging
from threading import Lock
from typing import Union

from blatann import peer, exceptions
from blatann.gap import advertising, scanning, default_bond_db, IoCapabilities, SecurityParameters, PairingPolicy
from blatann.gap.generic_access_service import GenericAccessService
from blatann.gatt import gatts, MTU_SIZE_FOR_MAX_DLE, MTU_SIZE_MINIMUM
from blatann.nrf import nrf_events, nrf_types
from blatann.nrf.nrf_driver import NrfDriver, NrfDriverObserver
from blatann.uuid import Uuid, Uuid16, Uuid128
from blatann.waitables.connection_waitable import PeripheralConnectionWaitable
from blatann.bt_sig.uuids import UUID_DESCRIPTION_MAP


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
                logger.debug("Got NRF Driver event: %s", event)


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
            uuid = Uuid16(nrf_uuid.get_value())
            uuid.description = UUID_DESCRIPTION_MAP.get(uuid, "")
            return uuid
        base = None
        for uuid_base in self.registered_vs_uuids:
            if nrf_uuid.base.type == uuid_base.type:
                base = uuid_base

        if base is None:
            raise ValueError("Unable to find registered 128-bit uuid: {}".format(nrf_uuid))
        return Uuid128.combine_with_base(nrf_uuid.value, base.base)


class BleDevice(NrfDriverObserver):
    """
    Represents the Bluetooth device itself. Provides the high-level bluetooth APIs (Advertising, Scanning, Connections),
    configuration, and bond database
    """
    def __init__(self, comport="COM1", baud=1000000, log_driver_comms=False,
                 notification_hw_queue_size=16, write_command_hw_queue_size=16):
        self.ble_driver = NrfDriver(comport, baud, log_driver_comms)
        self.event_logger = _EventLogger(self.ble_driver)
        self.ble_driver.observer_register(self)
        self.ble_driver.event_subscribe(self._on_user_mem_request, nrf_events.EvtUserMemoryRequest)
        self.ble_driver.event_subscribe(self._on_sys_attr_missing, nrf_events.GattsEvtSysAttrMissing)
        self._ble_configuration = self.ble_driver.ble_enable_params_setup()
        self._default_conn_config = nrf_types.BleConnConfig(event_length=6,                                       # Minimum event length required for max DLE
                                                            hvn_tx_queue_size=notification_hw_queue_size,         # Hardware queue of 16 notifications
                                                            write_cmd_tx_queue_size=write_command_hw_queue_size)  # Hardware queue of 16 write cmds (no response)

        self.bond_db_loader = default_bond_db.DefaultBondDatabaseLoader()
        self.bond_db = default_bond_db.DefaultBondDatabase()

        self.client = peer.Client(self)
        self.connected_peripherals = {}
        self.connecting_peripheral = None

        self.uuid_manager = _UuidManager(self.ble_driver)
        self.advertiser = advertising.Advertiser(self, self.client, self._default_conn_config.conn_tag)
        self.scanner = scanning.Scanner(self)
        self._generic_access_service = GenericAccessService(self.ble_driver)
        self._db = gatts.GattsDatabase(self, self.client, self._default_conn_config.hvn_tx_queue_size)
        self._default_conn_params = peer.DEFAULT_CONNECTION_PARAMS
        self._default_security_params = peer.DEFAULT_SECURITY_PARAMS
        self._att_mtu_max = MTU_SIZE_MINIMUM

    def configure(self, vendor_specific_uuid_count=10,
                  service_changed=False,
                  max_connected_peripherals=1,
                  max_connected_clients=1,
                  max_secured_peripherals=1,
                  attribute_table_size=nrf_types.driver.BLE_GATTS_ATTR_TAB_SIZE_DEFAULT,
                  att_mtu_max_size=MTU_SIZE_FOR_MAX_DLE):
        """
        Configures the BLE Device with the given settings.

        .. note:: Configuration must be set before opening the device

        :param vendor_specific_uuid_count: The Nordic hardware limits number of 128-bit Base UUIDs
                                           that the device can know about. This normally equals the number of custom services
                                           that are to be supported, since characteristic UUIDs are usually derived from the service base UUID.
        :param service_changed: Whether or not the Service Changed characteristic is exposed in the GAP service
        :param max_connected_peripherals: The maximum number of concurrent connections with peripheral devices
        :param max_connected_clients: The maximum number of concurrent connections with client devices (NOTE: blatann currently only supports 1)
        :param max_secured_peripherals: The maximum number of concurrent peripheral connections that will need security (bonding/pairing) enabled
        :param attribute_table_size: The maximum size of the attribute table.
                                     Increase this number if there's a lot of services/characteristics in your GATT database.
        :param att_mtu_max_size: The maximum ATT MTU size supported. The default supports an MTU which will fit into
                                 a single transmission if Data Length Extensions is set to its max (251)
        """
        if self.ble_driver.is_open:
            raise exceptions.InvalidStateException("Cannot configure the BLE device after it has been opened")

        self._ble_configuration = nrf_types.BleEnableConfig(vendor_specific_uuid_count, max_connected_clients,
                                                            max_connected_peripherals, max_secured_peripherals,
                                                            service_changed, attribute_table_size)
        self._default_conn_config.max_att_mtu = att_mtu_max_size

    def open(self, clear_bonding_data=False):
        """
        Opens the connection to the BLE device. Must be called prior to performing any BLE operations

        :param clear_bonding_data: Flag that the bonding data should be cleared prior to opening the device.
        """
        if clear_bonding_data:
            self.clear_bonding_data()
        else:
            self.bond_db = self.bond_db_loader.load()
        self.ble_driver.open()
        self._default_conn_config.conn_count = self._ble_configuration.central_role_count + self._ble_configuration.periph_role_count
        self.ble_driver.ble_conn_configure(self._default_conn_config)
        self.ble_driver.ble_enable(self._ble_configuration)
        self._generic_access_service.update()

    def close(self):
        """
        Closes the connection to the BLE device. The connection to the device must be opened again to perform BLE operations.
        """
        if self.ble_driver.is_open:
            self.ble_driver.close()
            self.bond_db_loader.save(self.bond_db)

    def __del__(self):
        self.close()

    def clear_bonding_data(self):
        """
        Clears out all bonding data from the bond database. Any subsequent connections
        will require re-pairing.
        """
        logger.info("Clearing out all bonding information")
        self.bond_db.delete_all()
        self.bond_db_loader.save(self.bond_db)

    @property
    def address(self) -> nrf_types.BLEGapAddr:
        """
        The MAC Address of the BLE device

        :getter: Gets the MAC address of the BLE device
        :setter: Sets the MAC address for the device to use

        .. note:: The MAC address cannot be changed while the device is advertising, scanning, or initiating a connection
        """
        return self.ble_driver.ble_gap_addr_get()

    @address.setter
    def address(self, address):
        self.ble_driver.ble_gap_addr_set(address)

    @property
    def database(self) -> gatts.GattsDatabase:
        """
        **Read Only**

        The local database instance that is accessed by connected clients
        """
        return self._db

    @property
    def generic_access_service(self) -> GenericAccessService:
        """
        **Read Only**

        The Generic Access service in the local database
        """
        return self._generic_access_service

    @property
    def max_mtu_size(self) -> int:
        """
        **Read Only**

        The maximum allowed ATT MTU size that was configured for the device

        .. note:: The Max MTU size is set through :meth:`configure`
        """
        return self._default_conn_config.max_att_mtu

    def connect(self, peer_address, connection_params=None) -> PeripheralConnectionWaitable:
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
        """
        if peer_address in self.connected_peripherals.keys():
            raise exceptions.InvalidStateException("Already connected to {}".format(peer_address))
        if self.connecting_peripheral is not None:
            raise exceptions.InvalidStateException("Cannot initiate a new connection while connecting to another")

        # Try finding the peer's name in the scan report
        name = ""
        scan_report = self.scanner.scan_report.get_report_for_peer(peer_address)
        if scan_report:
            name = scan_report.advertise_data.local_name

        if not connection_params:
            connection_params = self._default_conn_params

        self.connecting_peripheral = peer.Peripheral(self, peer_address, connection_params, self._default_security_params, name,
                                                     self._default_conn_config.write_cmd_tx_queue_size)
        periph_connection_waitable = PeripheralConnectionWaitable(self, self.connecting_peripheral)
        self.ble_driver.ble_gap_connect(peer_address, conn_params=connection_params,
                                        conn_cfg_tag=self._default_conn_config.conn_tag)
        return periph_connection_waitable

    def set_default_peripheral_connection_params(self, min_interval_ms: float, max_interval_ms: float,
                                                 timeout_ms: int, slave_latency: int = 0):
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

    def set_default_security_params(self, passcode_pairing: bool, io_capabilities: IoCapabilities, bond: bool, out_of_band: bool,
                                    reject_pairing_requests: Union[bool, PairingPolicy] = False, lesc_pairing: bool = False):
        """
        Sets the default security parameters for all subsequent connections to peripherals.

        :param passcode_pairing: Flag indicating that passcode pairing is required
        :param io_capabilities: The input/output capabilities of this device
        :param bond: Flag indicating that long-term bonding should be performed
        :param out_of_band: Flag indicating if out-of-band pairing is supported
        :param reject_pairing_requests: Flag indicating that all security requests by the peer should be rejected
        :param lesc_pairing: Flag indicating that LE Secure Pairing methods are supported
        """
        self._default_security_params = SecurityParameters(passcode_pairing, io_capabilities, bond, out_of_band,
                                                           reject_pairing_requests, lesc_pairing)

    def _on_user_mem_request(self, nrf_driver, event):
        # Only action that can be taken
        self.ble_driver.ble_user_mem_reply(event.conn_handle)

    def _on_sys_attr_missing(self, nrf_driver, event):
        # TODO: Save/load system attributes from a database
        self.ble_driver.ble_gatts_sys_attr_set(event.conn_handle, None)

    def on_driver_event(self, nrf_driver, event):
        """
        For internal use only
        """
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
