from enum import Enum, IntEnum, IntFlag
from blatann.nrf.nrf_dll_load import driver

"""
Generic Enums
"""


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
    lmp_transaction_collision = driver.BLE_HCI_STATUS_CODE_LMP_ERROR_TRANSACTION_COLLISION
    lmp_pdu_not_allowed = driver.BLE_HCI_STATUS_CODE_LMP_PDU_NOT_ALLOWED
    instant_passed = driver.BLE_HCI_INSTANT_PASSED
    pairintg_with_unit_key_unsupported = driver.BLE_HCI_PAIRING_WITH_UNIT_KEY_UNSUPPORTED
    differen_transaction_collision = driver.BLE_HCI_DIFFERENT_TRANSACTION_COLLISION
    controller_busy = driver.BLE_HCI_CONTROLLER_BUSY
    conn_interval_unacceptable = driver.BLE_HCI_CONN_INTERVAL_UNACCEPTABLE
    parameter_out_of_mandatory_range = driver.BLE_HCI_PARAMETER_OUT_OF_MANDATORY_RANGE
    directed_advertiser_timeout = driver.BLE_HCI_DIRECTED_ADVERTISER_TIMEOUT
    conn_terminated_due_to_mic_failure = driver.BLE_HCI_CONN_TERMINATED_DUE_TO_MIC_FAILURE
    conn_failed_to_be_established = driver.BLE_HCI_CONN_FAILED_TO_BE_ESTABLISHED


