from enum import Enum
import logging
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_types.enums import *


logger = logging.getLogger(__name__)


class BLEGapSecMode(object):
    def __init__(self, sec_mode, level):
        self.sm = sec_mode
        self.level = level

    def to_c(self):
        params = driver.ble_gap_conn_sec_mode_t()
        params.sm = self.sm
        params.lv = self.level
        return params

    @classmethod
    def from_c(cls, params):
        return cls(params.sm, params.lv)


class BLEGapSecModeType(object):
    NO_ACCESS = BLEGapSecMode(0, 0)
    OPEN = BLEGapSecMode(1, 1)
    ENCRYPTION = BLEGapSecMode(1, 2)
    MITM = BLEGapSecMode(1, 3)
    LESC_MITM = BLEGapSecMode(1, 4)
    SIGN_OR_ENCRYPT = BLEGapSecMode(2, 1)
    SIGN_OR_ENCRYPT_MITM = BLEGapSecMode(2, 2)


class BLEGapSecLevels(object):
    def __init__(self, lv1, lv2, lv3, lv4):
        self.lv1 = lv1
        self.lv2 = lv2
        self.lv3 = lv3
        self.lv4 = lv4

    @classmethod
    def from_c(cls, sec_level):
        return cls(lv1=sec_level.lv1,
                   lv2=sec_level.lv2,
                   lv3=sec_level.lv3,
                   lv4=sec_level.lv4)

    def to_c(self):
        sec_level = driver.ble_gap_sec_levels_t()
        sec_level.lv1 = self.lv1
        sec_level.lv2 = self.lv2
        sec_level.lv3 = self.lv3
        sec_level.lv4 = self.lv4
        return sec_level

    def __repr__(self):
        return "{}(lv1={!r}, lv2={!r}, lv3={!r}, lv4={!r})".format(self.__class__.__name__,
                                                                   self.lv1, self.lv2, self.lv3, self.lv4)


class BLEGapSecKeyDist(object):
    def __init__(self, enc_key=False, id_key=False, sign_key=False, link_key=False):
        self.enc_key = enc_key
        self.id_key = id_key
        self.sign_key = sign_key
        self.link_key = link_key

    @classmethod
    def from_c(cls, kdist):
        return cls(enc_key=kdist.enc,
                   id_key=kdist.id,
                   sign_key=kdist.sign,
                   link_key=kdist.link)

    def to_c(self):
        kdist = driver.ble_gap_sec_kdist_t()
        kdist.enc = self.enc_key
        kdist.id = self.id_key
        kdist.sign = self.sign_key
        kdist.link = self.link_key
        return kdist

    def __repr__(self):
        return "{}(enc_key={!r}, id_key={!r}, sign_key={!r}, link_key={!r})".format(self.__class__.__name__,
                                                                                    self.enc_key, self.id_key,
                                                                                    self.sign_key,
                                                                                    self.link_key)


class BLEGapSecParams(object):
    def __init__(self, bond, mitm, le_sec_pairing, keypress_noti, io_caps, oob, min_key_size, max_key_size, kdist_own,
                 kdist_peer):
        self.bond = bond
        self.mitm = mitm
        self.le_sec_pairing = le_sec_pairing
        self.keypress_noti = keypress_noti
        self.io_caps = io_caps
        self.oob = oob
        self.min_key_size = min_key_size
        self.max_key_size = max_key_size
        self.kdist_own = kdist_own
        self.kdist_peer = kdist_peer

    @classmethod
    def from_c(cls, sec_params):
        return cls(bond=sec_params.bond,
                   mitm=sec_params.mitm,
                   le_sec_pairing=sec_params.lesc,
                   keypress_noti=sec_params.keypress,
                   io_caps=sec_params.io_caps,
                   oob=sec_params.oob,
                   min_key_size=sec_params.min_key_size,
                   max_key_size=sec_params.max_key_size,
                   kdist_own=BLEGapSecKeyDist.from_c(sec_params.kdist_own),
                   kdist_peer=BLEGapSecKeyDist.from_c(sec_params.kdist_peer))

    def to_c(self):
        sec_params = driver.ble_gap_sec_params_t()
        sec_params.bond = self.bond
        sec_params.mitm = self.mitm
        sec_params.lesc = self.le_sec_pairing
        sec_params.keypress = self.keypress_noti
        sec_params.io_caps = self.io_caps
        sec_params.oob = self.oob
        sec_params.min_key_size = self.min_key_size
        sec_params.max_key_size = self.max_key_size
        sec_params.kdist_own = self.kdist_own.to_c()
        sec_params.kdist_peer = self.kdist_peer.to_c()
        return sec_params

    def __repr__(self):
        return "{}(bond={!r}, mitm={!r}, le_sec_pairing={!r}, keypress_noti={!r}, io_caps={!r}, oob={!r}, " \
               "min_key_size={!r}, max_key_size={!r}, kdist_own={!r}, kdist_peer={!r})".format(self.__class__.__name__,
                                                                                               self.bond, self.mitm,
                                                                                               self.le_sec_pairing,
                                                                                               self.keypress_noti,
                                                                                               self.io_caps,
                                                                                               self.oob,
                                                                                               self.min_key_size,
                                                                                               self.max_key_size,
                                                                                               self.kdist_own,
                                                                                               self.kdist_peer)


class BLEGapSecKeyset(object):
    def __init__(self):
        self.sec_keyset = driver.ble_gap_sec_keyset_t()
        keys_own = driver.ble_gap_sec_keys_t()
        self.sec_keyset.keys_own = keys_own

        keys_peer = driver.ble_gap_sec_keys_t()
        keys_peer.p_enc_key = driver.ble_gap_enc_key_t()
        keys_peer.p_enc_key.enc_info = driver.ble_gap_enc_info_t()
        keys_peer.p_enc_key.master_id = driver.ble_gap_master_id_t()
        keys_peer.p_id_key = driver.ble_gap_id_key_t()
        keys_peer.p_id_key.id_info = driver.ble_gap_irk_t()
        keys_peer.p_id_key.id_addr_info = driver.ble_gap_addr_t()
        # keys_peer.p_sign_key            = driver.ble_gap_sign_info_t()
        # keys_peer.p_pk                  = driver.ble_gap_lesc_p256_pk_t()
        self.sec_keyset.keys_peer = keys_peer

    @classmethod
    def from_c(cls, sec_params):
        raise NotImplemented()

    def to_c(self):
        return self.sec_keyset
