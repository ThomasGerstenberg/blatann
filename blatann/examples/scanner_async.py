"""
This example simply demonstrates scanning for peripheral devices using async methods
"""
from __future__ import annotations

import asyncio

from blatann import BleDevice
from blatann.examples import example_utils

logger = example_utils.setup_logger(level="INFO")


async def _main(ble_device: BleDevice):
    # Open the device
    ble_device.open()

    logger.info("Scanning...")
    # Set scanning for 4 seconds
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)

    # Start scanning and iterate through the reports as they're received, async to not block the main thread
    async for report in ble_device.scanner.start_scan().scan_reports_async:
        if not report.duplicate:
            logger.info(report)

    scan_report = ble_device.scanner.scan_report
    print("\n")
    logger.info("Finished scanning. Scan reports by peer address:")
    # Iterate through all the peers found and print out the reports
    for report in scan_report.advertising_peers_found:
        logger.info(report)

    # Clean up and close the device
    ble_device.close()


def main(serial_port):
    ble_device = BleDevice(serial_port)
    try:
        asyncio.run(_main(ble_device))
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure the ble device is closed on exit
        ble_device.close()


if __name__ == '__main__':
    main("COM4")