class NrfError(Enum):
    # Generic errors
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

    # sdm_lfclk_source_unknown = driver.NRF_ERROR_SDM_LFCLK_SOURCE_UNKNOWN
    # sdm_incorrect_interrupt_configuration = driver.NRF_ERROR_SDM_INCORRECT_INTERUUPT_CONFIGURATION
    # sdm_incorrect_clenr0 = driver.NRF_ERROR_SDM_INCORRECT_CLENR0
    # soc_mutex_already_taken = driver.NRF_ERROR_SOC_MUTEX_ALREADY_TAKEN
    # soc_nvic_interrupt_not_available = driver.NRF_ERROR_SOC_NVIC_INTERRUPT_NOT_AVAILABLE
    # soc_nvic_interrupt_priority_not_allowed = driver.NRF_ERROR_SOC_NVIC_INTERRUPT_PRIORITY_NOT_ALLOWED
    # soc_nvic_should_not_return = driver.NRF_ERROR_SOC_NVIC_SHOULD_NOT_RETURN
    # soc_power_mode_unknown = driver.NRF_ERROR_SOC_POWER_MODE_UNKNOWN
    # soc_power_pof_threshold_unknown = driver.NRF_ERROR_SOC_POWER_POF_THRESHOLD_UNKNOWN
    # soc_power_off_should_not_return = driver.NRF_ERROR_SOC_POWER_OFF_SHOULD_NOT_RETURN
    # soc_rand_not_enough_values = driver.NRF_ERROR_SOC_RAND_NOT_ENOUGH_VALUES
    # soc_ppi_invalid_channel = driver.NRF_ERROR_SOC_PPI_INVALID_CHANNEL
    # soc_ppi_invalid_group = driver.NRF_ERROR_SOC_PPI_INVALID_GROUP

    # Values copied from header files, should replace with driver values if ever exposed from there
    ble_not_enabled = 0x3001
    ble_invalid_conn_handle = 0x3002
    ble_invalid_attr_handle = 0x3003
    ble_invalid_adv_handle = 0x3004
    ble_invalid_role = 0x3005
    ble_blocked_by_other_links = 0x3006

    ble_gap_uuid_list_mismatch = 0x3200
    ble_gap_discoverable_with_whitelist = 0x3201
    ble_gap_invalid_ble_addr = 0x3202
    ble_gap_whitelist_in_use = 0x3203
    ble_gap_device_identities_in_use = 0x3204
    ble_gap_device_identities_duplicate = 0x3205

    ble_gattc_proc_not_permitted = 0x3300

    ble_gatts_invalid_attr_type = 0x3400
    ble_gatts_sys_attr_missing = 0x3401

    # pc-ble-driver RPC error codes
    rpc_encode = driver.NRF_ERROR_SD_RPC_ENCODE  # 32769
    rpc_decode = driver.NRF_ERROR_SD_RPC_DECODE  # 32770
    rpc_send = driver.NRF_ERROR_SD_RPC_SEND  # 32771
    rpc_invalid_argument = driver.NRF_ERROR_SD_RPC_INVALID_ARGUMENT  # 32772
    rpc_no_response = driver.NRF_ERROR_SD_RPC_NO_RESPONSE  # 32773
    rpc_invalid_state = driver.NRF_ERROR_SD_RPC_INVALID_STATE  # 32774

    rpc_serialization_transport = driver.NRF_ERROR_SD_RPC_SERIALIZATION_TRANSPORT  # 32788
    rpc_serialization_transport_invalid_state = driver.NRF_ERROR_SD_RPC_SERIALIZATION_TRANSPORT_INVALID_STATE  # 32789
    rpc_serialization_transport_no_response = driver.NRF_ERROR_SD_RPC_SERIALIZATION_TRANSPORT_NO_RESPONSE  # 32790
    rpc_serialization_transport_already_open = driver.NRF_ERROR_SD_RPC_SERIALIZATION_TRANSPORT_ALREADY_OPEN  # 32791
    rpc_serialization_transport_already_closed = driver.NRF_ERROR_SD_RPC_SERIALIZATION_TRANSPORT_ALREADY_CLOSED  # 32792

    rpc_h5_transport = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT  # 32808
    rpc_h5_transport_state = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_STATE  # 32809
    rpc_h5_transport_no_response = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_NO_RESPONSE  # 32810
    rpc_h5_transport_slip_payload_size = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_SLIP_PAYLOAD_SIZE  # 32811
    rpc_h5_transport_slip_calculated_payload_size = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_SLIP_CALCULATED_PAYLOAD_SIZE  # 32812
    rpc_h5_transport_slip_decoding = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_SLIP_DECODING  # 32813
    rpc_h5_transport_header_checksum = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_HEADER_CHECKSUM  # 32814
    rpc_h5_transport_packet_checksum = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_PACKET_CHECKSUM  # 32815
    rpc_h5_transport_already_open = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_ALREADY_OPEN  # 32816
    rpc_h5_transport_already_closed = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_ALREADY_CLOSED  # 32817

    rpc_h5_transport_internal_error = driver.NRF_ERROR_SD_RPC_H5_TRANSPORT_INTERNAL_ERROR  # 32818
    rpc_serial_port = driver.NRF_ERROR_SD_RPC_SERIAL_PORT  # 32828
    rpc_serial_port_state = driver.NRF_ERROR_SD_RPC_SERIAL_PORT_STATE  # 32829
    rpc_serial_port_already_open = driver.NRF_ERROR_SD_RPC_SERIAL_PORT_ALREADY_OPEN  # 32830
    rpc_serial_port_already_closed = driver.NRF_ERROR_SD_RPC_SERIAL_PORT_ALREADY_CLOSED  # 32831
    rpc_serial_port_internal_error = driver.NRF_ERROR_SD_RPC_SERIAL_PORT_INTERNAL_ERROR  # = 32832


"""
Gap Enums
"""

BLE_CONN_HANDLE_INVALID = driver.BLE_CONN_HANDLE_INVALID


class BLEGapAdvType(IntEnum):
    connectable_undirected = driver.BLE_GAP_ADV_TYPE_ADV_IND
    connectable_directed = driver.BLE_GAP_ADV_TYPE_ADV_DIRECT_IND
    scanable_undirected = driver.BLE_GAP_ADV_TYPE_ADV_SCAN_IND
    non_connectable_undirected = driver.BLE_GAP_ADV_TYPE_ADV_NONCONN_IND
    scan_response = 4


class BLEGapRoles(IntEnum):
    invalid = driver.BLE_GAP_ROLE_INVALID
    periph = driver.BLE_GAP_ROLE_PERIPH
    central = driver.BLE_GAP_ROLE_CENTRAL


