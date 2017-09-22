import enum


class PeerState(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED_NOT_SECURE = 2
    CONNECTED_SECURE = 3


class Peer(object):
    def __init__(self):
        self.conn_handle = -1
        self.address = "",
        self.connection_state = PeerState.DISCONNECTED

    def peer_connecting(self):
        self.connection_state = PeerState.CONNECTING

    def peer_connected(self, conn_handle, peer_address):
        self.conn_handle = conn_handle
        self.address = peer_address
        self.connection_state = PeerState.CONNECTED_NOT_SECURE

    def peer_secured(self):
        self.connection_state = PeerState.CONNECTED_SECURE
