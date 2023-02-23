from enum import Enum, IntEnum
import logging

from pc_ble_driver_py.lib import nrf_ble_driver_sd_api_v5

from blatann.nrf import nrf_driver_types as util
from blatann.nrf.nrf_dll_load import driver

logger = logging.getLogger(__name__)


class BleOptionFlag(IntEnum):
    pa_lna = driver.BLE_COMMON_OPT_PA_LNA
    conn_event_extension = driver.BLE_COMMON_OPT_CONN_EVT_EXT
    gap_channel_map = driver.BLE_GAP_OPT_CH_MAP
    gap_local_conn_latency = driver.BLE_GAP_OPT_LOCAL_CONN_LATENCY
    gap_passkey = driver.BLE_GAP_OPT_PASSKEY
    gap_scan_req_report = driver.BLE_GAP_OPT_SCAN_REQ_REPORT
    gap_compat_mode_1 = driver.BLE_GAP_OPT_COMPAT_MODE_1
    gap_auth_payload_timeout = driver.BLE_GAP_OPT_AUTH_PAYLOAD_TIMEOUT
    gap_slave_latency_disable = driver.BLE_GAP_OPT_SLAVE_LATENCY_DISABLE


class BleOption(object):
    option_flag = None
    path = ""

    def to_c(self):
        raise NotImplementedError


class BleEnableOpt(BleOption):
    _default = False
    _driver_type = None

    def __init__(self, enabled=_default):
        self.enabled = enabled

    def to_c(self):
        opt = self._driver_type()
        opt.enable = self.enabled
        return opt


class BleOptConnEventExtenion(BleEnableOpt):
    option_flag = BleOptionFlag.conn_event_extension
    path = "common_opt.conn_evt_ext"
    _driver_type = driver.ble_common_opt_conn_evt_ext_t


class BlePaLnaConfig(object):
    def __init__(self, enabled=False, active_high=True, pin=0):
        self.enabled = enabled
        self.active_high = active_high
        self.pin = pin

    def to_c(self):
        cfg = driver.ble_pa_lna_cfg_t()
        cfg.enable = int(self.enabled)
        cfg.active_high = int(self.active_high)
        cfg.gpio_pin = self.pin
        return cfg


class BleOptPaLna(BleOption):
    option_flag = BleOptionFlag.pa_lna
    path = "common_opt.pa_lna"

    def __init__(self, pa_config=None, lna_cfg=None, ppi_channel_set=0,
                 ppi_channel_clear=0, gpiote_channel=0):
        self.pa_config = pa_config or BlePaLnaConfig()
        self.lna_config = lna_cfg or BlePaLnaConfig()
        self.ppi_channel_set = ppi_channel_set
        self.ppi_channel_clear = ppi_channel_clear
        self.gpiote_channel = gpiote_channel

    def to_c(self):
        opt = driver.ble_common_opt_pa_lna_t()
        opt.pa_cfg = self.pa_config.to_c()
        opt.lna_cfg = self.lna_config.to_c()
        opt.ppi_ch_id_set = self.ppi_channel_set
        opt.ppi_ch_id_clr = self.ppi_channel_clear
        opt.gpiote_ch_id = self.gpiote_channel
        return opt


class BleOptGapChannelMap(BleOption):
    option_flag = BleOptionFlag.gap_channel_map
    path = "gap_opt.ch_map"

    def __init__(self, enabled_channels=None, conn_handle=0):
        self.conn_handle = conn_handle
        self.channel_map = enabled_channels or list(range(37))

    def to_c(self):
        opt = driver.ble_gap_opt_ch_map_t()
        opt.conn_handle = self.conn_handle
        for i in self.channel_map:
            if i >= 37:
                logger.warning("Cannot set channel {} in the channel map".format(i))
                continue
            byte = i // 8
            bit = 1 << (i % 8)
            opt.ch_map[byte] |= bit

        return opt


