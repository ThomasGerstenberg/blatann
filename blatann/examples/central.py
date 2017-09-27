import time

from blatann import BleDevice


def main(serial_port):
    ble_device = BleDevice(serial_port)
    target_device_name = "Periph Test"
    print("Scanning for {}".format(target_device_name))
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    scan_report = ble_device.scanner.start_scan().wait()

    target_address = None
    for peer_address, scan_report in scan_report.scans_by_peer_address.items():
        if scan_report.advertise_data.local_name == target_device_name:
            target_address = peer_address
            break

    if not target_address:
        print("Did not find target peripheral")
        return

    print("Found match: address {}".format(target_address))
    print("Connecting to periph_test...")
    peer = ble_device.connect(target_address).wait()
    if not peer:
        print("Timed out connecting to device")
        return
    print("Connected, conn_handle: {}".format(peer.conn_handle))
    time.sleep(10)
    print("Disconnecting")
    peer.disconnect().wait()
    print("Disconnected")


if __name__ == '__main__':
    main("COM45")