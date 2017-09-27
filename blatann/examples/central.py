import time

from blatann import BleDevice
from blatann.examples import example_utils

logger = example_utils.setup_logger(level="INFO")


def find_target_device(ble_device, name):
    scan_report = ble_device.scanner.start_scan().wait()

    target_address = None
    for peer_address, scan_report in scan_report.scans_by_peer_address.items():
        if scan_report.advertise_data.local_name == name:
            target_address = peer_address
            break
    return target_address


def main(serial_port):

    target_device_name = "Periph Test"

    ble_device = BleDevice(serial_port)

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
        time.sleep(10)
        logger.info("Disconnecting...")
        peer.disconnect().wait()
        logger.info("Disconnected")


if __name__ == '__main__':
    main("COM4")
