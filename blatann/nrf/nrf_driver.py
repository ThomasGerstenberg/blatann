#
# Copyright (c) 2016 Nordic Semiconductor ASA
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   3. Neither the name of Nordic Semiconductor ASA nor the names of other
#   contributors to this software may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
#   4. This software must only be used in or with a processor manufactured by Nordic
#   Semiconductor ASA, or in or with a processor manufactured by a third party that
#   is used in combination with a processor manufactured by Nordic Semiconductor.
#
#   5. Any software provided in binary or object form under this license must not be
#   reverse engineered, decompiled, modified and/or disassembled.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import atexit
import functools
import wrapt
import queue
import traceback
from threading import Thread, Lock, Event

from blatann.nrf.nrf_events import *
from blatann.nrf.nrf_types import *
from blatann.nrf.nrf_dll_load import driver
from pc_ble_driver_py.exceptions import NordicSemiException
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_types.config import BleEnableConfig, BleConnConfig

logger = logging.getLogger(__name__)

NoneType = type(None)


# TODO: Do we really want to raise exceptions all the time?
def NordicSemiErrorCheck(wrapped=None, expected=driver.NRF_SUCCESS):
    if wrapped is None:
        return functools.partial(NordicSemiErrorCheck, expected=expected)

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        logger.debug("[%s] %s%s", instance.serial_port, wrapped.__name__, args)
        result = wrapped(*args, **kwargs)
        if isinstance(result, (list, tuple)):
            err_code = result[0]
            result = result[1:]
            if len(result) == 1:
                result = result[0]
        else:
            err_code = result
            result = None

        if err_code != expected:
            try:
                err_string = 'Error code: {}'.format(NrfError(err_code))
            except ValueError:
                err_string = 'Error code: 0x{:04x}, {}'.format(err_code, err_code)
            raise NordicSemiException('Failed to {}. {}'.format(wrapped.__name__, err_string), err_code)
        return result

    return wrapper(wrapped)


class NrfDriverObserver(object):
    def on_driver_event(self, nrf_driver, event):
        pass


