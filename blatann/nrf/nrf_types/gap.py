from enum import Enum, IntEnum
import logging

from blatann.utils import repr_format
from pc_ble_driver_py.exceptions import NordicSemiException
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_types.enums import *
from blatann.utils import repr_format


logger = logging.getLogger(__name__)


class TimeRange(object):

    def __init__(self, name, val_min, val_max, unit_ms_conversion, divisor=1.0, units="ms"):
        self._name = name
        self._units = units
        self._min = util.units_to_msec(val_min, unit_ms_conversion) / divisor
        self._max = util.units_to_msec(val_max, unit_ms_conversion) / divisor

    @property
    def name(self) -> str:
        return self._name

    @property
    def min(self) -> float:
        return self._min

    @property
    def max(self) -> float:
        return self._max

    @property
    def units(self) -> str:
        return self._units

    def is_in_range(self, value):
        return self._min <= value <= self._max

    def validate(self, value):
        if value < self._min:
            raise ValueError(f"Minimum {self.name} is {self._min}{self.units} (Got {value})")
        if value > self._max:
            raise ValueError(f"Maximum {self.name} is {self._max}{self.units} (Got {value})")


adv_interval_range = TimeRange("Advertising Interval",
                               driver.BLE_GAP_ADV_INTERVAL_MIN, driver.BLE_GAP_ADV_INTERVAL_MAX, util.UNIT_0_625_MS)
scan_window_range = TimeRange("Scan Window",
                              driver.BLE_GAP_SCAN_WINDOW_MIN, driver.BLE_GAP_SCAN_WINDOW_MAX, util.UNIT_0_625_MS)
scan_interval_range = TimeRange("Scan Interval",
                                driver.BLE_GAP_SCAN_INTERVAL_MIN, driver.BLE_GAP_SCAN_INTERVAL_MAX, util.UNIT_0_625_MS)
scan_timeout_range = TimeRange("Scan Timeout",
                               driver.BLE_GAP_SCAN_TIMEOUT_MIN, driver.BLE_GAP_SCAN_TIMEOUT_MAX, util.UNIT_10_MS, 1000.0, "s")
conn_interval_range = TimeRange("Connection Interval",
                                driver.BLE_GAP_CP_MIN_CONN_INTVL_MIN, driver.BLE_GAP_CP_MAX_CONN_INTVL_MAX, util.UNIT_1_25_MS)
conn_timeout_range = TimeRange("Connection Timeout",
                               driver.BLE_GAP_CP_CONN_SUP_TIMEOUT_MIN, driver.BLE_GAP_CP_CONN_SUP_TIMEOUT_MAX, util.UNIT_10_MS)


class BLEGapAdvParams(object):
    def __init__(self, interval_ms, timeout_s, advertising_type=BLEGapAdvType.connectable_undirected, channel_mask=None):
        self.interval_ms = interval_ms
        self.timeout_s = timeout_s
        self.advertising_type = advertising_type
        self.channel_mask = channel_mask or [False, False, False]

    def to_c(self):
        adv_params = driver.ble_gap_adv_params_t()
        adv_params.type = self.advertising_type.value
        adv_params.p_peer_addr = None  # Undirected advertisement.
        adv_params.fp = driver.BLE_GAP_ADV_FP_ANY
        adv_params.p_whitelist = None
        adv_params.interval = util.msec_to_units(self.interval_ms,
                                                 util.UNIT_0_625_MS)
        adv_params.timeout = self.timeout_s

        mask = driver.ble_gap_adv_ch_mask_t()
        mask.ch_37_off = self.channel_mask[0]
        mask.ch_38_off = self.channel_mask[1]
        mask.ch_39_off = self.channel_mask[2]
        adv_params.channel_mask = mask

        return adv_params

    def __repr__(self):
        ch_mask_str = "".join([str(int(c)) for c in self.channel_mask])
        return "{!r}(type: {!r}, interval: {!r}ms, timeout: {!r}s, ch mask: {})".format(
            self.__class__.__name__,
            self.advertising_type,
            self.interval_ms,
            self.timeout_s,
            ch_mask_str)


