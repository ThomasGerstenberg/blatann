from enum import Enum
from types import NoneType
import logging
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util

logger = logging.getLogger(__name__)


class BLEHci(Enum):
    success = driver.BLE_HCI_STATUS_CODE_SUCCESS
    unknown_btle_command = driver.BLE_HCI_STATUS_CODE_UNKNOWN_BTLE_COMMAND
    unknown_connection_identifier = driver.BLE_HCI_STATUS_CODE_UNKNOWN_CONNECTION_IDENTIFIER
    authentication_failure = driver.BLE_HCI_AUTHENTICATION_FAILURE
    pin_or_key_missing = driver.BLE_HCI_STATUS_CODE_PIN_OR_KEY_MISSING
    memory_capacity_exceeded = driver.BLE_HCI_MEMORY_CAPACITY_EXCEEDED
    connection_timeout = driver.BLE_HCI_CONNECTION_TIMEOUT
    command_disallowed = driver.BLE_HCI_STATUS_CODE_COMMAND_DISALLOWED
    invalid_btle_command_parameters = driver.BLE_HCI_STATUS_CODE_INVALID_BTLE_COMMAND_PARAMETERS
    remote_user_terminated_connection = driver.BLE_HCI_REMOTE_USER_TERMINATED_CONNECTION
    remote_dev_termination_due_to_low_resources = driver.BLE_HCI_REMOTE_DEV_TERMINATION_DUE_TO_LOW_RESOURCES
    remote_dev_termination_due_to_power_off = driver.BLE_HCI_REMOTE_DEV_TERMINATION_DUE_TO_POWER_OFF
    local_host_terminated_connection = driver.BLE_HCI_LOCAL_HOST_TERMINATED_CONNECTION
    unsupported_remote_feature = driver.BLE_HCI_UNSUPPORTED_REMOTE_FEATURE
    invalid_lmp_parameters = driver.BLE_HCI_STATUS_CODE_INVALID_LMP_PARAMETERS
    unspecified_error = driver.BLE_HCI_STATUS_CODE_UNSPECIFIED_ERROR
    lmp_response_timeout = driver.BLE_HCI_STATUS_CODE_LMP_RESPONSE_TIMEOUT
    lmp_pdu_not_allowed = driver.BLE_HCI_STATUS_CODE_LMP_PDU_NOT_ALLOWED
    instant_passed = driver.BLE_HCI_INSTANT_PASSED
    pairintg_with_unit_key_unsupported = driver.BLE_HCI_PAIRING_WITH_UNIT_KEY_UNSUPPORTED
    differen_transaction_collision = driver.BLE_HCI_DIFFERENT_TRANSACTION_COLLISION
    controller_busy = driver.BLE_HCI_CONTROLLER_BUSY
    conn_interval_unacceptable = driver.BLE_HCI_CONN_INTERVAL_UNACCEPTABLE
    directed_advertiser_timeout = driver.BLE_HCI_DIRECTED_ADVERTISER_TIMEOUT
    conn_terminated_due_to_mic_failure = driver.BLE_HCI_CONN_TERMINATED_DUE_TO_MIC_FAILURE
    conn_failed_to_be_established = driver.BLE_HCI_CONN_FAILED_TO_BE_ESTABLISHED


