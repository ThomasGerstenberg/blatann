from __future__ import annotations
import logging
import threading
import enum

from blatann.event_type import EventSource, Event
from blatann.gap import smp
from blatann.gatt import gattc, service_discovery, MTU_SIZE_DEFAULT, MTU_SIZE_MINIMUM, DLE_MAX, DLE_MIN, DLE_OVERHEAD
from blatann.nrf import nrf_events
from blatann.nrf.nrf_types.enums import BLE_CONN_HANDLE_INVALID
from blatann.nrf.nrf_types import conn_interval_range, conn_timeout_range, BLEGapDataLengthParams
from blatann.waitables.waitable import EmptyWaitable
from blatann.waitables.connection_waitable import DisconnectionWaitable
from blatann.waitables.event_waitable import EventWaitable
from blatann.event_args import *

logger = logging.getLogger(__name__)


class PeerState(enum.Enum):
    """
    Connection state of the peer
    """
    DISCONNECTED = 0  #: Peer is disconnected
    CONNECTING = 1    #: Peer is in the process of connecting
    CONNECTED = 2     #: Peer is connected


class Phy(enum.IntFlag):
    """
    The supported PHYs

    .. note:: Coded PHY is currently not supported (hardware limitation)
    """
    auto = int(nrf_events.BLEGapPhy.auto)          #: Automatically select the PHY based on what's supported
    one_mbps = int(nrf_events.BLEGapPhy.one_mbps)  #: 1 Mbps PHY
    two_mbps = int(nrf_events.BLEGapPhy.two_mbps)  #: 2 Mbps PHY

    # NOT SUPPORTED coded = int(nrf_events.BLEGapPhy.coded)


class PeerAddress(nrf_events.BLEGapAddr):
    pass


class ConnectionParameters(nrf_events.BLEGapConnParams):
    """
    Represents the connection parameters that are sent during negotiation. This includes
    the preferred min/max interval range, timeout, and slave latency
    """
    def __init__(self, min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency=0):
        super(ConnectionParameters, self).__init__(min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency)
        self.validate()

    def validate(self):
        conn_interval_range.validate(self.min_conn_interval_ms)
        conn_interval_range.validate(self.max_conn_interval_ms)
        conn_timeout_range.validate(self.conn_sup_timeout_ms)
        if self.min_conn_interval_ms > self.max_conn_interval_ms:
            raise ValueError(f"Minimum connection interval must be <= max connection interval "
                             f"(Min: {self.min_conn_interval_ms} Max: {self.max_conn_interval_ms}")


class ActiveConnectionParameters(object):
    """
    Represents the connection parameters that are currently in use with a peer device.
    This is similar to ConnectionParameters with the sole difference being
    the connection interval is not a min/max range but a single number
    """
    def __init__(self, conn_params: ConnectionParameters):
        self._interval_ms = conn_params.min_conn_interval_ms
        self._timeout_ms = conn_params.conn_sup_timeout_ms
        self._slave_latency = conn_params.slave_latency

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"ConnectionParams({self._interval_ms}ms/{self._slave_latency}/{self._timeout_ms}ms)"

    @property
    def interval_ms(self) -> float:
        """
        **Read Only**

        The connection interval, in milliseconds
        """
        return self._interval_ms

    @property
    def timeout_ms(self) -> float:
        """
        **Read Only**

        The connection timeout, in milliseconds
        """
        return self._timeout_ms

    @property
    def slave_latency(self) -> int:
        """
        **Read Only**

        The slave latency (the number of connection intervals the slave is allowed to skip before being
        required to respond)
        """
        return self._slave_latency


DEFAULT_CONNECTION_PARAMS = ConnectionParameters(15, 30, 4000, 0)
DEFAULT_SECURITY_PARAMS = smp.SecurityParameters(reject_pairing_requests=True)