class BLEGapScanParams(object):
    def __init__(self, interval_ms, window_ms, timeout_s, active=True):
        self.interval_ms = interval_ms
        self.window_ms = window_ms
        self.timeout_s = timeout_s
        self.active = active

    def to_c(self):
        scan_params = driver.ble_gap_scan_params_t()
        scan_params.active = self.active
        scan_params.use_whitelist = False
        scan_params.interval = util.msec_to_units(self.interval_ms,
                                                  util.UNIT_0_625_MS)
        scan_params.window = util.msec_to_units(self.window_ms,
                                                util.UNIT_0_625_MS)
        scan_params.timeout = self.timeout_s

        return scan_params


class BLEGapConnParams(object):
    def __init__(self, min_conn_interval_ms, max_conn_interval_ms, conn_sup_timeout_ms, slave_latency):
        self.min_conn_interval_ms = min_conn_interval_ms
        self.max_conn_interval_ms = max_conn_interval_ms
        self.conn_sup_timeout_ms = conn_sup_timeout_ms
        self.slave_latency = slave_latency

    def validate(self):
        conn_interval_range.validate(self.min_conn_interval_ms)
        conn_interval_range.validate(self.max_conn_interval_ms)
        conn_timeout_range.validate(self.conn_sup_timeout_ms)
        if self.min_conn_interval_ms > self.max_conn_interval_ms:
            raise ValueError(f"Minimum connection interval must be <= max connection interval "
                             f"(Min: {self.min_conn_interval_ms} Max: {self.max_conn_interval_ms}")

    @classmethod
    def from_c(cls, conn_params):
        return cls(min_conn_interval_ms=util.units_to_msec(conn_params.min_conn_interval,
                                                           util.UNIT_1_25_MS),
                   max_conn_interval_ms=util.units_to_msec(conn_params.max_conn_interval,
                                                           util.UNIT_1_25_MS),
                   conn_sup_timeout_ms=util.units_to_msec(conn_params.conn_sup_timeout,
                                                          util.UNIT_10_MS),
                   slave_latency=conn_params.slave_latency)

    def to_c(self):
        conn_params = driver.ble_gap_conn_params_t()
        conn_params.min_conn_interval = util.msec_to_units(self.min_conn_interval_ms,
                                                           util.UNIT_1_25_MS)
        conn_params.max_conn_interval = util.msec_to_units(self.max_conn_interval_ms,
                                                           util.UNIT_1_25_MS)
        conn_params.conn_sup_timeout = util.msec_to_units(self.conn_sup_timeout_ms,
                                                          util.UNIT_10_MS)
        conn_params.slave_latency = self.slave_latency

        return conn_params

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{}(interval: [{!r}-{!r}] ms, timeout: {!r} ms, latency: {!r})".format(self.__class__.__name__,
                                                                                      self.min_conn_interval_ms,
                                                                                      self.max_conn_interval_ms,
                                                                                      self.conn_sup_timeout_ms,
                                                                                      self.slave_latency)


class BLEGapAddrTypes(IntEnum):
    public = int(driver.BLE_GAP_ADDR_TYPE_PUBLIC)
    random_static = int(driver.BLE_GAP_ADDR_TYPE_RANDOM_STATIC)
    random_private_resolvable = int(driver.BLE_GAP_ADDR_TYPE_RANDOM_PRIVATE_RESOLVABLE)
    random_private_non_resolvable = int(driver.BLE_GAP_ADDR_TYPE_RANDOM_PRIVATE_NON_RESOLVABLE)
    anonymous = 127  # This isn't defined in the headers for Softdevice v5 and was added in v6


