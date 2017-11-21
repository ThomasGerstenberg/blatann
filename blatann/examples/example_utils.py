from blatann.utils import setup_logger


def find_target_device(ble_device, name):
    scan_report = ble_device.scanner.start_scan().wait()

    for report in scan_report.advertising_peers_found:
        if report.advertise_data.local_name == name:
            return report.peer_address
