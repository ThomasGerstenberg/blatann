from blatann.nrf.nrf_events.generic_events import *
from blatann.nrf.nrf_events.gap_events import *
from blatann.nrf.nrf_events.smp_events import *
from blatann.nrf.nrf_events.gatt_events import *


_event_classes = [
    EvtUserMemoryRequest,

    # Gap
    GapEvtConnected,
    GapEvtDisconnected,
    GapEvtConnParamUpdate,
    GapEvtRssiChanged,
    GapEvtAdvReport,
    GapEvtTimeout,
    GapEvtConnParamUpdateRequest,
    GapEvtDataLengthUpdate,
    GapEvtDataLengthUpdateRequest,
    GapEvtPhyUpdate,
    GapEvtPhyUpdateRequest,

    # SMP
    GapEvtSecParamsRequest,
    GapEvtAuthKeyRequest,
    GapEvtConnSecUpdate,
    GapEvtAuthStatus,
    GapEvtPasskeyDisplay,
    GapEvtSecInfoRequest,
    GapEvtLescDhKeyRequest,
    GapEvtSecRequest,

    # Gattc
    GattcEvtPrimaryServiceDiscoveryResponse,
    GattcEvtCharacteristicDiscoveryResponse,
    GattcEvtDescriptorDiscoveryResponse,
    GattcEvtReadResponse,
    GattcEvtWriteResponse,
    GattcEvtHvx,
    GattcEvtAttrInfoDiscoveryResponse,
    GattcEvtMtuExchangeResponse,
    GattcEvtTimeout,
    GattcEvtWriteCmdTxComplete,
    # TODO:
    # driver.BLE_GATTC_EVT_REL_DISC_RSP
    # driver.BLE_GATTC_EVT_CHAR_VAL_BY_UUID_READ_RSP
    # driver.BLE_GATTC_EVT_CHAR_VALS_READ_RSP

    # Gatts
    GattsEvtWrite,
    GattsEvtReadWriteAuthorizeRequest,
    GattsEvtHandleValueConfirm,
    GattsEvtExchangeMtuRequest,
    GattsEvtNotificationTxComplete,
    GattsEvtTimeout,
    GattsEvtSysAttrMissing
    # TODO:
    # driver.BLE_GATTS_EVT_SC_CONFIRM
]

_events_by_id = {e.evt_id: e for e in _event_classes}


def event_decode(ble_event):
    event_cls = _events_by_id.get(ble_event.header.evt_id, None)
    if event_cls:
        return event_cls.from_c(ble_event)
    return None