class BleOptGapLocalConnLatency(BleOption):
    option_flag = BleOptionFlag.gap_local_conn_latency
    path = "gap_opt.local_conn_latency"

    def __init__(self, conn_handle=0, requested_latency=0):
        self.conn_handle = conn_handle
        self.requested_latency = requested_latency

    def to_c(self):
        opt = driver.ble_gap_opt_local_conn_latency_t()
        opt.conn_handle = self.conn_handle
        opt.requested_latency = self.requested_latency
        return opt


class BleOptGapPasskey(BleOption):
    option_flag = BleOptionFlag.gap_passkey
    path = "gap_opt.passkey"

    def __init__(self, passkey="000000"):
        self.passkey = passkey

    def to_c(self):
        opt = driver.ble_gap_opt_passkey_t()
        opt.p_passkey = util.list_to_char_array(self.passkey).cast()
        return opt


class BleOptGapScanRequestReport(BleEnableOpt):
    option_flag = BleOptionFlag.gap_scan_req_report
    path = "gap_opt.scan_req_report"
    _driver_type = driver.ble_gap_opt_scan_req_report_t


class BleOptGapCompatMode1(BleEnableOpt):
    option_flag = BleOptionFlag.gap_compat_mode_1
    path = "gap_opt.compat_mode_q"
    _driver_type = driver.ble_gap_opt_compat_mode_1_t


class BleOptGapAuthPayloadTimeout(BleOption):
    option_flag = BleOptionFlag.gap_auth_payload_timeout
    path = "gap_opt.auth_payload_timeout"

    def __init__(self, conn_handle, timeout_ms=driver.BLE_GAP_AUTH_PAYLOAD_TIMEOUT_MAX):
        self.conn_handle = conn_handle
        self.timeout_ms = timeout_ms

    def to_c(self):
        opt = driver.ble_gap_opt_auth_payload_timeout_t()
        opt.conn_handle = self.conn_handle
        opt.auth_payload_timeout = util.msec_to_units(self.timeout_ms, util.UNIT_10_MS)
        return opt


class BleOptGapSlaveLatencyDisable(BleOption):
    option_flag = BleOptionFlag.gap_slave_latency_disable
    path = "gap_opt.slave_latency_disable"

    def __init__(self, conn_handle, disabled=False):
        self.conn_handle = conn_handle
        self.disabled = disabled

    def to_c(self):
        opt = driver.ble_gap_opt_slave_latency_disable_t()
        opt.conn_handle = self.conn_handle
        opt.disable = int(self.disabled)


class BleEnableConfig(object):
    def __init__(self,
                 vs_uuid_count=10,
                 periph_role_count=driver.BLE_GAP_ROLE_COUNT_PERIPH_DEFAULT,
                 central_role_count=driver.BLE_GAP_ROLE_COUNT_CENTRAL_DEFAULT,
                 central_sec_count=driver.BLE_GAP_ROLE_COUNT_CENTRAL_DEFAULT,
                 service_changed_char=driver.BLE_GATTS_SERVICE_CHANGED_DEFAULT,
                 attr_table_size=driver.BLE_GATTS_ATTR_TAB_SIZE_DEFAULT):
        self.vs_uuid_count = vs_uuid_count
        self.periph_role_count = periph_role_count
        self.central_role_count = central_role_count
        self.central_sec_count = central_sec_count
        self.service_changed_char = service_changed_char
        self.attr_table_size = attr_table_size

    def get_vs_uuid_cfg(self):
        config = driver.ble_cfg_t()
        cfg = config.common_cfg.vs_uuid_cfg
        cfg.vs_uuid_count = self.vs_uuid_count

        return driver.BLE_COMMON_CFG_VS_UUID, config

    def get_role_count_cfg(self):
        config = driver.ble_cfg_t()
        cfg = config.gap_cfg.role_count_cfg
        cfg.periph_role_count = self.periph_role_count
        cfg.central_role_count = self.central_role_count
        cfg.central_sec_count = self.central_sec_count

        return driver.BLE_GAP_CFG_ROLE_COUNT, config

    def get_device_name_cfg(self):
        config = driver.ble_cfg_t()
        cfg = config.gap_cfg.device_name_cfg
        cfg.current_len = 0
        cfg.max_len = driver.BLE_GAP_DEVNAME_DEFAULT_LEN
        cfg.write_perm.sm = 0
        cfg.write_perm.lv = 0
        cfg.vloc = driver.BLE_GATTS_VLOC_STACK

        return driver.BLE_GAP_CFG_DEVICE_NAME, config

    def get_service_changed_cfg(self):
        config = driver.ble_cfg_t()
        cfg = config.gatts_cfg.service_changed
        cfg.service_changed = self.service_changed_char

        return driver.BLE_GATTS_CFG_SERVICE_CHANGED, config

    def get_attr_tab_size_cfg(self):
        config = driver.ble_cfg_t()
        cfg = config.gatts_cfg.attr_tab_size
        cfg.attr_tab_size = self.attr_table_size

        return driver.BLE_GATTS_CFG_ATTR_TAB_SIZE, config

    def get_configs(self):
        yield self.get_vs_uuid_cfg()
        yield self.get_role_count_cfg()
        yield self.get_device_name_cfg()
        yield self.get_service_changed_cfg()
        yield self.get_attr_tab_size_cfg()


