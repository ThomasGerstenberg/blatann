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
        return self._repr_format(sec_mode=self.sec_mode, sec_level=self.sec_level, encr_key_size=self.encr_key_size)


class GapEvtSecInfoRequest(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_SEC_INFO_REQUEST

    def __init__(self, conn_handle, peer_addr, master_id, enc_info, id_info, sign_info):
        super(GapEvtSecInfoRequest, self).__init__(conn_handle)
        self.peer_addr = peer_addr
        self.master_id = master_id
        self.enc_info = enc_info
        self.id_info = id_info
        self.sign_info = sign_info

    @classmethod
    def from_c(cls, event):
        sec_info = event.evt.gap_evt.params.sec_info_request
        conn_handle = event.evt.gap_evt.conn_handle
        peer_addr = BLEGapAddr.from_c(sec_info.peer_addr)
        master_id = BLEGapMasterId.from_c(sec_info.master_id)

        return cls(conn_handle, peer_addr, master_id, sec_info.enc_info, sec_info.id_info, sec_info.sign_info)

    def __repr__(self):
        return self._repr_format(peer_addr=self.peer_addr, master_id=self.master_id, enc=self.enc_info,
                                 id=self.id_info, sign=self.sign_info)


class GapEvtSecRequest(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_SEC_REQUEST

    def __init__(self, conn_handle, bond, mitm, lesc, keypress):
        super(GapEvtSecRequest, self).__init__(conn_handle)
        self.bond = bond
        self.mitm = mitm
        self.lesc = lesc
        self.keypress = keypress

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gap_evt.conn_handle
        sec_req = event.evt.gap_evt.params.sec_request
        bond = bool(sec_req.bond)
        mitm = bool(sec_req.mitm)
        lesc = bool(sec_req.lesc)
        keypress = bool(sec_req.keypress)

        return cls(conn_handle, bond, mitm, lesc, keypress)

    def __repr__(self):
        return self._repr_format(bond=self.bond, mitm=self.mitm, lesc=self.lesc, keypress=self.keypress)


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
        return self._repr_format(sec_params=self.sec_params)


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
        return self._repr_format(key_type=self.key_type)


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
        return self._repr_format(auth_status=self.auth_status, error_src=self.error_src, bonded=self.bonded,
                                 sm1_levels=self.sm1_levels, sm2_levels=self.sm2_levels,
                                 kdist_own=self.kdist_own, kdist_peer=self.kdist_peer)


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
        return self._repr_format(passkey=self.passkey, match_request=self.match_request)


class GapEvtLescDhKeyRequest(GapEvtSec):
    evt_id = driver.BLE_GAP_EVT_LESC_DHKEY_REQUEST

    def __init__(self, conn_handle, remote_public_key, oob_required):
        super(GapEvtLescDhKeyRequest, self).__init__(conn_handle)
        self.remote_public_key = remote_public_key  # type: BLEGapDhKey
        self.oob_required = oob_required

    @classmethod
    def from_c(cls, event):
        dh_key_request = event.evt.gap_evt.params.lesc_dhkey_request
        remote_pk = BLEGapPublicKey.from_c(dh_key_request.p_pk_peer)
        oob_required = bool(dh_key_request.oobd_req)
        return cls(conn_handle=event.evt.gap_evt.conn_handle,
                   remote_public_key=remote_pk,
                   oob_required=oob_required)

    def __repr__(self):
        return self._repr_format(remote_key=self.remote_public_key, oob=self.oob_required)
