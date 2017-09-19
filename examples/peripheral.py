from blatann import BleDevice
from blatann.uuid import Uuid128
from blatann.nrf.nrf_types import BLEAdvData
from blatann.nrf.nrf_events import GapEvtDisconnected
from blatann.nrf.nrf_event_sync import EventSync
from blatann import gatt


def main():
    ble_device = BleDevice("COM3")
    service_uuid = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
    service = ble_device.peripheral.database.add_service(service_uuid)
    props = gatt.CharacteristicProperties(read=True, notify=True, max_length=10)
    service.add_characteristic(Uuid128("deadbeaa-0011-2345-6679-ab12ccd4f550"), props)
    ble_device.peripheral.set_advertise_data(BLEAdvData(complete_local_name='Thomas Test'))
    ble_device.peripheral.advertise()
    print("Advertising")
    event = ble_device.wait_for_connection()
    if event:
        print("Connected, event: {}".format(event))
    else:
        print("Connection timeout")
        return
    with EventSync(ble_device.ble_driver, GapEvtDisconnected) as sync:
        event = sync.get(timeout=600)
    
    print("Done")
    


if __name__ == '__main__':
    main()