class NrfError(Enum):
    success = driver.NRF_SUCCESS
    svc_handler_missing = driver.NRF_ERROR_SVC_HANDLER_MISSING
    softdevice_not_enabled = driver.NRF_ERROR_SOFTDEVICE_NOT_ENABLED
    internal = driver.NRF_ERROR_INTERNAL
    no_mem = driver.NRF_ERROR_NO_MEM
    not_found = driver.NRF_ERROR_NOT_FOUND
    not_supported = driver.NRF_ERROR_NOT_SUPPORTED
    invalid_param = driver.NRF_ERROR_INVALID_PARAM
    invalid_state = driver.NRF_ERROR_INVALID_STATE
    invalid_length = driver.NRF_ERROR_INVALID_LENGTH
    invalid_flags = driver.NRF_ERROR_INVALID_FLAGS
    invalid_data = driver.NRF_ERROR_INVALID_DATA
    data_size = driver.NRF_ERROR_DATA_SIZE
    timeout = driver.NRF_ERROR_TIMEOUT
    null = driver.NRF_ERROR_NULL
    forbidden = driver.NRF_ERROR_FORBIDDEN
    invalid_addr = driver.NRF_ERROR_INVALID_ADDR
    busy = driver.NRF_ERROR_BUSY
    conn_count = driver.NRF_ERROR_CONN_COUNT
    resources = driver.NRF_ERROR_RESOURCES

    # sdm_lfclk_source_unknown                    = driver.NRF_ERROR_SDM_LFCLK_SOURCE_UNKNOWN
    # sdm_incorrect_interrupt_configuration       = driver.NRF_ERROR_SDM_INCORRECT_INTERRUPT_CONFIGURATION
    # sdm_incorrect_clenr0                        = driver.NRF_ERROR_SDM_INCORRECT_CLENR0

    # soc_mutex_already_taken                     = driver.NRF_ERROR_SOC_MUTEX_ALREADY_TAKEN
    # soc_nvic_interrupt_not_available            = driver.NRF_ERROR_SOC_NVIC_INTERRUPT_NOT_AVAILABLE
    # soc_nvic_interrupt_priority_not_allowed     = driver.NRF_ERROR_SOC_NVIC_INTERRUPT_PRIORITY_NOT_ALLOWED
    # soc_nvic_should_not_return                  = driver.NRF_ERROR_SOC_NVIC_SHOULD_NOT_RETURN
    # soc_power_mode_unknown                      = driver.NRF_ERROR_SOC_POWER_MODE_UNKNOWN
    # soc_power_pof_threshold_unknown             = driver.NRF_ERROR_SOC_POWER_POF_THRESHOLD_UNKNOWN
    # soc_power_off_should_not_return             = driver.NRF_ERROR_SOC_POWER_OFF_SHOULD_NOT_RETURN
    # soc_rand_not_enough_values                  = driver.NRF_ERROR_SOC_RAND_NOT_ENOUGH_VALUES
    # soc_ppi_invalid_channel                     = driver.NRF_ERROR_SOC_PPI_INVALID_CHANNEL
    # soc_ppi_invalid_group                       = driver.NRF_ERROR_SOC_PPI_INVALID_GROUP

    # ble_error_not_enabled                       = driver.BLE_ERROR_NOT_ENABLED
    # ble_error_invalid_conn_handle               = driver.BLE_ERROR_INVALID_CONN_HANDLE
    # ble_error_invalid_attr_handle               = driver.BLE_ERROR_INVALID_ATTR_HANDLE
    # ble_error_invalid_role                      = driver.BLE_ERROR_INVALID_ROLE

    # ble_error_gap_uuid_list_mismatch            = driver.BLE_ERROR_GAP_UUID_LIST_MISMATCH
    # ble_error_gap_discoverable_with_whitelist   = driver.BLE_ERROR_GAP_DISCOVERABLE_WITH_WHITELIST
    # ble_error_gap_invalid_ble_addr              = driver.BLE_ERROR_GAP_INVALID_BLE_ADDR
    # ble_error_gap_whitelist_in_use              = driver.BLE_ERROR_GAP_WHITELIST_IN_USE
    # ble_error_gap_device_identities_in_use      = driver.BLE_ERROR_GAP_DEVICE_IDENTITIES_IN_USE
    # ble_error_gap_device_identities_duplicate   = driver.BLE_ERROR_GAP_DEVICE_IDENTITIES_DUPLICATE

    # ble_error_gattc_proc_not_permitted          = driver.BLE_ERROR_GATTC_PROC_NOT_PERMITTED

    # ble_error_gatts_invalid_attr_type           = driver.BLE_ERROR_GATTS_INVALID_ATTR_TYPE
    # ble_error_gatts_sys_attr_missing            = driver.BLE_ERROR_GATTS_SYS_ATTR_MISSING


class BLEUUIDBase(object):
    def __init__(self, vs_uuid_base=None, uuid_type=None):
        assert isinstance(vs_uuid_base, (list, NoneType)), 'Invalid argument type'
        assert isinstance(uuid_type, (int, long, NoneType)), 'Invalid argument type'
        if vs_uuid_base is None:
            self.base = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00,
                         0x80, 0x00, 0x00, 0x80, 0x5F, 0x9B, 0x34, 0xFB]
            self.def_base = True
        else:
            self.base = vs_uuid_base
            self.def_base = False

        if uuid_type is None:
            self.type = driver.BLE_UUID_TYPE_BLE
        else:
            self.type = uuid_type

    def __eq__(self, other):
        if not isinstance(other, BLEUUIDBase):
            return False
        if self.base != other.base:
            return False
        if self.type != other.type:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_c(cls, uuid):
        if uuid.type == driver.BLE_UUID_TYPE_BLE:
            return cls(uuid_type=uuid.type)
        else:
            return cls([0] * 16, uuid_type=uuid.type)  # TODO: Hmmmm? [] or [None]*16? what?

    def to_c(self):
        lsb_list = self.base[::-1]
        self.__array = util.list_to_uint8_array(lsb_list)
        uuid = driver.ble_uuid128_t()
        uuid.uuid128 = self.__array.cast()
        return uuid


