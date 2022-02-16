"""
This is an example of a broadcaster role BLE device. It advertises as a non-connectable device
and emits the device's current time as a part of the advertising data.
"""
import time
import threading
from blatann import BleDevice
from blatann.gap.advertising import AdvertisingMode, AdvertisingData, AdvertisingFlags
from blatann.examples import example_utils


logger = example_utils.setup_logger(level="DEBUG")


def _get_time_service_data():
    # Get the current time
    t = time.strftime("%H:%M:%S", time.localtime())
    # Service data is 2 bytes UUID + data, use UUID 0x2143
    return "\x43\x21" + t


def wait_for_user_stop(stop_event):
    # Thread that just waits for the user to press enter, then signals the event
    input("Press enter to exit\n")
    stop_event.set()


def main(serial_port):
    stop_event = threading.Event()
    threading.Thread(target=wait_for_user_stop, args=(stop_event, )).start()
    time.sleep(2)

    ble_device = BleDevice(serial_port)
    ble_device.open()

    interval_ms = 100  # Send out an advertising packet every 100ms
    timeout_sec = 0    # Advertise forever
    mode = AdvertisingMode.non_connectable_undirected  # Set mode to not allow connections

    adv_flags = AdvertisingFlags.BR_EDR_NOT_SUPPORTED | AdvertisingFlags.GENERAL_DISCOVERY_MODE
    adv_data = AdvertisingData(flags=adv_flags, local_name="Time", service_data=_get_time_service_data())

    ble_device.advertiser.set_advertise_data(adv_data)
    ble_device.advertiser.start(interval_ms, timeout_sec, auto_restart=True, advertise_mode=mode)

    while True:
        # Update the advertising data every 1 second
        stop_event.wait(1)
        if stop_event.is_set():  # User stopped execution, break out and stop advertising
            break
        # Update the service data and set it in the BLE device
        adv_data.service_data = _get_time_service_data()
        ble_device.advertiser.set_advertise_data(adv_data)

    ble_device.advertiser.stop()
    ble_device.close()


if __name__ == '__main__':
    main("COM8")
