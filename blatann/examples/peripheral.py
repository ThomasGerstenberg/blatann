from blatann import BleDevice
from blatann.uuid import Uuid128
from blatann.nrf.nrf_types import BLEAdvData
from blatann.nrf.nrf_events import GapEvtDisconnected
from blatann.nrf.nrf_event_sync import EventSync
from blatann import gatt


def on_gatts_characteristic_write(characteristic):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    """
    print("Got characteristic write - characteristic: {}, data: 0x{}".format(characteristic.uuid,
                                                                             str(characteristic.value).encode("hex")))


def on_gatts_subscription_state_changed(characteristic, new_state):
    print("Subscription state changed - characteristic: {}, state: {}".format(characteristic, new_state))


def main():
    ble_device = BleDevice("COM3")
    service_uuid = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
    service = ble_device.peripheral.database.add_service(service_uuid)
    props = gatt.CharacteristicProperties(read=True, notify=True, write=True, max_length=30, variable_length=True)
    char1 = service.add_characteristic(Uuid128("deadbeaa-0011-2345-6679-ab12ccd4f550"), props, "Test Data")
    char1.register_on_write(on_gatts_characteristic_write)
    char1.register_on_subscription_change(on_gatts_subscription_state_changed)
    ble_device.peripheral.set_advertise_data(BLEAdvData(complete_local_name='Thomas Test'))
    ble_device.peripheral.advertise()
    print("Advertising")
    event = ble_device.wait_for_connection()
    if event:
        print("Connected, event: {}".format(event))
    else:
        print("Connection timeout")
        return
    with EventSync(ble_device.ble_driver, GapEvtDisconnected) as sync:
        event = sync.get(timeout=600)
    
    print("Done")
    


if __name__ == '__main__':
    main()
