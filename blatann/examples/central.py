import time
import struct
from blatann import BleDevice, uuid
from blatann.examples import example_utils, constants
from blatann.nrf import nrf_events

logger = example_utils.setup_logger(level="DEBUG")


def find_target_device(ble_device, name):
    scan_report = ble_device.scanner.start_scan().wait()

    for scan_report in scan_report.advertising_peers_found:
        if scan_report.advertise_data.local_name == name:
            return scan_report.peer_address


def on_counting_char_notification(characteristic, value):
    current_count = struct.unpack("<I", value)[0]
    logger.info("Counting char notification. Curent count: {}".format(current_count))


def main(serial_port):
    target_device_name = "Periph Test"

    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)

    ble_device.scanner.set_default_scan_params(timeout_seconds=4)

    logger.info("Scanning for '{}'".format(target_device_name))
    while True:
        logger.info("Scanning...")
        target_address = find_target_device(ble_device, target_device_name)

        if not target_address:
            logger.info("Did not find target peripheral")
            continue

        logger.info("Found match: connecting to address {}".format(target_address))
        peer = ble_device.connect(target_address).wait()
        if not peer:
            logger.warning("Timed out connecting to device")
            continue
        logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
        services, status = peer.discover_services().wait(1000, exception_on_timeout=False)
        logger.info("Service discovery complete! status: {}".format(status))
        for service in peer.database.services:
            logger.info(service)

        # Find the counting characteristic
        counting_char = peer.database.find_characteristic(constants.COUNTING_CHAR_UUID)

        if counting_char:
            logger.info("Subscribing to the counting characteristic..")
            # counting_char.subscribe(on_counting_char_notification).wait(5, False)
            logger.info("Subscribed")
        else:
            logger.warning("Failed to find counting characteristic")

        char1 = peer.database.find_characteristic(constants.CHAR1_UUID)
        if char1:
            logger.info("Testing writes")
            data = bytearray(ord('A') + i for i in range(48))
            for i in range(48):
                data_to_send = data[:i+1]
                if not char1.write(data_to_send).wait(10, False):
                    logger.error("Failed to write data, i={}".format(i))
                    break

                char, status, data_read = char1.read().wait(10, False)
                logger.info("Read data: '{}'".format(data_read))
        else:
            logger.warning("Failed to find char1")

        time.sleep(10)
        logger.info("Disconnecting...")
        peer.disconnect().wait()
        logger.info("Disconnected")


if __name__ == '__main__':
    main("COM4")
