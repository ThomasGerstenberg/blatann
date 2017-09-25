import enum
from blatann.nrf.nrf_types.enums import BLE_CONN_HANDLE_INVALID


class PeerState(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class Peer(object):
    def __init__(self):
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.address = "",
        self.connection_state = PeerState.DISCONNECTED

    def peer_connecting(self):
        self.connection_state = PeerState.CONNECTING

    def peer_connected(self, conn_handle, peer_address):
        self.conn_handle = conn_handle
        self.address = peer_address
        self.connection_state = PeerState.CONNECTED

    def peer_disconnected(self):
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.connection_state = PeerState.DISCONNECTED
        self.address = ""

    def __nonzero__(self):
        return self.conn_handle != BLE_CONN_HANDLE_INVALID

    def __bool__(self):
        return self.__nonzero__()
