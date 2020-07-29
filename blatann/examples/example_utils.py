from blatann.utils import setup_logger


def find_target_device(ble_device, name):
    """
    Starts the scanner and searches the advertising report for the desired name.
    If found, returns the peer's address that can be connected to

    :param ble_device: The ble device to operate on
    :type ble_device: blatann.BleDevice
    :param name: The device's local name that is advertised
    :return: The peer's address if found, or None if not found
    """
    # Start scanning for the peripheral.
    # Using the `scan_reports` iterable on the waitable will return the scan reports as they're
    # discovered in real-time instead of waiting for the full scan to complete
    for report in ble_device.scanner.start_scan().scan_reports:
        if report.advertise_data.local_name == name:
            return report.peer_address
