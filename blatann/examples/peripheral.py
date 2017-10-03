import atexit
import time
import threading
import struct
from blatann import BleDevice
from blatann.uuid import Uuid128
from blatann.nrf.nrf_events import GapEvtDisconnected
from blatann.nrf.nrf_event_sync import EventSync
from blatann import gatt, gatts, advertising
from blatann.examples import example_utils, constants

logger = example_utils.setup_logger(level="DEBUG")


def on_connect(peer):
    """
    :type peer: blatann.peer.Peer or None
    """
    if peer:
        logger.info("Connected to peer")
    else:
        logger.warning("Connection timed out")


def on_disconnect(peer, reason):
    logger.info("Disconnected from peer, reason: {}".format(reason))


def on_gatts_characteristic_write(characteristic, value):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type value: bytearray
    """
    logger.info("Got characteristic write - characteristic: {}, data: 0x{}".format(characteristic.uuid,
                                                                                   str(value).encode("hex")))
    new_value = "{}".format(str(value).encode("hex"))
    characteristic.set_value(new_value[:characteristic.max_length], True)


def on_gatts_subscription_state_changed(characteristic, new_state):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type new_state: blatann.gatt.SubscriptionState
    """
    logger.info("Subscription state changed - characteristic: {}, state: {}".format(characteristic.uuid, new_state))


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
            try:
                self.characteristic.set_value(value, notify_client=True)
            except Exception as e:
                logger.error(e)
        self._stopped.set()


def main(serial_port):
    ble_device = BleDevice(serial_port)

    service = ble_device.database.add_service(constants.SERVICE1_UUID)

    char1 = service.add_characteristic(constants.CHAR1_UUID, constants.CHAR1_PROPERTIES, "Test Data")
    char1.on_write.register(on_gatts_characteristic_write)
    char1.on_subscription_change.register(on_gatts_subscription_state_changed)

    counting_char = service.add_characteristic(constants.COUNTING_CHAR_UUID, constants.COUNTING_CHAR_PROPERTIES, [0]*4)
    counting_char.on_subscription_change.register(on_gatts_subscription_state_changed)
    counting_char_thread = CountingCharacteristicThread(counting_char)

    time_service = ble_device.database.add_service(constants.TIME_SERVICE_UUID)
    time_char = time_service.add_characteristic(constants.TIME_CHAR_UUID, constants.TIME_CHAR_PROPERTIES, "Time")
    time_char.on_read.register(on_time_char_read)

    adv_data = advertising.AdvertisingData(local_name=constants.PERIPHERAL_NAME, flags=0x06)
    scan_data = advertising.AdvertisingData(service_uuid128s=constants.TIME_SERVICE_UUID, has_more_uuid128_services=True)
    ble_device.advertiser.set_advertise_data(adv_data, scan_data)

    logger.info("Advertising")
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)
    with EventSync(ble_device.ble_driver, int) as sync:
        event = sync.get(timeout=60*30)  # Advertise for 30 mins
    counting_char_thread.join()
    logger.info("Done")
    

if __name__ == '__main__':
    main("COM3")
