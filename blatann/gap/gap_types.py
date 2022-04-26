import enum
from blatann.nrf import nrf_events, nrf_types


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

    def __str__(self):
        return (f"ConnectionParams([{self.min_conn_interval_ms}-{self.max_conn_interval_ms}] ms, "
                f"timeout: {self.conn_sup_timeout_ms} ms, latency: {self.slave_latency}")

    def __repr__(self):
        return str(self)


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

    def __eq__(self, other):
        if not isinstance(other, ActiveConnectionParameters):
            return False
        return (self._interval_ms == other._interval_ms and
                self._slave_latency == other._slave_latency and
                self._timeout_ms == other._timeout_ms)

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
