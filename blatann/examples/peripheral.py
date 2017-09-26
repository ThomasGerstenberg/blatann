import atexit
import time
import threading
import struct
from blatann import BleDevice
from blatann.uuid import Uuid128
from blatann.nrf.nrf_events import GapEvtDisconnected
from blatann.nrf.nrf_event_sync import EventSync
from blatann import gatt, advertising


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


class CountingCharacteristicThread(object):
    def __init__(self, characteristic):
        self.current_value = 0
        self._stop_event = threading.Event()
        self._stopped = threading.Event()
        self.characteristic = characteristic
        self.thread = threading.Thread(target=self.run)
        atexit.register(self.join)
        self.thread.daemon = True
        self.thread.start()

    def join(self):
        self._stop_event.set()
        self._stopped.wait(3)

    def run(self):
        while not self._stop_event.is_set():
            time.sleep(1)
            self.current_value += 1
            value = struct.pack("<I", self.current_value)
            self.characteristic.set_value(value, notify_client=True)
        self._stopped.set()


def main(serial_port):
    ble_device = BleDevice(serial_port)

    service_uuid = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
    char1_uuid = service_uuid.new_uuid_from_base(0xbeaa)
    counting_char_uuid = service_uuid.new_uuid_from_base("1234")

    time_service_base_uuid = "beef0000-0123-4567-89ab-cdef01234567"
    time_service_uuid = Uuid128.combine_with_base("dead", time_service_base_uuid)
    time_char_uuid = time_service_uuid.new_uuid_from_base("dddd")

    service = ble_device.database.add_service(service_uuid)

    char1_props = gatt.CharacteristicProperties(read=True, notify=True, indicate=True, write=True, max_length=30,
                                                variable_length=True)
    char1 = service.add_characteristic(char1_uuid, char1_props, "Test Data")
    char1.on_write.register(on_gatts_characteristic_write)
    char1.on_subscription_change.register(on_gatts_subscription_state_changed)

    counting_char_props = gatt.CharacteristicProperties(read=False, notify=True, max_length=4, variable_length=False)
    counting_char = service.add_characteristic(counting_char_uuid, counting_char_props, [0]*4)
    counting_char_thread = CountingCharacteristicThread(counting_char)

    time_service = ble_device.database.add_service(time_service_uuid)
    time_char_props = gatt.CharacteristicProperties(read=True, max_length=30, variable_length=True)
    time_char = time_service.add_characteristic(time_char_uuid, time_char_props, "Time")
    time_char.on_read.register(on_time_char_read)

    ble_device.advertiser.set_advertise_data(advertising.AdvertisingData(complete_local_name='Periph Test'))

    print("Advertising")
    peer = ble_device.advertiser.start().then(on_connect).wait(300, False)
    if not peer:
        return
    with EventSync(ble_device.ble_driver, GapEvtDisconnected) as sync:
        event = sync.get(timeout=600)
    counting_char_thread.join()
    print("Done")
    

if __name__ == '__main__':
    main("COM3")
