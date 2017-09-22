from blatann import BleDevice
from blatann.uuid import Uuid128
from blatann.nrf.nrf_types import BLEAdvData
from blatann.nrf.nrf_events import GapEvtDisconnected
from blatann.nrf.nrf_event_sync import EventSync
from blatann import gatt
import time


def on_gatts_characteristic_write(characteristic):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    """
    print("Got characteristic write - characteristic: {}, data: 0x{}".format(characteristic.uuid,
                                                                             str(characteristic.value).encode("hex")))
    new_value = "Hello, {}".format(str(characteristic.value).encode("hex"))
    characteristic.set_value(new_value, True)


def on_gatts_subscription_state_changed(characteristic, new_state):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    """
    print("Subscription state changed - characteristic: {}, state: {}".format(characteristic.uuid, new_state))


def on_time_char_read(characteristic):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    """
    t = time.time()
    ms = int((t * 1000) % 1000)
    msg = "Time: {}.{:03}".format(time.strftime("%H:%M:%S", time.localtime(t)), ms)
    characteristic.set_value(msg)


def main():
    ble_device = BleDevice("COM3")

    service_uuid = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
    service = ble_device.peripheral.database.add_service(service_uuid)

    props1 = gatt.CharacteristicProperties(read=True, notify=True, indicate=True, write=True, max_length=30, variable_length=True)
    char1 = service.add_characteristic(Uuid128("deadbeaa-0011-2345-6679-ab12ccd4f550"), props1, "Test Data")
    char1.on_write.register(on_gatts_characteristic_write)
    char1.on_subscription_change.register(on_gatts_subscription_state_changed)

    time_char_props = gatt.CharacteristicProperties(read=True, max_length=30, variable_length=True)
    time_char = service.add_characteristic(Uuid128("deadbeee-0011-2345-6679-ab12ccd4f550"), time_char_props, "Time")
    time_char.on_read.register(on_time_char_read)

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