class BleConnConfig(object):
    DEFAULT_CONN_TAG = 1

    def __init__(self, conn_tag=DEFAULT_CONN_TAG,
                 conn_count=driver.BLE_GAP_CONN_COUNT_DEFAULT,
                 event_length=driver.BLE_GAP_EVENT_LENGTH_DEFAULT,
                 write_cmd_tx_queue_size=driver.BLE_GATTC_WRITE_CMD_TX_QUEUE_SIZE_DEFAULT,
                 hvn_tx_queue_size=driver.BLE_GATTS_HVN_TX_QUEUE_SIZE_DEFAULT,
                 max_att_mtu=driver.BLE_GATT_ATT_MTU_DEFAULT):  # TODO: L2CAP config
        self.conn_tag = conn_tag
        self.conn_count = conn_count
        self.event_length = event_length
        self.write_cmd_tx_queue_size = write_cmd_tx_queue_size
        self.hvn_tx_queue_size = hvn_tx_queue_size
        self.max_att_mtu = max_att_mtu

    def get_gap_config(self):
        config = driver.ble_cfg_t()
        config.conn_cfg.conn_cfg_tag = self.conn_tag
        cfg = config.conn_cfg.params.gap_conn_cfg
        cfg.conn_count = self.conn_count
        cfg.event_length = self.event_length
        return driver.BLE_CONN_CFG_GAP, config

    def get_gatt_config(self):
        config = driver.ble_cfg_t()
        config.conn_cfg.conn_cfg_tag = self.conn_tag
        cfg = config.conn_cfg.params.gatt_conn_cfg
        cfg.att_mtu = self.max_att_mtu
        return driver.BLE_CONN_CFG_GATT, config

    def get_gattc_config(self):
        config = driver.ble_cfg_t()
        config.conn_cfg.conn_cfg_tag = self.conn_tag
        cfg = config.conn_cfg.params.gattc_conn_cfg
        cfg.write_cmd_tx_queue_size = self.write_cmd_tx_queue_size
        return driver.BLE_CONN_CFG_GATTC, config

    def get_gatts_config(self):
        config = driver.ble_cfg_t()
        config.conn_cfg.conn_cfg_tag = self.conn_tag
        cfg = config.conn_cfg.params.gatts_conn_cfg
        cfg.hvn_tx_queue_size = self.hvn_tx_queue_size
        return driver.BLE_CONN_CFG_GATTS, config

    def get_configs(self):
        yield self.get_gap_config()
        yield self.get_gatt_config()
        yield self.get_gattc_config()
        yield self.get_gatts_config()