class Peer(object):
    """
    Object that represents a BLE-connected (or disconnected) peer
    """
    BLE_CONN_HANDLE_INVALID = BLE_CONN_HANDLE_INVALID

    """ Number of bytes that are header/overhead per MTU when sending a notification or indication """
    NOTIFICATION_INDICATION_OVERHEAD_BYTES = 3

    def __init__(self, ble_device, role, connection_params=DEFAULT_CONNECTION_PARAMS,
                 security_params=DEFAULT_SECURITY_PARAMS,
                 name="", write_no_resp_queue_size=1):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self._ble_device = ble_device
        self._role = role
        self._name = name
        self._preferred_connection_params = connection_params
        self._current_connection_params = ActiveConnectionParameters(connection_params)
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.peer_address = "",
        self.connection_state = PeerState.DISCONNECTED
        self._on_connect = EventSource("On Connect", logger)
        self._on_disconnect = EventSource("On Disconnect", logger)
        self._on_mtu_exchange_complete = EventSource("On MTU Exchange Complete", logger)
        self._on_mtu_size_updated = EventSource("On MTU Size Updated", logger)
        self._on_data_length_updated = EventSource("On Data Length Updated", logger)
        self._on_phy_updated = EventSource("On Phy Updated", logger)
        self._mtu_size = MTU_SIZE_DEFAULT
        self._preferred_mtu_size = MTU_SIZE_DEFAULT
        self._negotiated_mtu_size = None
        self._preferred_phy = Phy.auto
        self._current_phy = Phy.one_mbps
        self._disconnection_reason = nrf_events.BLEHci.local_host_terminated_connection

        self._connection_based_driver_event_handlers = {}
        self._connection_handler_lock = threading.Lock()

        self.security = smp.SecurityManager(self._ble_device, self, security_params)
        self._db = gattc.GattcDatabase(ble_device, self, write_no_resp_queue_size)
        self._discoverer = service_discovery.DatabaseDiscoverer(ble_device, self)

    """
    Properties
    """

    @property
    def name(self) -> str:
        """
        The name of the peer, if known. This property is for the user's benefit to name certain connections.
        The name is is also saved in the case that the peer is subsequently bonded to and can be looked up that way
        in the bond database

        .. note:: For central peers this name is unknown unless set by the setter.
           For peripheral peers the name is defaulted to the one found in the advertising payload, if any.

       :getter: Gets the name of the peer
       :setter: Sets the name of the peer
        """
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def connected(self) -> bool:
        """
        **Read Only**

        Gets if this peer is currently connected
        """
        return self.connection_state == PeerState.CONNECTED

    @property
    def bytes_per_notification(self) -> int:
        """
        **Read Only**

        The maximum number of bytes that can be sent in a single notification/indication
        """
        return self._mtu_size - self.NOTIFICATION_INDICATION_OVERHEAD_BYTES

    @property
    def is_peripheral(self) -> bool:
        """
        **Read Only**

        Gets if this peer is a peripheral (the local device acting as a central/client)
        """
        return isinstance(self, Peripheral)

    @property
    def is_client(self) -> bool:
        """
        **Read Only**

        Gets if this peer is a Client (the local device acting as a peripheral/server)
        """
        return isinstance(self, Client)

    @property
    def is_previously_bonded(self) -> bool:
        """
        **Read Only**

        Gets if the peer has bonding information stored in the bond database (the peer was bonded to in a previous connection)
        """
        return self.security.is_previously_bonded

    @property
    def preferred_connection_params(self) -> ConnectionParameters:
        """
        **Read Only**

        The connection parameters that were negotiated for this peer
        """
        return self._preferred_connection_params

    @property
    def active_connection_params(self) -> ActiveConnectionParameters:
        """
        **Read Only**

        The active connection parameters in use with the peer.
        If the peer is disconnected, this will return the connection parameters last used
        """
        return self._current_connection_params

    @property
    def mtu_size(self) -> int:
        """
        **Read Only**

        The current size of the MTU for the connection to the peer
        """
        return self._mtu_size

    @property
    def max_mtu_size(self) -> int:
        """
        **Read Only**

        The maximum allowed MTU size. This is set when initially configuring the BLE Device
        """
        return self._ble_device.max_mtu_size

    @property
    def preferred_mtu_size(self) -> int:
        """
        The user-set preferred MTU size. Defaults to the Bluetooth default MTU size (23).
        This is the value that will be negotiated during an MTU Exchange but is not guaranteed in the case that the peer has a smaller MTU

        :getter: Gets the preferred MTU size that was configured
        :setter: Sets the preferred MTU size to use for MTU exchanges
        """
        return self._preferred_mtu_size

    @preferred_mtu_size.setter
    def preferred_mtu_size(self, mtu_size: int):
        self._validate_mtu_size(mtu_size)
        self._preferred_mtu_size = mtu_size

    @property
    def preferred_phy(self) -> Phy:
        """
        The PHY that is preferred for this connection.
        This value is used for Peer-initiated PHY update procedures and
        as the default for :meth:`update_phy`.

        Default value is :attr:`Phy.auto`

        :getter: Gets the preferred PHY
        :setter: Sets the preferred PHY
        """
        return self._preferred_phy

    @preferred_phy.setter
    def preferred_phy(self, phy: Phy):
        self._preferred_phy = phy

    @property
    def phy_channel(self) -> Phy:
        """
        **Read Only**

        The current PHY in use for the connection
        """
        return self._current_phy

    @property
    def database(self) -> gattc.GattcDatabase:
        """
        **Read Only**

        The GATT database of the peer.

        .. note:: This is not useful until services are discovered first
        """
        return self._db

    """
    Events
    """

    @property
    def on_connect(self) -> Event[Peer, None]:
        """
        Event generated when the peer connects to the local device
        """
        return self._on_connect

    @property
    def on_disconnect(self) -> Event[Peer, DisconnectionEventArgs]:
        """
        Event generated when the peer disconnects from the local device
        """
        return self._on_disconnect

    @property
    def on_mtu_exchange_complete(self) -> Event[Peer, MtuSizeUpdatedEventArgs]:
        """
        Event generated when an MTU exchange completes with the peer
        """
        return self._on_mtu_exchange_complete

    @property
    def on_mtu_size_updated(self) -> Event[Peer, MtuSizeUpdatedEventArgs]:
        """
        Event generated when the effective MTU size has been updated on the connection
        """
        return self._on_mtu_size_updated

    @property
    def on_data_length_updated(self) -> Event[Peer, DataLengthUpdatedEventArgs]:
        """
        Event generated when the link layer data length has been updated
        """
        return self._on_data_length_updated

    @property
    def on_phy_updated(self) -> Event[Peer, PhyUpdatedEventArgs]:
        """
        Event generated when the PHY in use for this peer has been updated
        """
        return self._on_phy_updated

    @property
    def on_database_discovery_complete(self) -> Event[Peripheral, DatabaseDiscoveryCompleteEventArgs]:
        """
        Event that is triggered when database discovery has completed
        """
        return self._discoverer.on_discovery_complete

    """
    Public Methods
    """

    def disconnect(self, status_code=nrf_events.BLEHci.remote_user_terminated_connection) -> DisconnectionWaitable:
        """
        Disconnects from the peer, giving the optional status code.
        Returns a waitable that will trigger when the disconnection is complete.
        If the peer is already disconnected, the waitable will trigger immediately

        :param status_code: The HCI Status code to send back to the peer
        :return: A waitable that will trigger when the peer is disconnected
        """
        if self.connection_state != PeerState.CONNECTED:
            return EmptyWaitable(self, self._disconnection_reason)
        self._ble_device.ble_driver.ble_gap_disconnect(self.conn_handle, status_code)
        return self._disconnect_waitable

    def set_connection_parameters(self,
                                  min_connection_interval_ms: float,
                                  max_connection_interval_ms: float,
                                  connection_timeout_ms: int,
                                  slave_latency=0):
        """
        Sets the connection parameters for the peer and starts the connection parameter update process (if connected)

        .. note:: Connection interval values should be a multiple of 1.25ms since that is the granularity allowed in the Bluetooth specification.
           Any non-multiples will be rounded down to the nearest 1.25ms.
           Additionally, the connection timeout has a granularity of 10 milliseconds and will also be rounded as such.

        :param min_connection_interval_ms: The minimum acceptable connection interval, in milliseconds
        :param max_connection_interval_ms: The maximum acceptable connection interval, in milliseconds
        :param connection_timeout_ms: The connection timeout, in milliseconds
        :param slave_latency: The slave latency allowed, which regulates how many connection intervals the peripheral is allowed to skip before responding
        """
        self._preferred_connection_params = ConnectionParameters(min_connection_interval_ms, max_connection_interval_ms,
                                                                 connection_timeout_ms, slave_latency)
        if self.connected:
            self.update_connection_parameters()

    def update_connection_parameters(self):
        """
        Starts the process to re-negotiate the connection parameters using the previously-set connection parameters
        """
        self._ble_device.ble_driver.ble_gap_conn_param_update(self.conn_handle, self._preferred_connection_params)

    def exchange_mtu(self, mtu_size=None) -> EventWaitable[Peer, MtuSizeUpdatedEventArgs]:
        """
        Initiates the MTU Exchange sequence with the peer device.

        If the MTU size is not provided :attr:`preferred_mtu_size` value will be used.
        If an MTU size is provided ``preferred_mtu_size`` will be updated to the given value.

        :param mtu_size: Optional MTU size to use. If provided, it will also updated the preferred MTU size
        :return: A waitable that will trigger when the MTU exchange completes
        """
        # If the MTU size has already been negotiated we need to use the same value
        # as the previous exchange (Vol 3, Part F 3.4.2.2)
        if self._negotiated_mtu_size is None:
            if mtu_size is not None:
                self._validate_mtu_size(mtu_size)
                self._negotiated_mtu_size = mtu_size
            else:
                self._negotiated_mtu_size = self.preferred_mtu_size

        self._ble_device.ble_driver.ble_gattc_exchange_mtu_req(self.conn_handle, self._negotiated_mtu_size)
        return EventWaitable(self._on_mtu_exchange_complete)

    def update_data_length(self, data_length: int = None) -> EventWaitable[Peripheral, DataLengthUpdatedEventArgs]:
        """
        Starts the process which updates the link layer data length to the optimal value given the MTU.
        For best results call this method after the MTU is set to the desired size.

        :param data_length: Optional value to override the data length to.
                            If not provided, uses the optimal value based on the current MTU
        :return: A waitable that will trigger when the process finishes
        """
        if data_length is not None:
            if data_length > DLE_MAX or data_length < DLE_MIN:
                raise ValueError(f"Data length must be between {DLE_MIN} and {DLE_MAX} (inclusive)")
        else:
            data_length = self.mtu_size + DLE_OVERHEAD

        params = BLEGapDataLengthParams(data_length, data_length)
        self._ble_device.ble_driver.ble_gap_data_length_update(self.conn_handle, params)
        return EventWaitable(self._on_data_length_updated)

    def update_phy(self, phy: Phy = None) -> EventWaitable[Peer, PhyUpdatedEventArgs]:
        """
        Performs the PHY update procedure, negotiating a new PHY (1Mbps, 2Mbps, or coded PHY)
        to use for the connection. Performing this procedure does not guarantee that the PHY
        will change based on what the peer supports.

        :param phy: Optional PHY to use. If None, uses the :attr:`preferred_phy` attribute.
                    If not None, the preferred PHY is updated to this value.
        :return: An event waitable that triggers when the phy process completes
        """
        if phy is None:
            phy = self._preferred_phy
        else:
            self._preferred_phy = phy
        self._ble_device.ble_driver.ble_gap_phy_update(self.conn_handle, phy, phy)
        return EventWaitable(self._on_phy_updated)

    def discover_services(self) -> EventWaitable[Peer, DatabaseDiscoveryCompleteEventArgs]:
        """
        Starts the database discovery process of the peer. This will discover all services, characteristics, and
        descriptors on the peer's database.

        :return: a Waitable that will trigger when service discovery is complete
        """
        self._discoverer.start()
        return EventWaitable(self._discoverer.on_discovery_complete)

    """
    Internal Library Methods
    """

    def peer_connected(self, conn_handle, peer_address, connection_params):
        """
        Internal method called when the peer connects to set up the object.

        **Should not be called by the user**
        """
        self.conn_handle = conn_handle
        self.peer_address = peer_address
        self._mtu_size = MTU_SIZE_DEFAULT
        self._negotiated_mtu_size = None
        self._disconnect_waitable = DisconnectionWaitable(self)
        self.connection_state = PeerState.CONNECTED
        self._current_connection_params = ActiveConnectionParameters(connection_params)

        self._ble_device.ble_driver.event_subscribe(self._on_disconnect_event, nrf_events.GapEvtDisconnected)
        self.driver_event_subscribe(self._on_connection_param_update, nrf_events.GapEvtConnParamUpdate, nrf_events.GapEvtConnParamUpdateRequest)
        self.driver_event_subscribe(self._on_mtu_exchange_request, nrf_events.GattsEvtExchangeMtuRequest)
        self.driver_event_subscribe(self._on_mtu_exchange_response, nrf_events.GattcEvtMtuExchangeResponse)
        self.driver_event_subscribe(self._on_data_length_update_request, nrf_events.GapEvtDataLengthUpdateRequest)
        self.driver_event_subscribe(self._on_data_length_update, nrf_events.GapEvtDataLengthUpdate)
        self.driver_event_subscribe(self._on_phy_update_request, nrf_events.GapEvtPhyUpdateRequest)
        self.driver_event_subscribe(self._on_phy_update, nrf_events.GapEvtPhyUpdate)
        self._on_connect.notify(self)

    def _check_driver_event_connection_handle_wrapper(self, func):
        def wrapper(driver, event):
            if self.connected and self.conn_handle == event.conn_handle:
                func(driver, event)
        return wrapper

    def driver_event_subscribe(self, handler, *event_types):
        """
        Internal method that subscribes handlers to NRF Driver events directed at this peer.
        Handlers are automatically unsubscribed once the peer disconnects.

        :param handler: The handler to subscribe
        :param event_types: The NRF Driver event types to subscribe to
        """
        wrapped_handler = self._check_driver_event_connection_handle_wrapper(handler)
        with self._connection_handler_lock:
            if handler not in self._connection_based_driver_event_handlers:
                self._connection_based_driver_event_handlers[handler] = wrapped_handler
                self._ble_device.ble_driver.event_subscribe(wrapped_handler, *event_types)

    def driver_event_unsubscribe(self, handler, *event_types):
        """
        Internal method that unsubscribes handlers from NRF Driver events.

        :param handler: The handler to unsubscribe
        :param event_types: The event types to unsubscribe from
        """
        with self._connection_handler_lock:
            wrapped_handler = self._connection_based_driver_event_handlers.get(handler, None)
            logger.debug("Unsubscribing {} ({})".format(handler, wrapped_handler))
            if wrapped_handler:
                self._ble_device.ble_driver.event_unsubscribe(wrapped_handler, *event_types)
                del self._connection_based_driver_event_handlers[handler]

    """
    Private Methods
    """

    def _on_disconnect_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if not self.connected or self.conn_handle != event.conn_handle:
            return
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.connection_state = PeerState.DISCONNECTED
        self._disconnection_reason = event.reason
        self._on_disconnect.notify(self, DisconnectionEventArgs(event.reason))

        with self._connection_handler_lock:
            for handler in self._connection_based_driver_event_handlers.values():
                self._ble_device.ble_driver.event_unsubscribe_all(handler)
            self._connection_based_driver_event_handlers = {}
        self._ble_device.ble_driver.event_unsubscribe(self._on_disconnect_event)
        self._ble_device.ble_driver.event_unsubscribe(self._on_connection_param_update)

    def _on_connection_param_update(self, driver, event):
        """
        :type event: nrf_events.GapEvtConnParamUpdate
        """
        if not self.connected or self.conn_handle != event.conn_handle:
            return
        if isinstance(event, nrf_events.GapEvtConnParamUpdateRequest):
            logger.debug("[{}] Conn Params updating to {}".format(self.conn_handle, self._preferred_connection_params))
            self._ble_device.ble_driver.ble_gap_conn_param_update(self.conn_handle, self._preferred_connection_params)
        else:
            logger.debug("[{}] Updated to {}".format(self.conn_handle, event.conn_params))
            self._current_connection_params = ActiveConnectionParameters(event.conn_params)

    def _validate_mtu_size(self, mtu_size):
        if mtu_size < MTU_SIZE_MINIMUM:
            raise ValueError("Invalid MTU size {}. "
                             "Minimum is {}".format(mtu_size, MTU_SIZE_MINIMUM))
        if mtu_size > self.max_mtu_size:
            raise ValueError("Invalid MTU size {}. "
                             "Maximum configured in the BLE device: {}".format(mtu_size, self._ble_device.max_mtu_size))

    def _resolve_mtu_exchange(self, our_mtu, peer_mtu):
        previous_mtu_size = self._mtu_size
        self._mtu_size = max(min(our_mtu, peer_mtu), MTU_SIZE_MINIMUM)
        logger.debug("[{}] MTU Exchange - Ours: {}, Peers: {}, Effective: {}".format(self.conn_handle,
                                                                                     our_mtu, peer_mtu, self._mtu_size))
        self._on_mtu_size_updated.notify(self, MtuSizeUpdatedEventArgs(previous_mtu_size, self._mtu_size))

        return previous_mtu_size, self._mtu_size

    def _on_mtu_exchange_request(self, driver, event):
        if self._negotiated_mtu_size is None:
            self._negotiated_mtu_size = self.preferred_mtu_size

        self._ble_device.ble_driver.ble_gatts_exchange_mtu_reply(self.conn_handle, self._negotiated_mtu_size)
        self._resolve_mtu_exchange(self._negotiated_mtu_size, event.client_mtu)

    def _on_mtu_exchange_response(self, driver, event):
        previous, current = self._resolve_mtu_exchange(self._negotiated_mtu_size, event.server_mtu)
        self._on_mtu_exchange_complete.notify(self, MtuSizeUpdatedEventArgs(previous, current))

    def _on_data_length_update_request(self, driver, event):
        self._ble_device.ble_driver.ble_gap_data_length_update(self.conn_handle)

    def _on_data_length_update(self, driver, event):
        event_args = DataLengthUpdatedEventArgs(event.max_tx_octets, event.max_rx_octets,
                                                event.max_tx_time_us, event.max_rx_time_us)
        self._on_data_length_updated.notify(self, event_args)

    def _on_phy_update_request(self, driver, event):
        self._ble_device.ble_driver.ble_gap_phy_update(self.conn_handle)

    def _on_phy_update(self, driver, event: nrf_events.GapEvtPhyUpdate):
        self._current_phy = Phy(event.rx_phy) | Phy(event.tx_phy)
        self._on_phy_updated.notify(self, PhyUpdatedEventArgs(event.status, self._current_phy))

    def __nonzero__(self):
        return self.conn_handle != BLE_CONN_HANDLE_INVALID

    def __bool__(self):
        return self.__nonzero__()


