import atexit
import struct
import threading
import time

from blatann import BleDevice
from blatann.examples import example_utils, constants
from blatann.gap import advertising, smp
from blatann.nrf.nrf_event_sync import EventSync

logger = example_utils.setup_logger(level="DEBUG")


def on_connect(peer, event_args):
    """
    :type peer: blatann.peer.Peer
    :type event_args: None
    """
    if peer:
        logger.info("Connected to peer")
    else:
        logger.warning("Connection timed out")


def on_disconnect(peer, event_args):
    logger.info("Disconnected from peer, reason: {}".format(event_args.reason))


def on_gatts_characteristic_write(characteristic, event_args):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type event_args: blatann.event_args.WriteEventArgs
    """
    logger.info("Got characteristic write - characteristic: {}, data: 0x{}".format(characteristic.uuid,
                                                                                   str(event_args.value).encode("hex")))
    new_value = "{}".format(str(event_args.value).encode("hex"))
    characteristic.set_value(new_value[:characteristic.max_length], True)


def on_gatts_subscription_state_changed(characteristic, event_args):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type event_args: blatann.event_args.SubscriptionStateChangeEventArgs
    """
    logger.info("Subscription state changed - characteristic: {}, state: {}".format(characteristic.uuid, event_args.subscription_state))


def on_time_char_read(characteristic, event_args):
    """
    :type characteristic: blatann.gatts.GattsCharacteristic
    :type event_args: None
    """
    t = time.time()
    ms = int((t * 1000) % 1000)
    msg = "Time: {}.{:03}".format(time.strftime("%H:%M:%S", time.localtime(t)), ms)
    characteristic.set_value(msg)


def on_client_pairing_complete(peer, event_args):
    """
    :param peer:
    :type event_args: blatann.event_args.PairingCompleteEventArgs
    """
    logger.info("Client Pairing complete, status: {}".format(event_args.status))


def on_passkey_display(peer, event_args):
    """

    :param peer:
    :type event_args: blatann.event_args.PasskeyDisplayEventArgs
    """
    logger.info("Passkey display: {}, match: {}".format(event_args.passkey, event_args.match_request))


class CountingCharacteristicThread(object):
    def __init__(self, characteristic):
        """
        :type characteristic: blatann.gatt.gatts.GattsCharacteristic
        """
        self.current_value = 0
        self._stop_event = threading.Event()
        self._stopped = threading.Event()
        self.characteristic = characteristic
        self.characteristic.on_notify_complete.register(self._on_notify_complete)
        self.thread = threading.Thread(target=self.run)
        atexit.register(self.join)
        self.thread.daemon = True
        self.thread.start()

    def join(self):
        self._stop_event.set()
        self._stopped.wait(3)

    def _on_notify_complete(self, characteristic, event_args):
        logger.info("Notification Complete, id: {}, reason: {}".format(event_args.id, event_args.reason))

    def run(self):
        while not self._stop_event.is_set():

            try:
                if not self.characteristic.client_subscribed:
                    continue
                self.current_value += 1
                value = struct.pack("<I", self.current_value)
                waitable = self.characteristic.notify(value)
                # Send a burst of 16, then wait for them all to send before trying to send more
                if self.current_value % 16 == 0:
                    waitable.wait()
            except Exception as e:
                logger.exception(e)

        self._stopped.set()


def main(serial_port):
    ble_device = BleDevice(serial_port)
    ble_device.open()

    # Set up desired security parameters
    ble_device.client.security.set_security_params(True, smp.IoCapabilities.DISPLAY_ONLY, False, False)
    ble_device.client.security.on_pairing_complete.register(on_client_pairing_complete)
    ble_device.client.security.on_passkey_display_required.register(on_passkey_display)

    service = ble_device.database.add_service(constants.MATH_SERVICE_UUID)

    char1 = service.add_characteristic(constants.HEX_CONVERT_CHAR_UUID, constants.HEX_CONVERT_CHAR_PROPERTIES, "Test Data")
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
    ble_device.close()
    

if __name__ == '__main__':
    main("COM49")
