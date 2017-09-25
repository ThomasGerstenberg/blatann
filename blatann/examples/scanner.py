from blatann import BleDevice


def main(serial_port):
    ble_device = BleDevice(serial_port)

    print("Scanning...")
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    scan_report = ble_device.scanner.start_scan().wait()
    print("")
    print("Finished scanning. Scan reports:")
    for peer, report in scan_report.scans_by_peer_address.items():
        print(report)


if __name__ == '__main__':
    main("COM3")
