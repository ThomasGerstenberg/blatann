from blatann import BleDevice
from blatann.examples import example_utils

logger = example_utils.setup_logger(level="INFO")


def main(serial_port):
    ble_device = BleDevice(serial_port)
    ble_device.open()

    logger.info("Scanning...")
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    scan_report = ble_device.scanner.start_scan().wait()
    print("")
    logger.info("Finished scanning. Scan reports:")

    for report in scan_report.advertising_peers_found:
        logger.info(report)

    ble_device.close()


if __name__ == '__main__':
    main("COM4")
