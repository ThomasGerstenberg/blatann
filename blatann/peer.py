import enum
from blatann.nrf.nrf_types.enums import BLE_CONN_HANDLE_INVALID
from blatann.nrf import nrf_events
from blatann.event_type import Event, EventSource
from blatann.waitables import connection_waitable


class PeerState(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class ConnectionParameters(object):
    def __init__(self, min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency=0):
        self.min_conn_interval_ms = min_conn_interval_ms
        self.max_conn_interval_ms = max_conn_interval_ms
        self.slave_latency = slave_latency
        self.timeout_ms = timeout_ms


DEFAULT_CONNECTION_PARAMS = ConnectionParameters(15, 30, 4000, 0)


class Peer(object):
    BLE_CONN_HANDLE_INVALID = BLE_CONN_HANDLE_INVALID

    def __init__(self, ble_device, role, connection_params=DEFAULT_CONNECTION_PARAMS):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.address = "",
        self.connection_state = PeerState.DISCONNECTED
        self._on_disconnect = EventSource("On Disconnect")
        self._ble_device = ble_device
        self._connection_params = connection_params

    @property
    def on_disconnect(self):
        return self._on_disconnect

    def disconnect(self, status_code=nrf_events.BLEHci.remote_user_terminated_connection):
        if self.connection_state != PeerState.CONNECTED:
            return
        self._ble_device.ble_driver.ble_gap_disconnect(self.conn_handle, status_code)
        return connection_waitable.DisconnectionWaitable(self)

    def set_connection_parameters(self, connection_params):
        self._connection_params = connection_params
        if self.connection_state != PeerState.CONNECTED:
            return
        # Do stuff to set the connection parameters

    def peer_connected(self, conn_handle, peer_address):
        self.conn_handle = conn_handle
        self.address = peer_address
        self.connection_state = PeerState.CONNECTED
        self._ble_device.ble_driver.event_subscribe(self._on_disconnect_event, nrf_events.GapEvtDisconnected)

    def _on_disconnect_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if self.connection_state != PeerState.CONNECTED:
            return
        if event.conn_handle == self.conn_handle:
            self.conn_handle = BLE_CONN_HANDLE_INVALID
            self.connection_state = PeerState.DISCONNECTED
            self._ble_device.ble_driver.event_unsubscribe(self._on_disconnect_event, nrf_events.GapEvtDisconnected)
            self._on_disconnect.notify(self)

    def __nonzero__(self):
        return self.conn_handle != BLE_CONN_HANDLE_INVALID

    def __bool__(self):
        return self.__nonzero__()


class Peripheral(Peer):
    def __init__(self, ble_device, connection_params=DEFAULT_CONNECTION_PARAMS):
        super(Peripheral, self).__init__(ble_device, nrf_events.BLEGapRoles.central, connection_params)


class Client(Peer):
    def __init__(self, ble_device, connection_params=DEFAULT_CONNECTION_PARAMS):
        super(Client, self).__init__(ble_device, nrf_events.BLEGapRoles.periph, connection_params)
