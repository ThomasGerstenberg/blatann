from blatann.nrf.nrf_events.generic_events import *
from blatann.nrf.nrf_events.gap_events import *
from blatann.nrf.nrf_events.smp_events import *
from blatann.nrf.nrf_events.gatt_events import *


def event_decode(ble_event):
    event_classes = [
        EvtTxComplete,

        # Gap
        GapEvtAdvReport,
        GapEvtConnected,
        GapEvtDisconnected,
        GapEvtTimeout,

        GapEvtConnParamUpdateRequest,
        GapEvtConnParamUpdate,

        # SMP
        GapEvtSecParamsRequest,
        GapEvtAuthKeyRequest,
        GapEvtConnSecUpdate,
        GapEvtAuthStatus,
        GapEvtPasskeyDisplay,
        # driver.BLE_GAP_EVT_SEC_INFO_REQUEST,
        # driver.BLE_GAP_EVT_SEC_REQUEST,

        # Gattc
        GattcEvtReadResponse,
        GattcEvtHvx,
        GattcEvtWriteResponse,
        GattcEvtPrimaryServiceDiscoveryResponse,
        GattcEvtCharacteristicDiscoveryResponse,
        GattcEvtDescriptorDiscoveryResponse
    ]

    for event_class in event_classes:
        if ble_event.header.evt_id == event_class.evt_id:
            return event_class.from_c(ble_event)