class NrfDriver(object):
    default_baud_rate = 1000000
    ATT_MTU_DEFAULT = driver.BLE_GATT_ATT_MTU_DEFAULT

    def __init__(self, serial_port, baud_rate=None, log_driver_comms=False):
        if baud_rate is None:
            baud_rate = self.default_baud_rate

        self._events = queue.Queue()
        self._event_thread = None
        self._event_loop = False
        self._event_stopped = Event()
        self.observers = []
        self.ble_enable_params = None
        self._event_observers = {}
        self._event_observer_lock = Lock()
        self._log_driver_comms = log_driver_comms
        self._serial_port = serial_port

        phy_layer = driver.sd_rpc_physical_layer_create_uart(serial_port,
                                                             baud_rate,
                                                             driver.SD_RPC_FLOW_CONTROL_NONE,
                                                             driver.SD_RPC_PARITY_NONE)
        link_layer = driver.sd_rpc_data_link_layer_create_bt_three_wire(phy_layer, 100)
        transport_layer = driver.sd_rpc_transport_layer_create(link_layer, 100)
        self.rpc_adapter = driver.sd_rpc_adapter_create(transport_layer)

    @property
    def serial_port(self):
        return self._serial_port

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def open(self):
        if self.is_open:
            logger.warning("Trying to open already opened driver")
            return driver.NRF_SUCCESS

        err_code = driver.sd_rpc_open(self.rpc_adapter,
                                      self._status_handler,
                                      self.ble_evt_handler,
                                      self._log_message_handler)

        if err_code == driver.NRF_SUCCESS:
            self._event_thread = Thread(target=self._event_handler, name="{}_Event".format(self._serial_port))
            # Note: We create a daemon thread and then register an exit handler
            #       to make sure this thread stops. This ensures that scripts that
            #       stop because of ctrl-c interrupt, compile errors or other problems
            #       do not keep hanging in the console, waiting for an infinite thread
            #       loop.
            atexit.register(self._event_thread_join)
            self._event_thread.daemon = True
            self._event_thread.start()
        return err_code

    def _event_thread_join(self):
        if self._event_thread is None:
            return
        self._event_loop = False
        self._event_stopped.wait(1)
        self._event_thread = None

    @property
    def is_open(self):
        return self._event_thread is not None

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def close(self):
        if not self.is_open:
            return driver.NRF_SUCCESS
        driver.sd_rpc_conn_reset(self.rpc_adapter, 0)
        retval = driver.sd_rpc_close(self.rpc_adapter)
        driver.sd_rpc_adapter_delete(self.rpc_adapter)
        self._event_thread_join()
        return retval

    def event_subscribe(self, handler, *event_types):
        for event_type in event_types:
            if not issubclass(event_type, BLEEvent):
                raise ValueError("Event type must be a valid BLEEvent class type. Got {}".format(event_type))
        with self._event_observer_lock:
            for event_type in event_types:
                # If event type not already in dict, create an empty list
                if event_type not in self._event_observers.keys():
                    self._event_observers[event_type] = []
                handlers = self._event_observers[event_type]
                if handler not in handlers:
                    handlers.append(handler)

    def event_unsubscribe(self, handler, *event_types):
        if not event_types:
            self.event_unsubscribe_all(handler)
            return

        with self._event_observer_lock:
            for event_type in event_types:
                handlers = self._event_observers.get(event_type, [])
                if handler in handlers:
                    handlers.remove(handler)

    def event_unsubscribe_all(self, handler):
        with self._event_observer_lock:
            for event_type, handlers in self._event_observers.items():
                if handler in handlers:
                    handlers.remove(handler)

    def observer_register(self, observer):
        with self._event_observer_lock:
            if observer not in self.observers:
                self.observers.append(observer)

    def observer_unregister(self, observer):
        with self._event_observer_lock:
            if observer in self.observers:
                self.observers.remove(observer)

    def ble_enable_params_setup(self):
        return BleEnableConfig()

    def adv_params_setup(self):
        return BLEGapAdvParams(interval_ms=40, timeout_s=180)

    def scan_params_setup(self):
        return BLEGapScanParams(interval_ms=200, window_ms=150, timeout_s=10)

    def conn_params_setup(self):
        return BLEGapConnParams(min_conn_interval_ms=15, max_conn_interval_ms=30,
                                conn_sup_timeout_ms=4000, slave_latency=0)

    def security_params_setup(self):
        return BLEGapSecParams(bond=True, mitm=True, le_sec_pairing=False, keypress_noti=False,
                               io_caps=BLEGapIoCaps.NONE, oob=False, min_key_size=8,max_key_size=16,
                               kdist_own=BLEGapSecKeyDist(), kdist_peer=BLEGapSecKeyDist(enc_key=True))

    """
    BLE Generic methods
    """
    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_conn_configure(self, conn_params):
        assert isinstance(conn_params, BleConnConfig)
        for tag, cfg in conn_params.get_configs():
            err = driver.sd_ble_cfg_set(self.rpc_adapter, tag, cfg, 0)
            if err != driver.NRF_SUCCESS:
                return err
        return driver.NRF_SUCCESS

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_enable(self, ble_enable_params=None):
        if not ble_enable_params:
            ble_enable_params = self.ble_enable_params_setup()
        assert isinstance(ble_enable_params, BleEnableConfig), 'Invalid argument type'
        self.ble_enable_params = ble_enable_params
        for tag, cfg in self.ble_enable_params.get_configs():
            err = driver.sd_ble_cfg_set(self.rpc_adapter, tag, cfg, 0)
            if err != driver.NRF_SUCCESS:
                return err

        return driver.sd_ble_enable(self.rpc_adapter, None)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_opt_set(self, ble_opt):
        assert isinstance(ble_opt, BleOption)
        opt = driver.ble_opt_t()
        sub_attr = opt
        path = ble_opt.path.split(".")
        for name in path[:-1]:
            sub_attr = getattr(sub_attr, name)
        setattr(sub_attr, path[-1], ble_opt.to_c())
        return driver.sd_ble_opt_set(self.rpc_adapter, ble_opt.option_flag, opt)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_user_mem_reply(self, conn_handle):
        return driver.sd_ble_user_mem_reply(self.rpc_adapter, conn_handle, None)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_vs_uuid_add(self, uuid_base):
        assert isinstance(uuid_base, BLEUUIDBase), 'Invalid argument type'
        uuid_type = driver.new_uint8()

        err_code = driver.sd_ble_uuid_vs_add(self.rpc_adapter,
                                             uuid_base.to_c(),
                                             uuid_type)
        if err_code == driver.NRF_SUCCESS:
            uuid_base.type = driver.uint8_value(uuid_type)
        return err_code

    """
    GAP Methods
    """

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_addr_get(self):
        addr = driver.ble_gap_addr_t()
        err_code = driver.sd_ble_gap_addr_get(self.rpc_adapter, addr)
        if err_code == driver.NRF_SUCCESS:
            addr = BLEGapAddr.from_c(addr)
        else:
            addr = None
        return err_code, addr

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_addr_set(self, address):
        assert isinstance(address, BLEGapAddr), "Invalid argument type"
        addr_c = address.to_c()
        return driver.sd_ble_gap_addr_set(self.rpc_adapter, addr_c)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_device_name_set(self, name):
        if isinstance(name, str):
            name = name.encode("utf8")
        write_perm = BLEGapSecMode(0, 0).to_c()
        length = len(name)
        data_array = util.list_to_uint8_array(name)
        data = data_array.cast()
        return driver.sd_ble_gap_device_name_set(self.rpc_adapter, write_perm, data, length)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_appearance_set(self, value):
        return driver.sd_ble_gap_appearance_set(self.rpc_adapter, value)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_ppcp_set(self, conn_params):
        assert isinstance(conn_params, BLEGapConnParams), "Invalid argument type"
        params = conn_params.to_c()
        return driver.sd_ble_gap_ppcp_set(self.rpc_adapter, params)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_tx_power_set(self, tx_power):
        return driver.sd_ble_gap_tx_power_set(self.rpc_adapter, tx_power)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_privacy_set(self, privacy):
        assert isinstance(privacy, BLEGapPrivacyParams)
        params = privacy.to_c()
        return driver.sd_ble_gap_privacy_set(self.rpc_adapter, params)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_adv_start(self, adv_params=None, conn_cfg_tag=0):
        if not adv_params:
            adv_params = self.adv_params_setup()
        assert isinstance(adv_params, BLEGapAdvParams), 'Invalid argument type'
        return driver.sd_ble_gap_adv_start(self.rpc_adapter, adv_params.to_c(), conn_cfg_tag)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_conn_param_update(self, conn_handle, conn_params):
        assert isinstance(conn_params, (BLEGapConnParams, NoneType)), 'Invalid argument type'
        if conn_params:
            conn_params = conn_params.to_c()
        return driver.sd_ble_gap_conn_param_update(self.rpc_adapter, conn_handle, conn_params)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_adv_stop(self):
        return driver.sd_ble_gap_adv_stop(self.rpc_adapter)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_scan_start(self, scan_params=None):
        if not scan_params:
            scan_params = self.scan_params_setup()
        assert isinstance(scan_params, BLEGapScanParams), 'Invalid argument type'
        return driver.sd_ble_gap_scan_start(self.rpc_adapter, scan_params.to_c())

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_scan_stop(self):
        return driver.sd_ble_gap_scan_stop(self.rpc_adapter)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_rssi_start(self, conn_handle, threshold_dbm, skip_count):
        if threshold_dbm is None:
            threshold_dbm = driver.BLE_GAP_RSSI_THRESHOLD_INVALID
        return driver.sd_ble_gap_rssi_start(self.rpc_adapter, conn_handle, threshold_dbm, skip_count)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_rssi_stop(self, conn_handle):
        return driver.sd_ble_gap_rssi_stop(self.rpc_adapter, conn_handle)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_rssi_get(self, conn_handle):
        rssi = driver.new_int8()
        err = driver.sd_ble_gap_rssi_get(self.rpc_adapter, conn_handle, rssi)
        if err == driver.NRF_SUCCESS:
            rssi = driver.int8_value(rssi)
        else:
            rssi = None
        return err, rssi

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_connect(self, address, scan_params=None, conn_params=None, conn_cfg_tag=0):
        assert isinstance(address, BLEGapAddr), 'Invalid argument type'

        if not scan_params:
            scan_params = self.scan_params_setup()
        assert isinstance(scan_params, BLEGapScanParams), 'Invalid argument type'

        if not conn_params:
            conn_params = self.conn_params_setup()
        assert isinstance(conn_params, BLEGapConnParams), 'Invalid argument type'

        return driver.sd_ble_gap_connect(self.rpc_adapter,
                                         address.to_c(),
                                         scan_params.to_c(),
                                         conn_params.to_c(),
                                         conn_cfg_tag)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_disconnect(self, conn_handle, hci_status_code=BLEHci.remote_user_terminated_connection):
        assert isinstance(hci_status_code, BLEHci), 'Invalid argument type'
        return driver.sd_ble_gap_disconnect(self.rpc_adapter,
                                            conn_handle,
                                            hci_status_code.value)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_adv_data_set(self, adv_data=BLEAdvData(), scan_data=BLEAdvData()):
        assert isinstance(adv_data, BLEAdvData), 'Invalid argument type'
        assert isinstance(scan_data, BLEAdvData), 'Invalid argument type'
        (adv_data_len, p_adv_data) = adv_data.to_c()
        (scan_data_len, p_scan_data) = scan_data.to_c()

        return driver.sd_ble_gap_adv_data_set(self.rpc_adapter,
                                              p_adv_data,
                                              adv_data_len,
                                              p_scan_data,
                                              scan_data_len)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_data_length_update(self, conn_handle, params=None):
        assert isinstance(params, (BLEGapDataLengthParams, NoneType))
        if isinstance(params, BLEGapDataLengthParams):
            params = params.to_c()
        return driver.sd_ble_gap_data_length_update(self.rpc_adapter, conn_handle, params, None)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_phy_update(self, conn_handle, tx_phy=BLEGapPhy.auto, rx_phy=BLEGapPhy.auto):
        params = BLEGapPhys(tx_phy, rx_phy)
        return driver.sd_ble_gap_phy_update(self.rpc_adapter, conn_handle, params.to_c())

    """
    SMP Methods
    """

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_authenticate(self, conn_handle, sec_params):
        assert isinstance(sec_params, (BLEGapSecParams, NoneType)), 'Invalid argument type'
        return driver.sd_ble_gap_authenticate(self.rpc_adapter,
                                              conn_handle,
                                              sec_params.to_c() if sec_params else None)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_sec_params_reply(self, conn_handle, sec_status, sec_params, sec_keyset):
        assert isinstance(sec_status, BLEGapSecStatus), 'Invalid argument type'
        assert isinstance(sec_params, (BLEGapSecParams, NoneType)), 'Invalid argument type'
        assert isinstance(sec_keyset, BLEGapSecKeyset), 'Invalid argument type'

        return driver.sd_ble_gap_sec_params_reply(self.rpc_adapter,
                                                  conn_handle,
                                                  sec_status.value,
                                                  sec_params.to_c() if sec_params else None,
                                                  sec_keyset.to_c())

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_auth_key_reply(self, conn_handle, key_type, key):
        key_data = None
        if key is not None:
            key_data = util.list_to_uint8_array(key)
            key_buf = key_data.cast()
        else:
            key_buf = None
        return driver.sd_ble_gap_auth_key_reply(self.rpc_adapter, conn_handle, key_type, key_buf)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_sec_info_reply(self, conn_handle, enc_info=None, irk=None, sign_info=None):
        assert isinstance(enc_info, (BLEGapEncryptInfo, NoneType)), "Invalid argument type"
        assert isinstance(irk, (BLEGapIdKey, NoneType)), "Invalid argument type"
        assert isinstance(sign_info, (BLEGapSignKey, NoneType)), "Invalid argument type"
        if enc_info is not None:
            enc_info = enc_info.to_c()
        if irk is not None:
            irk = irk.to_c().id_info
        if sign_info is not None:
            sign_info = sign_info.to_c()

        return driver.sd_ble_gap_sec_info_reply(self.rpc_adapter, conn_handle, enc_info, irk, sign_info)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_encrypt(self, conn_handle, master_id, enc_info):
        assert isinstance(master_id, BLEGapMasterId)
        assert isinstance(enc_info, BLEGapEncryptInfo)

        return driver.sd_ble_gap_encrypt(self.rpc_adapter, conn_handle, master_id.to_c(), enc_info.to_c())

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gap_lesc_dhkey_reply(self, conn_handle, dh_key):
        assert isinstance(dh_key, BLEGapDhKey)

        key = dh_key.to_c()
        return driver.sd_ble_gap_lesc_dhkey_reply(self.rpc_adapter, conn_handle, key)

    """
    GATTS Methods
    """
    # TODO: sd_ble_gatts_include_add, sd_ble_gatts_descriptor_add, sd_ble_gatts_sys_attr_set/get,
    # sd_ble_gatts_initial_user_handle_get, sd_ble_gatts_attr_get

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_service_add(self, service_type, uuid, service_handle):
        handle = driver.new_uint16()
        uuid_c = uuid.to_c()
        err_code = driver.sd_ble_gatts_service_add(self.rpc_adapter,
                                                   service_type,
                                                   uuid_c,
                                                   handle)
        if err_code == driver.NRF_SUCCESS:
            service_handle.handle = driver.uint16_value(handle)
        return err_code

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_characteristic_add(self, service_handle, char_md, attr_char_value, char_handle):
        # TODO type assertions
        handle_params = driver.ble_gatts_char_handles_t()
        err_code = driver.sd_ble_gatts_characteristic_add(self.rpc_adapter,
                                                          service_handle,
                                                          char_md.to_c(),
                                                          attr_char_value.to_c(),
                                                          handle_params)
        if err_code == driver.NRF_SUCCESS:
            char_handle.value_handle = handle_params.value_handle
            char_handle.user_desc_handle = handle_params.user_desc_handle
            char_handle.cccd_handle = handle_params.cccd_handle
            char_handle.sccd_handle = handle_params.sccd_handle
        return err_code

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_descriptor_add(self, char_handle, attr):
        assert isinstance(attr, BLEGattsAttribute)
        handle = driver.new_uint16()
        err_code = driver.sd_ble_gatts_descriptor_add(self.rpc_adapter, char_handle, attr.to_c(), handle)
        if err_code == driver.NRF_SUCCESS:
            attr.handle = driver.uint16_value(handle)
        return err_code


    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_rw_authorize_reply(self, conn_handle, authorize_reply_params):
        assert isinstance(authorize_reply_params, BLEGattsRwAuthorizeReplyParams)
        return driver.sd_ble_gatts_rw_authorize_reply(self.rpc_adapter, conn_handle, authorize_reply_params.to_c())

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_value_get(self, conn_handle, attribute_handle, gatts_value, max_bytes_read=512):
        assert isinstance(gatts_value, BLEGattsValue)
        value_params = gatts_value.to_c()
        value_params.len = max_bytes_read
        err_code = driver.sd_ble_gatts_value_get(self.rpc_adapter, conn_handle, attribute_handle, value_params)

        if err_code == driver.NRF_SUCCESS:
            value_out = BLEGattsValue.from_c(value_params)
            gatts_value.offset = value_out.offset
            gatts_value.value = value_out.value
        return err_code

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_value_set(self, conn_handle, attribute_handle, gatts_value):
        assert isinstance(gatts_value, BLEGattsValue)
        value_params = gatts_value.to_c()
        return driver.sd_ble_gatts_value_set(self.rpc_adapter, conn_handle, attribute_handle, value_params)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_hvx(self, conn_handle, hvx_params):
        assert isinstance(hvx_params, BLEGattsHvx)
        return driver.sd_ble_gatts_hvx(self.rpc_adapter, conn_handle, hvx_params.to_c())

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_service_changed(self, conn_handle, start_handle, end_handle):
        return driver.sd_ble_gatts_service_changed(self.rpc_adapter, conn_handle, start_handle, end_handle)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_exchange_mtu_reply(self, conn_handle, server_mtu):
        return driver.sd_ble_gatts_exchange_mtu_reply(self.rpc_adapter, conn_handle, server_mtu)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gatts_sys_attr_set(self, conn_handle, sys_attr_data, flags=0):
        data_array = None
        if sys_attr_data is not None:
            data_array = util.list_to_uint8_array(sys_attr_data)
            data = data_array.cast()
            length = len(sys_attr_data)
        else:
            data = None
            length = 0
        return driver.sd_ble_gatts_sys_attr_set(self.rpc_adapter, conn_handle, data, length, flags)

    """
    GATTC Methods
    """

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_write(self, conn_handle, write_params):
        assert isinstance(write_params, BLEGattcWriteParams), 'Invalid argument type'
        return driver.sd_ble_gattc_write(self.rpc_adapter,
                                         conn_handle,
                                         write_params.to_c())

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_prim_srvc_disc(self, conn_handle, srvc_uuid, start_handle):
        assert isinstance(srvc_uuid, (BLEUUID, NoneType)), 'Invalid argument type'
        return driver.sd_ble_gattc_primary_services_discover(self.rpc_adapter,
                                                             conn_handle,
                                                             start_handle,
                                                             srvc_uuid.to_c() if srvc_uuid else None)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_char_disc(self, conn_handle, start_handle, end_handle):
        handle_range = driver.ble_gattc_handle_range_t()
        handle_range.start_handle = start_handle
        handle_range.end_handle = end_handle
        return driver.sd_ble_gattc_characteristics_discover(self.rpc_adapter,
                                                            conn_handle,
                                                            handle_range)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_desc_disc(self, conn_handle, start_handle, end_handle):
        handle_range = driver.ble_gattc_handle_range_t()
        handle_range.start_handle = start_handle
        handle_range.end_handle = end_handle
        return driver.sd_ble_gattc_descriptors_discover(self.rpc_adapter,
                                                        conn_handle,
                                                        handle_range)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_attr_info_disc(self, conn_handle, start_handle, end_handle):
        handle_range = driver.ble_gattc_handle_range_t()
        handle_range.start_handle = start_handle
        handle_range.end_handle = end_handle
        return driver.sd_ble_gattc_attr_info_discover(self.rpc_adapter, conn_handle, handle_range)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_read(self, conn_handle, read_handle, offset=0):
        return driver.sd_ble_gattc_read(self.rpc_adapter, conn_handle, read_handle, offset)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_exchange_mtu_req(self, conn_handle, att_mtu_size):
        return driver.sd_ble_gattc_exchange_mtu_request(self.rpc_adapter,
                                                        conn_handle,
                                                        att_mtu_size)

    @NordicSemiErrorCheck
    @wrapt.synchronized
    def ble_gattc_hv_confirm(self, conn_handle, attr_handle):
        return driver.sd_ble_gattc_hv_confirm(self.rpc_adapter, conn_handle, attr_handle)

    """
    Driver handlers
    """

    def _status_handler(self, adapter, status_code, status_message):
        if self._log_driver_comms:
            logger.info("STATUS [{}]: {}".format(status_code, status_message))

    def _log_message_handler(self, adapter, severity, log_message):
        if self._log_driver_comms:
            logger.info("LOG [{}]: {}".format(severity, log_message))

    """
    Event handling
    """

    def ble_evt_handler(self, adapter, ble_event):
        self._events.put(ble_event)

    def _event_handler(self):
        self._event_loop = True
        self._event_stopped.clear()
        while self._event_loop:
            try:
                ble_event = self._events.get(timeout=0.1)
            except queue.Empty:
                continue

            if len(self.observers) == 0:
                continue

            event = event_decode(ble_event)
            if event is None:
                logger.warning('unknown ble_event %r (discarded)', ble_event.header.evt_id)
                continue

            # Get a copy of the observers and event observers in case its modified during this execution
            with self._event_observer_lock:
                observers = self.observers[:]
                event_handlers = {k: v[:] for k, v in self._event_observers.items()}

            # Call all the observers
            for obs in observers:
                try:
                    obs.on_driver_event(self, event)
                except:
                    traceback.print_exc()

            # Call all the handlers for the event type provided
            for event_type, handlers in event_handlers.items():
                if issubclass(type(event), event_type):
                    for handler in handlers:
                        try:
                            handler(self, event)
                        except:
                            traceback.print_exc()

        self._event_stopped.set()
