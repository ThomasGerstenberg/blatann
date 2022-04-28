from enum import IntEnum

from blatann.nrf.nrf_types import *
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_events.generic_events import BLEEvent


class GapEvt(BLEEvent):
    pass


class GapEvtRssiChanged(GapEvt):
    evt_id = driver.BLE_GAP_EVT_RSSI_CHANGED

    def __init__(self, conn_handle, rssi):
        super(GapEvtRssiChanged, self).__init__(conn_handle)
        self.rssi = rssi

    @classmethod
    def from_c(cls, event):
        rssi = event.evt.gap_evt.params.rssi_changed.rssi
        return cls(conn_handle=event.evt.gap_evt.conn_handle, rssi=rssi)

    def __repr__(self):
        return self._repr_format(rssi=self.rssi)


class GapEvtAdvReport(GapEvt):
    evt_id = driver.BLE_GAP_EVT_ADV_REPORT

    def __init__(self, conn_handle, peer_addr, rssi, adv_type, adv_data):
        # TODO: What? Adv event has conn_handle? Does not compute
        super(GapEvtAdvReport, self).__init__(conn_handle)
        self.peer_addr = peer_addr
        self.rssi = rssi
        self.adv_type = adv_type
        self.adv_data = adv_data

    def get_device_name(self):
        dev_name_list = []
        if BLEAdvData.Types.complete_local_name in self.adv_data.records:
            dev_name_list = self.adv_data.records[BLEAdvData.Types.complete_local_name]
        elif BLEAdvData.Types.short_local_name in self.adv_data.records:
            dev_name_list = self.adv_data.records[BLEAdvData.Types.short_local_name]
        return "".join(map(chr, dev_name_list))

    @classmethod
    def from_c(cls, event):
        adv_report_evt = event.evt.gap_evt.params.adv_report

        if not adv_report_evt.scan_rsp:
            adv_type = BLEGapAdvType(adv_report_evt.type)
        else:
            adv_type = BLEGapAdvType.scan_response

        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   peer_addr=BLEGapAddr.from_c(adv_report_evt.peer_addr),
                   rssi=adv_report_evt.rssi,
                   adv_type=adv_type,
                   adv_data=BLEAdvData.from_c(adv_report_evt))

    def __repr__(self):
        return "{}(conn_handle={!r}, peer_addr={!r}, rssi={!r}, adv_type={!r}, adv_data={!r})".format(
            self.__class__.__name__, self.conn_handle,
            self.peer_addr, self.rssi, self.adv_type, self.adv_data)


class GapEvtTimeout(GapEvt):
    evt_id = driver.BLE_GAP_EVT_TIMEOUT

    def __init__(self, conn_handle, src):
        super(GapEvtTimeout, self).__init__(conn_handle)
        self.src = src

    @classmethod
    def from_c(cls, event):
        timeout_evt = event.evt.gap_evt.params.timeout
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   src=BLEGapTimeoutSrc(timeout_evt.src))

    def __repr__(self):
        return "{}(conn_handle={!r}, src={!r})".format(self.__class__.__name__, self.conn_handle, self.src)


class GapEvtConnParamUpdateRequest(GapEvt):
    evt_id = driver.BLE_GAP_EVT_CONN_PARAM_UPDATE_REQUEST

    def __init__(self, conn_handle, conn_params):
        super(GapEvtConnParamUpdateRequest, self).__init__(conn_handle)
        self.conn_params = conn_params

    @classmethod
    def from_c(cls, event):
        conn_params = event.evt.gap_evt.params.conn_param_update_request.conn_params
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   conn_params=BLEGapConnParams.from_c(conn_params))

    def __repr__(self):
        return "{}(conn_handle={!r}, conn_params={!r})".format(self.__class__.__name__, self.conn_handle,
                                                               self.conn_params)


class GapEvtConnParamUpdate(GapEvt):
    evt_id = driver.BLE_GAP_EVT_CONN_PARAM_UPDATE

    def __init__(self, conn_handle, conn_params):
        super(GapEvtConnParamUpdate, self).__init__(conn_handle)
        self.conn_params = conn_params

    @classmethod
    def from_c(cls, event):
        conn_params = event.evt.gap_evt.params.conn_param_update.conn_params
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   conn_params=BLEGapConnParams.from_c(conn_params))

    def __repr__(self):
        return "{}(conn_handle={!r}, conn_params={})".format(self.__class__.__name__, self.conn_handle,
                                                             self.conn_params)


