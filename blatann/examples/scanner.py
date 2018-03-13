"""
This example simply demonstrates scanning for peripheral devices
"""
from blatann import BleDevice
from blatann.examples import example_utils

logger = example_utils.setup_logger(level="INFO")


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.open()

    logger.info("Scanning...")
    # Set scanning for 4 seconds
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)

    # Start scanning and wait for it to complete
    scan_report = ble_device.scanner.start_scan().wait()
    print("")
    logger.info("Finished scanning. Scan reports:")

    # Iterate through all the peers found and print out the reports
    for report in scan_report.advertising_peers_found:
        logger.info(report)

    # Clean up and close the device
    ble_device.close()


if __name__ == '__main__':
    main("COM4")