class Peripheral(Peer):
    """
    Object which represents a BLE-connected device that is acting as a peripheral/server (local device is client/central)
    """
    def __init__(self, ble_device, peer_address,
                 connection_params=DEFAULT_CONNECTION_PARAMS,
                 security_params=DEFAULT_SECURITY_PARAMS,
                 name="",
                 write_no_resp_queue_size=1):
        super(Peripheral, self).__init__(ble_device, nrf_events.BLEGapRoles.central, connection_params,
                                         security_params, name, write_no_resp_queue_size)
        self.peer_address = peer_address
        self.connection_state = PeerState.CONNECTING


class Client(Peer):
    """
    Object which represents a BLE-connected device that is acting as a client/central (local device is peripheral/server)
    """
    def __init__(self, ble_device,
                 connection_params=DEFAULT_CONNECTION_PARAMS,
                 security_params=DEFAULT_SECURITY_PARAMS,
                 name="",
                 write_no_resp_queue_size=1):
        super(Client, self).__init__(ble_device, nrf_events.BLEGapRoles.periph, connection_params,
                                     security_params, name, write_no_resp_queue_size)
        self._first_connection = True

    def peer_connected(self, conn_handle, peer_address, connection_params):
        # Recreate the DB and discovery class since the client object persists across disconnects
        if not self._first_connection:
            self._db = gattc.GattcDatabase(self._ble_device, self)
            self._discoverer = service_discovery.DatabaseDiscoverer(self._ble_device, self)
        self._first_connection = False
        self._name = ""
        super(Client, self).peer_connected(conn_handle, peer_address, connection_params)
