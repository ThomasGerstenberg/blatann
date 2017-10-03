from enum import IntEnum

from blatann.nrf.nrf_types import *
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_events.gap_events import GapEvt


class GapEvtSec(GapEvt):
    pass


class GapEvtConnSecUpdate(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_CONN_SEC_UPDATE

    def __init__(self, conn_handle, sec_mode, sec_level, encr_key_size):
        super(GapEvtConnSecUpdate, self).__init__(conn_handle)
        self.sec_mode = sec_mode
        self.sec_level = sec_level
        self.encr_key_size = encr_key_size

    @classmethod
    def from_c(cls, event):
        conn_sec = event.evt.gap_evt.params.conn_sec_update.conn_sec
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   sec_mode=conn_sec.sec_mode.sm,
                   sec_level=conn_sec.sec_mode.lv,
                   encr_key_size=conn_sec.encr_key_size)

    def __repr__(self):
        return "{}(conn_handle={!r}, sec_mode={!r}, sec_level={!r}, encr_key_size={!r})".format(self.__class__.__name__,
                                                                                                self.conn_handle,
                                                                                                self.sec_mode,
                                                                                                self.sec_level,
                                                                                                self.encr_key_size)


class GapEvtSecParamsRequest(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_SEC_PARAMS_REQUEST

    def __init__(self, conn_handle, sec_params):
        super(GapEvtSecParamsRequest, self).__init__(conn_handle)
        self.sec_params = sec_params

    @classmethod
    def from_c(cls, event):
        sec_params = event.evt.gap_evt.params.sec_params_request.peer_params
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   sec_params=BLEGapSecParams.from_c(sec_params))

    def __repr__(self):
        return "{}(conn_handle={!r}, sec_params={!r})".format(self.__class__.__name__, self.conn_handle,
                                                              self.sec_params)


class GapEvtAuthKeyRequest(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_AUTH_KEY_REQUEST

    def __init__(self, conn_handle, key_type):
        super(GapEvtAuthKeyRequest, self).__init__(conn_handle)
        self.key_type = key_type

    @classmethod
    def from_c(cls, event):
        auth_key_request = event.evt.gap_evt.params.auth_key_request
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   key_type=BLEGapAuthKeyType(auth_key_request.key_type))

    def __repr__(self):
        return "{}(conn_handle={!r}, key_type={!r})".format(self.__class__.__name__, self.conn_handle, self.key_type)


class GapEvtAuthStatus(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_AUTH_STATUS

    def __init__(self, conn_handle, auth_status, error_src, bonded, sm1_levels, sm2_levels, kdist_own, kdist_peer):
        super(GapEvtAuthStatus, self).__init__(conn_handle)
        self.auth_status = auth_status
        self.error_src = error_src
        self.bonded = bonded
        self.sm1_levels = sm1_levels
        self.sm2_levels = sm2_levels
        self.kdist_own = kdist_own
        self.kdist_peer = kdist_peer

    @classmethod
    def from_c(cls, event):
        auth_status = event.evt.gap_evt.params.auth_status
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   auth_status=BLEGapSecStatus(auth_status.auth_status),
                   error_src=auth_status.error_src,
                   bonded=auth_status.bonded,
                   sm1_levels=BLEGapSecLevels.from_c(auth_status.sm1_levels),
                   sm2_levels=BLEGapSecLevels.from_c(auth_status.sm2_levels),
                   kdist_own=BLEGapSecKeyDist.from_c(auth_status.kdist_own),
                   kdist_peer=BLEGapSecKeyDist.from_c(auth_status.kdist_peer))

    def __repr__(self):
        return "{}(conn_handle={!r}, auth_status={!r}, error_src={!r}, bonded={!r}, sm1_levels={!r}, sm2_levels={!r}, " \
               "kdist_own={!r}, kdist_peer={!r})".format(self.__class__.__name__, self.conn_handle, self.auth_status,
                                                         self.error_src, self.bonded,
                                                         self.sm1_levels, self.sm2_levels, self.kdist_own,
                                                         self.kdist_peer)


class GapEvtPasskeyDisplay(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_PASSKEY_DISPLAY

    def __init__(self, conn_handle, passkey, match_request):
        super(GapEvtPasskeyDisplay, self).__init__(conn_handle)
        self.passkey = passkey
        self.match_request = match_request

    @classmethod
    def from_c(cls, event):
        passkey_display = event.evt.gap_evt.params.passkey_display
        passkey = "".join(chr(c) for c in util.uint8_array_to_list(passkey_display.passkey, 6))
        match_request = bool(passkey_display.match_request)
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   passkey=passkey,
                   match_request=match_request)

    def __repr__(self):
        return "{}(conn_handle={!r}, passkey={!r}, match_request={!r})".format(self.__class__.__name__,
                                                                               self.conn_handle, self.passkey,
                                                                               self.match_request)