class BLEUUID(object):
    class Standard(Enum):
        unknown = 0x0000
        service_primary = 0x2800
        service_secondary = 0x2801
        characteristic = 0x2803
        cccd = 0x2902
        battery_level = 0x2A19
        heart_rate = 0x2A37

    def __init__(self, value, base=BLEUUIDBase()):
        assert isinstance(base, BLEUUIDBase), 'Invalid argument type'
        self.base = base
        if self.base.def_base:
            try:
                self.value = value if isinstance(value, BLEUUID.Standard) else BLEUUID.Standard(value)
            except ValueError:
                self.value = value
        else:
            self.value = value

    def get_value(self):
        if isinstance(self.value, BLEUUID.Standard):
            return self.value.value
        return self.value

    def as_array(self):
        base_and_value = self.base.base[:]
        base_and_value[2] = (self.get_value() >> 8) & 0xff
        base_and_value[3] = (self.get_value() >> 0) & 0xff
        return base_and_value

    def __str__(self):
        if isinstance(self.value, BLEUUID.Standard):
            return '0x{:04X} ({})'.format(self.value.value, self.value)
        elif self.base.type == driver.BLE_UUID_TYPE_BLE and self.base.def_base:
            return '0x{:04X}'.format(self.value)
        else:
            base_and_value = self.base.base[:]
            base_and_value[2] = (self.value >> 8) & 0xff
            base_and_value[3] = (self.value >> 0) & 0xff
            return '0x{}'.format(''.join(['{:02X}'.format(i) for i in base_and_value]))

    def __eq__(self, other):
        if not isinstance(other, BLEUUID):
            return False
        if not self.base == other.base:
            return False
        if not self.value == other.value:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_c(cls, uuid):
        return cls(value=uuid.uuid, base=BLEUUIDBase.from_c(uuid))  # TODO: Is this correct?

    def to_c(self):
        assert self.base.type is not None, 'Vendor specific UUID not registered'
        uuid = driver.ble_uuid_t()
        if isinstance(self.value, BLEUUID.Standard):
            uuid.uuid = self.value.value
        else:
            uuid.uuid = self.value
        uuid.type = self.base.type
        return uuid

    @classmethod
    def from_array(cls, uuid_array_lt):
        base = list(reversed(uuid_array_lt))
        uuid = (base[2] << 8) + base[3]
        base[2] = 0
        base[3] = 0
        return cls(value=uuid, base=BLEUUIDBase(base, 0))


class BLEEnableParams(object):
    def __init__(self,
                 vs_uuid_count,
                 service_changed,
                 periph_conn_count,
                 central_conn_count,
                 central_sec_count,
                 attr_tab_size=driver.BLE_GATTS_ATTR_TAB_SIZE_DEFAULT):
        self.vs_uuid_count = vs_uuid_count
        self.attr_tab_size = attr_tab_size
        self.service_changed = service_changed
        self.periph_conn_count = periph_conn_count
        self.central_conn_count = central_conn_count
        self.central_sec_count = central_sec_count

    def to_c(self):
        ble_enable_params = driver.ble_enable_params_t()
        ble_enable_params.common_enable_params.p_conn_bw_counts = None
        ble_enable_params.common_enable_params.vs_uuid_count = self.vs_uuid_count
        ble_enable_params.gatts_enable_params.attr_tab_size = self.attr_tab_size
        ble_enable_params.gatts_enable_params.service_changed = self.service_changed
        ble_enable_params.gap_enable_params.periph_conn_count = self.periph_conn_count
        ble_enable_params.gap_enable_params.central_conn_count = self.central_conn_count
        ble_enable_params.gap_enable_params.central_sec_count = self.central_sec_count

        return ble_enable_params