class BLEGapTimeoutSrc(IntEnum):
    advertising = driver.BLE_GAP_TIMEOUT_SRC_ADVERTISING
    scan = driver.BLE_GAP_TIMEOUT_SRC_SCAN
    conn = driver.BLE_GAP_TIMEOUT_SRC_CONN


class BLEGapPhy(IntFlag):
    auto = driver.BLE_GAP_PHY_AUTO
    one_mbps = driver.BLE_GAP_PHY_1MBPS
    two_mbps = driver.BLE_GAP_PHY_2MBPS
    coded = driver.BLE_GAP_PHY_CODED


"""
SMP Enums
"""


class BLEGapIoCaps(IntEnum):
    DISPLAY_ONLY = driver.BLE_GAP_IO_CAPS_DISPLAY_ONLY
    DISPLAY_YESNO = driver.BLE_GAP_IO_CAPS_DISPLAY_YESNO
    KEYBOARD_ONLY = driver.BLE_GAP_IO_CAPS_KEYBOARD_ONLY
    NONE = driver.BLE_GAP_IO_CAPS_NONE
    KEYBOARD_DISPLAY = driver.BLE_GAP_IO_CAPS_KEYBOARD_DISPLAY


class BLEGapAuthKeyType(IntEnum):
    NONE = driver.BLE_GAP_AUTH_KEY_TYPE_NONE
    OOB = driver.BLE_GAP_AUTH_KEY_TYPE_OOB
    PASSKEY = driver.BLE_GAP_AUTH_KEY_TYPE_PASSKEY


class BLEGapSecStatus(IntEnum):
    success = driver.BLE_GAP_SEC_STATUS_SUCCESS
    timeout = driver.BLE_GAP_SEC_STATUS_TIMEOUT
    pdu_invalid = driver.BLE_GAP_SEC_STATUS_PDU_INVALID
    passkey_entry_failed = driver.BLE_GAP_SEC_STATUS_PASSKEY_ENTRY_FAILED
    oob_not_available = driver.BLE_GAP_SEC_STATUS_OOB_NOT_AVAILABLE
    auth_req = driver.BLE_GAP_SEC_STATUS_AUTH_REQ
    confirm_value = driver.BLE_GAP_SEC_STATUS_CONFIRM_VALUE
    pairing_not_supp = driver.BLE_GAP_SEC_STATUS_PAIRING_NOT_SUPP
    enc_key_size = driver.BLE_GAP_SEC_STATUS_ENC_KEY_SIZE
    smp_cmd_unsupported = driver.BLE_GAP_SEC_STATUS_SMP_CMD_UNSUPPORTED
    unspecified = driver.BLE_GAP_SEC_STATUS_UNSPECIFIED
    repeated_attempts = driver.BLE_GAP_SEC_STATUS_REPEATED_ATTEMPTS
    invalid_params = driver.BLE_GAP_SEC_STATUS_INVALID_PARAMS
    dhkey_failure = driver.BLE_GAP_SEC_STATUS_DHKEY_FAILURE
    num_comp_failure = driver.BLE_GAP_SEC_STATUS_NUM_COMP_FAILURE
    br_edr_in_prog = driver.BLE_GAP_SEC_STATUS_BR_EDR_IN_PROG
    x_trans_key_disallowed = driver.BLE_GAP_SEC_STATUS_X_TRANS_KEY_DISALLOWED


"""
GATT Enums
"""


class BLEGattWriteOperation(Enum):
    invalid = driver.BLE_GATT_OP_INVALID
    write_req = driver.BLE_GATT_OP_WRITE_REQ
    write_cmd = driver.BLE_GATT_OP_WRITE_CMD
    signed_write_cmd = driver.BLE_GATT_OP_SIGN_WRITE_CMD
    prepare_write_req = driver.BLE_GATT_OP_PREP_WRITE_REQ
    execute_write_req = driver.BLE_GATT_OP_EXEC_WRITE_REQ


class BLEGattHVXType(Enum):
    invalid = driver.BLE_GATT_HVX_INVALID
    notification = driver.BLE_GATT_HVX_NOTIFICATION
    indication = driver.BLE_GATT_HVX_INDICATION


