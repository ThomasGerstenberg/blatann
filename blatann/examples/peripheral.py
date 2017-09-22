from blatann import BleDevice
from blatann.uuid import Uuid128
from blatann.nrf.nrf_types import BLEAdvData
from blatann.nrf.nrf_events import GapEvtDisconnected
from blatann.nrf.nrf_event_sync import EventSync
from blatann import gatt
import time


def on_connect(peer):
    """
    :type peer: blatann.peer.Peer or None
    """
    if peer:
        print("Connected to peer")
    else:
        print("Connection timed out")


def on_gatts_characteristic_write(characteristic, value):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type value: bytearray
    """
    print("Got characteristic write - characteristic: {}, data: 0x{}".format(characteristic.uuid,
                                                                             str(value).encode("hex")))
    new_value = "Hello, {}".format(str(value).encode("hex"))
    characteristic.set_value(new_value, True)


def on_gatts_subscription_state_changed(characteristic, new_state):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type new_state: blatann.gatt.SubscriptionState
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
    char1_uuid = service_uuid.new_uuid_from_base(0xbeaa)
    time_char_uuid = service_uuid.new_uuid_from_base("beee")

    service2_base_uuid = "beef0000-0123-4567-89ab-cdef01234567"
    service2_uuid = Uuid128.combine_with_base("dead", service2_base_uuid)

    service = ble_device.peripheral.database.add_service(service_uuid)

    char1_props = gatt.CharacteristicProperties(read=True, notify=True, indicate=True, write=True, max_length=30,
                                                variable_length=True)
    char1 = service.add_characteristic(char1_uuid, char1_props, "Test Data")
    char1.on_write.register(on_gatts_characteristic_write)
    char1.on_subscription_change.register(on_gatts_subscription_state_changed)

    time_char_props = gatt.CharacteristicProperties(read=True, max_length=30, variable_length=True)
    time_char = service.add_characteristic(time_char_uuid, time_char_props, "Time")
    time_char.on_read.register(on_time_char_read)

    service_2 = ble_device.peripheral.database.add_service(service2_uuid)

    ble_device.peripheral.set_advertise_data(BLEAdvData(complete_local_name='Periph Test'))

    print("Advertising")
    peer = ble_device.peripheral.advertise().then(on_connect).wait(30, False)
    if not peer:
        return
    with EventSync(ble_device.ble_driver, GapEvtDisconnected) as sync:
        event = sync.get(timeout=600)
    
    print("Done")
    

if __name__ == '__main__':
    main()
