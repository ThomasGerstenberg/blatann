from __future__ import annotations

from blatann import BleDevice
from blatann.utils import setup_logger


def find_target_device(ble_device: BleDevice, name: str):
    """
    Starts the scanner and searches the advertising report for the desired name.
    If found, returns the peer's address that can be connected to

    :param ble_device: The ble device to operate on
    :param name: The device's local name that is advertised
    :return: The peer's address if found, or None if not found
    """
    # Start scanning for the peripheral.
    # Using the `scan_reports` iterable on the waitable will return the scan reports as they're
    # discovered in real-time instead of waiting for the full scan to complete
    for report in ble_device.scanner.start_scan().scan_reports:
        if report.advertise_data.local_name == name:
            return report.peer_address


async def find_target_device_async(ble_device: BleDevice, name: str):
    async for report in ble_device.scanner.start_scan().scan_reports_async:
        if report.advertise_data.local_name == name:
            return report.peer_address