class GapEvtConnected(GapEvt):
    evt_id = driver.BLE_GAP_EVT_CONNECTED

    def __init__(self, conn_handle, peer_addr, role, conn_params):
        super(GapEvtConnected, self).__init__(conn_handle)
        self.peer_addr = peer_addr
        self.role = role
        self.conn_params = conn_params

    @classmethod
    def from_c(cls, event):
        connected_evt = event.evt.gap_evt.params.connected
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   peer_addr=BLEGapAddr.from_c(connected_evt.peer_addr),
                   role=BLEGapRoles(connected_evt.role),
                   conn_params=BLEGapConnParams.from_c(connected_evt.conn_params))

    def __repr__(self):
        return "{}(conn_handle={!r}, peer_addr={!r}, role={!r}, conn_params={})".format(self.__class__.__name__,
                                                                                        self.conn_handle,
                                                                                        self.peer_addr, self.role,
                                                                                        self.conn_params)


class GapEvtDisconnected(GapEvt):
    evt_id = driver.BLE_GAP_EVT_DISCONNECTED

    def __init__(self, conn_handle, reason):
        super(GapEvtDisconnected, self).__init__(conn_handle)
        self.reason = reason

    @classmethod
    def from_c(cls, event):
        disconnected_evt = event.evt.gap_evt.params.disconnected
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   reason=BLEHci(disconnected_evt.reason))

    def __repr__(self):
        return self._repr_format(reason=self.reason)


class GapEvtDataLengthUpdate(GapEvt):
    evt_id = driver.BLE_GAP_EVT_DATA_LENGTH_UPDATE

    def __init__(self, conn_handle, max_tx_octets, max_rx_octets, max_tx_time_us, max_rx_time_us):
        super(GapEvtDataLengthUpdate, self).__init__(conn_handle)
        self.max_tx_octets = max_tx_octets
        self.max_rx_octets = max_rx_octets
        self.max_tx_time_us = max_tx_time_us
        self.max_rx_time_us = max_rx_time_us

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gap_evt.conn_handle
        params = event.evt.gap_evt.params.data_length_update.effective_params
        return cls(conn_handle, params.max_tx_octets, params.max_rx_octets, params.max_tx_time_us, params.max_rx_time_us)

    def __repr__(self):
        return self._repr_format(max_tx_octets=self.max_tx_octets, max_rx_octets=self.max_rx_octets,
                                 max_tx_time_us=self.max_tx_time_us, max_rx_time_us=self.max_rx_time_us)


class GapEvtDataLengthUpdateRequest(GapEvt):
    evt_id = driver.BLE_GAP_EVT_DATA_LENGTH_UPDATE_REQUEST

    def __init__(self, conn_handle, max_tx_octets, max_rx_octets, max_tx_time_us, max_rx_time_us):
        super(GapEvtDataLengthUpdateRequest, self).__init__(conn_handle)
        self.max_tx_octets = max_tx_octets
        self.max_rx_octets = max_rx_octets
        self.max_tx_time_us = max_tx_time_us
        self.max_rx_time_us = max_rx_time_us

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gap_evt.conn_handle
        params = event.evt.gap_evt.params.data_length_update_request.peer_params
        return cls(conn_handle, params.max_tx_octets, params.max_rx_octets, params.max_tx_time_us, params.max_rx_time_us)

    def __repr__(self):
        return self._repr_format(max_tx_octets=self.max_tx_octets, max_rx_octets=self.max_rx_octets,
                                 max_tx_time_us=self.max_tx_time_us, max_rx_time_us=self.max_rx_time_us)


class GapEvtPhyUpdate(GapEvt):
    evt_id = driver.BLE_GAP_EVT_PHY_UPDATE

    def __init__(self, conn_handle, status, tx_phy, rx_phy):
        super(GapEvtPhyUpdate, self).__init__(conn_handle)
        self.status = status
        self.tx_phy = tx_phy
        self.rx_phy = rx_phy

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gap_evt.conn_handle
        params = event.evt.gap_evt.params.phy_update
        try:
            status = BLEHci(params.status)
        except:
            status = params.status
        return cls(conn_handle, status, BLEGapPhy(params.tx_phy), BLEGapPhy(params.rx_phy))

    def __repr__(self):
        return self._repr_format(status=self.status, tx_phy=self.tx_phy, rx_phy=self.rx_phy)


class GapEvtPhyUpdateRequest(GapEvt):
    evt_id = driver.BLE_GAP_EVT_PHY_UPDATE_REQUEST

    def __init__(self, conn_handle, tx_phy, rx_phy):
        super(GapEvtPhyUpdateRequest, self).__init__(conn_handle)
        self.tx_phy = tx_phy
        self.rx_phy = rx_phy

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gap_evt.conn_handle
        params = event.evt.gap_evt.params.phy_update_request.peer_preferred_phys
        return cls(conn_handle, BLEGapPhy(params.tx_phys), BLEGapPhy(params.rx_phys))

    def __repr__(self):
        return self._repr_format(tx_phy=self.tx_phy, rx_phy=self.rx_phy)