class BLEGapAddr(object):

    def __init__(self, addr_type, addr):
        assert isinstance(addr_type, BLEGapAddrTypes), 'Invalid argument type'
        self.addr_type = addr_type
        self.addr = addr

    @classmethod
    def from_c(cls, addr):
        addr_list = util.uint8_array_to_list(addr.addr, driver.BLE_GAP_ADDR_LEN)
        addr_list.reverse()
        return cls(addr_type=BLEGapAddrTypes(addr.addr_type),
                   addr=addr_list)

    @classmethod
    def from_string(cls, addr_string):
        addr, addr_flag = addr_string.split(',')
        addr_list = [int(i, 16) for i in addr.split(':')]

        if addr_flag in ['p', 'public']:
            addr_type = BLEGapAddrTypes.public
        elif (addr_list[0] & 0b11000000) == 0b00000000:
            addr_type = BLEGapAddrTypes.random_private_non_resolvable
        elif (addr_list[0] & 0b11000000) == 0b01000000:
            addr_type = BLEGapAddrTypes.random_private_resolvable
        elif (addr_list[0] & 0b11000000) == 0b11000000:
            addr_type = BLEGapAddrTypes.random_static
        else:
            raise ValueError("Provided random address do not follow rules")  # TODO: Improve error message

        return cls(addr_type, addr_list)

    def to_c(self):
        addr_array = util.list_to_uint8_array(self.addr[::-1])
        addr = driver.ble_gap_addr_t()
        addr.addr_type = self.addr_type.value
        addr.addr = addr_array.cast()
        return addr

    def get_addr_type_str(self):
        if self.addr_type == BLEGapAddrTypes.public:
            return 'public'
        elif self.addr_type == BLEGapAddrTypes.random_private_non_resolvable:
            return 'nonres'
        elif self.addr_type == BLEGapAddrTypes.random_private_resolvable:
            return 'res'
        elif self.addr_type == BLEGapAddrTypes.random_static:
            return 'static'
        elif self.addr_type == BLEGapAddrTypes.anonymous:
            return 'anonymous'
        else:
            return 'err'

    def __eq__(self, other):
        if not isinstance(other, BLEGapAddr):
            other = BLEGapAddr.from_string(str(other))
        return str(self) == str(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        value = 0
        for i, val in enumerate(self.addr[::-1]):
            value |= val << i*8
        return value

    def get_addr_flag(self):
        return {
            BLEGapAddrTypes.public: "p",
            BLEGapAddrTypes.random_static: "s",
            BLEGapAddrTypes.random_private_resolvable: "r",
            BLEGapAddrTypes.random_private_non_resolvable: "n",
            BLEGapAddrTypes.anonymous: "a"
        }[self.addr_type]

    def __str__(self):
        return '{},{}'.format(':'.join(['%02X' % i for i in self.addr]), self.get_addr_flag())

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, str(self))