class BLEGattStatusCode(Enum):
    success = driver.BLE_GATT_STATUS_SUCCESS
    unknown = driver.BLE_GATT_STATUS_UNKNOWN
    invalid = driver.BLE_GATT_STATUS_ATTERR_INVALID
    invalid_handle = driver.BLE_GATT_STATUS_ATTERR_INVALID_HANDLE
    read_not_permitted = driver.BLE_GATT_STATUS_ATTERR_READ_NOT_PERMITTED
    write_not_permitted = driver.BLE_GATT_STATUS_ATTERR_WRITE_NOT_PERMITTED
    invalid_pdu = driver.BLE_GATT_STATUS_ATTERR_INVALID_PDU
    insuf_authentication = driver.BLE_GATT_STATUS_ATTERR_INSUF_AUTHENTICATION
    request_not_supported = driver.BLE_GATT_STATUS_ATTERR_REQUEST_NOT_SUPPORTED
    invalid_offset = driver.BLE_GATT_STATUS_ATTERR_INVALID_OFFSET
    insuf_authorization = driver.BLE_GATT_STATUS_ATTERR_INSUF_AUTHORIZATION
    prepare_queue_full = driver.BLE_GATT_STATUS_ATTERR_PREPARE_QUEUE_FULL
    attribute_not_found = driver.BLE_GATT_STATUS_ATTERR_ATTRIBUTE_NOT_FOUND
    attribute_not_long = driver.BLE_GATT_STATUS_ATTERR_ATTRIBUTE_NOT_LONG
    insuf_enc_key_size = driver.BLE_GATT_STATUS_ATTERR_INSUF_ENC_KEY_SIZE
    invalid_att_val_length = driver.BLE_GATT_STATUS_ATTERR_INVALID_ATT_VAL_LENGTH
    unlikely_error = driver.BLE_GATT_STATUS_ATTERR_UNLIKELY_ERROR
    insuf_encryption = driver.BLE_GATT_STATUS_ATTERR_INSUF_ENCRYPTION
    unsupported_group_type = driver.BLE_GATT_STATUS_ATTERR_UNSUPPORTED_GROUP_TYPE
    insuf_resources = driver.BLE_GATT_STATUS_ATTERR_INSUF_RESOURCES
    rfu_range1_begin = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE1_BEGIN
    rfu_range1_end = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE1_END
    app_begin = driver.BLE_GATT_STATUS_ATTERR_APP_BEGIN
    app_end = driver.BLE_GATT_STATUS_ATTERR_APP_END
    rfu_range2_begin = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE2_BEGIN
    rfu_range2_end = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE2_END
    rfu_range3_begin = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE3_BEGIN
    rfu_range3_end = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE3_END
    cps_cccd_config_error = driver.BLE_GATT_STATUS_ATTERR_CPS_CCCD_CONFIG_ERROR
    cps_proc_alr_in_prog = driver.BLE_GATT_STATUS_ATTERR_CPS_PROC_ALR_IN_PROG
    cps_out_of_range = driver.BLE_GATT_STATUS_ATTERR_CPS_OUT_OF_RANGE


class BLEGattExecWriteFlag(Enum):
    prepared_cancel = driver.BLE_GATT_EXEC_WRITE_FLAG_PREPARED_CANCEL
    prepared_write = driver.BLE_GATT_EXEC_WRITE_FLAG_PREPARED_WRITE
    unused = 0x00

"""
GATTC Enums
"""


"""
GATTS Enums
"""


class BLEGattsWriteOperation(Enum):
    invalid = driver.BLE_GATTS_OP_INVALID
    write_req = driver.BLE_GATTS_OP_WRITE_REQ
    write_cmd = driver.BLE_GATTS_OP_WRITE_CMD
    sign_write_cmd = driver.BLE_GATTS_OP_SIGN_WRITE_CMD
    prep_write_req = driver.BLE_GATTS_OP_PREP_WRITE_REQ
    exec_write_req_cancel = driver.BLE_GATTS_OP_EXEC_WRITE_REQ_CANCEL
    exec_write_req_now = driver.BLE_GATTS_OP_EXEC_WRITE_REQ_NOW