class BLEAdvData(object):
    class Types(Enum):
        flags = driver.BLE_GAP_AD_TYPE_FLAGS
        service_16bit_uuid_more_available = driver.BLE_GAP_AD_TYPE_16BIT_SERVICE_UUID_MORE_AVAILABLE
        service_16bit_uuid_complete = driver.BLE_GAP_AD_TYPE_16BIT_SERVICE_UUID_COMPLETE
        service_32bit_uuid_more_available = driver.BLE_GAP_AD_TYPE_32BIT_SERVICE_UUID_MORE_AVAILABLE
        service_32bit_uuid_complete = driver.BLE_GAP_AD_TYPE_32BIT_SERVICE_UUID_COMPLETE
        service_128bit_uuid_more_available = driver.BLE_GAP_AD_TYPE_128BIT_SERVICE_UUID_MORE_AVAILABLE
        service_128bit_uuid_complete = driver.BLE_GAP_AD_TYPE_128BIT_SERVICE_UUID_COMPLETE
        short_local_name = driver.BLE_GAP_AD_TYPE_SHORT_LOCAL_NAME
        complete_local_name = driver.BLE_GAP_AD_TYPE_COMPLETE_LOCAL_NAME
        tx_power_level = driver.BLE_GAP_AD_TYPE_TX_POWER_LEVEL
        class_of_device = driver.BLE_GAP_AD_TYPE_CLASS_OF_DEVICE
        simple_pairing_hash_c = driver.BLE_GAP_AD_TYPE_SIMPLE_PAIRING_HASH_C
        simple_pairing_randimizer_r = driver.BLE_GAP_AD_TYPE_SIMPLE_PAIRING_RANDOMIZER_R
        security_manager_tk_value = driver.BLE_GAP_AD_TYPE_SECURITY_MANAGER_TK_VALUE
        security_manager_oob_flags = driver.BLE_GAP_AD_TYPE_SECURITY_MANAGER_OOB_FLAGS
        slave_connection_interval_range = driver.BLE_GAP_AD_TYPE_SLAVE_CONNECTION_INTERVAL_RANGE
        solicited_sevice_uuids_16bit = driver.BLE_GAP_AD_TYPE_SOLICITED_SERVICE_UUIDS_16BIT
        solicited_sevice_uuids_128bit = driver.BLE_GAP_AD_TYPE_SOLICITED_SERVICE_UUIDS_128BIT
        service_data = driver.BLE_GAP_AD_TYPE_SERVICE_DATA
        public_target_address = driver.BLE_GAP_AD_TYPE_PUBLIC_TARGET_ADDRESS
        random_target_address = driver.BLE_GAP_AD_TYPE_RANDOM_TARGET_ADDRESS
        appearance = driver.BLE_GAP_AD_TYPE_APPEARANCE
        advertising_interval = driver.BLE_GAP_AD_TYPE_ADVERTISING_INTERVAL
        le_bluetooth_device_address = driver.BLE_GAP_AD_TYPE_LE_BLUETOOTH_DEVICE_ADDRESS
        le_role = driver.BLE_GAP_AD_TYPE_LE_ROLE
        simple_pairng_hash_c256 = driver.BLE_GAP_AD_TYPE_SIMPLE_PAIRING_HASH_C256
        simple_pairng_randomizer_r256 = driver.BLE_GAP_AD_TYPE_SIMPLE_PAIRING_RANDOMIZER_R256
        service_data_32bit_uuid = driver.BLE_GAP_AD_TYPE_SERVICE_DATA_32BIT_UUID
        service_data_128bit_uuid = driver.BLE_GAP_AD_TYPE_SERVICE_DATA_128BIT_UUID
        uri = driver.BLE_GAP_AD_TYPE_URI
        information_3d_data = driver.BLE_GAP_AD_TYPE_3D_INFORMATION_DATA
        manufacturer_specific_data = driver.BLE_GAP_AD_TYPE_MANUFACTURER_SPECIFIC_DATA

    def __init__(self, **kwargs):
        self.records = dict()
        for k in kwargs:
            self.records[BLEAdvData.Types[k]] = kwargs[k]
        self.raw_bytes = b""

    def to_list(self):
        data_list = []
        for k in self.records:
            data_list.append(len(self.records[k]) + 1)  # add type length
            data_list.append(k.value)
            if isinstance(self.records[k], str):
                data_list.extend([ord(c) for c in self.records[k]])

            elif isinstance(self.records[k], list):
                data_list.extend(self.records[k])
            elif isinstance(self.records[k], bytes):
                data_list.extend(self.records[k])
            else:
                raise NordicSemiException('Unsupported value type: 0x{:02X}'.format(type(self.records[k])))
        self.raw_bytes = bytes(data_list)
        return data_list

    def to_c(self):
        data_list = self.to_list()
        data_len = len(data_list)
        if data_len == 0:
            return data_len, None
        else:
            self.__data_array = util.list_to_uint8_array(data_list)
            return data_len, self.__data_array.cast()

    @classmethod
    def from_c(cls, adv_report_evt):
        ad_list = util.uint8_array_to_list(adv_report_evt.data, adv_report_evt.dlen)
        ble_adv_data = cls()
        ble_adv_data.raw_bytes = bytes(ad_list)
        index = 0
        while index < len(ad_list):
            ad_len = ad_list[index]
            # If the length field is zero, skip it (probably padded zeros at the end of the payload)
            if ad_len == 0:
                index += 1
                continue
            try:
                ad_type = ad_list[index + 1]
                offset = index + 2
                key = BLEAdvData.Types(ad_type)
                ble_adv_data.records[key] = ad_list[offset: offset + ad_len - 1]
            except ValueError:
                logger.error('Invalid advertising data type: 0x{:02X}'.format(ad_type))
                pass
            except IndexError:
                logger.error('Invalid advertising data: {}'.format(ad_list))
                return ble_adv_data
            index += (ad_len + 1)

        return ble_adv_data

    def __repr__(self):
        return str(self.records)


class BLEGapDataLengthParams(object):
    def __init__(self, max_tx_octets=0, max_rx_octets=0, max_tx_time_us=0, max_rx_time_us=0):
        self.max_tx_octets = max_tx_octets
        self.max_rx_octets = max_rx_octets
        self.max_tx_time_us = max_tx_time_us
        self.max_rx_time_us = max_rx_time_us

    def to_c(self):
        params = driver.ble_gap_data_length_params_t()
        params.max_tx_octets = self.max_tx_octets
        params.max_rx_octets = self.max_rx_octets
        params.max_tx_time_us = self.max_tx_time_us
        params.max_rx_time_us = self.max_rx_time_us
        return params

    def __repr__(self):
        return repr_format(self, tx=self.max_tx_octets, rx=self.max_rx_octets)


class BLEGapPhys(object):
    def __init__(self, tx_phys=BLEGapPhy.auto, rx_phys=BLEGapPhy.auto):
        self.tx_phys = tx_phys
        self.rx_phys = rx_phys

    def to_c(self):
        params = driver.ble_gap_phys_t()
        params.tx_phys = self.tx_phys
        params.rx_phys = self.rx_phys
        return params


class BLEGapPrivacyParams(object):
    DEFAULT_PRIVATE_ADDR_CYCLE_INTERVAL_S = driver.BLE_GAP_DEFAULT_PRIVATE_ADDR_CYCLE_INTERVAL_S

    def __init__(self, enabled=False, resolvable_addr=False,
                 addr_update_rate_s=DEFAULT_PRIVATE_ADDR_CYCLE_INTERVAL_S):
        self.enabled = enabled
        self.resolvable_addr = resolvable_addr
        self.addr_update_rate_s = addr_update_rate_s

    def to_c(self):
        params = driver.ble_gap_privacy_params_t()
        params.privacy_mode = driver.BLE_GAP_PRIVACY_MODE_DEVICE_PRIVACY if self.enabled else driver.BLE_GAP_PRIVACY_MODE_OFF
        params.private_addr_cycle_s = self.addr_update_rate_s
        params.private_addr_type = driver.BLE_GAP_ADDR_TYPE_RANDOM_PRIVATE_RESOLVABLE if self.resolvable_addr else driver.BLE_GAP_ADDR_TYPE_RANDOM_PRIVATE_NON_RESOLVABLE
        return params

    @classmethod
    def from_c(cls, privacy):
        enabled = privacy.privacy_mode != driver.BLE_GAP_PRIVACY_MODE_OFF
        resolvable_addr = privacy.private_addr_type == driver.BLE_GAP_ADDR_TYPE_RANDOM_PRIVATE_RESOLVABLE
        update_rate = privacy.private_addr_cycle_s
        return cls(enabled, resolvable_addr, update_rate)

    def __repr__(self):
        return repr_format(self, enabled=self.enabled,
                           resolvable_addr=self.resolvable_addr,
                           addr_update_rate_s=self.addr_update_rate_s)

    def __str__(self):
        return self.__repr__()
