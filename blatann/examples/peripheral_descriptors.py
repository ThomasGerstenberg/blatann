"""
This example shows how to add descriptors to a characteristic in a GATT Database.

This can be used with the central_descriptor example running on a separate nordic device or
can be run with the nRF Connect app
"""
import time

from blatann import BleDevice
from blatann.gatt import gatts, PresentationFormat
from blatann.examples import example_utils, constants
from blatann.gap import smp, advertising
from blatann.bt_sig.assigned_numbers import Format, Units, Namespace, NamespaceDescriptor
from blatann.gatt.gatts_attribute import GattsAttributeProperties
from blatann.services.ble_data_types import Uint32
from blatann.waitables import GenericWaitable
from blatann.bt_sig.uuids import DescriptorUuid

logger = example_utils.setup_logger(level="INFO")


def on_connect(peer, event_args):
    """
    Event callback for when a central device connects to us

    :param peer: The peer that connected to us
    :type peer: blatann.peer.Client
    :param event_args: None
    """
    if peer:
        logger.info("Connected to peer")
    else:
        logger.warning("Connection timed out")


def on_disconnect(peer, event_args):
    """
    Event callback for when the client disconnects from us (or when we disconnect from the client)

    :param peer: The peer that disconnected
    :type peer: blatann.peer.Client
    :param event_args: The event args
    :type event_args: blatann.event_args.DisconnectionEventArgs
    """
    logger.info("Disconnected from peer, reason: {}".format(event_args.reason))


def on_read(characteristic, event_args):
    """
    On read for the Time characteristic. Updates the characteristic with the current
    UTC time as a 32-bit number
    """
    t = int(time.time())
    characteristic.set_value(Uint32.encode(t))


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.configure()
    ble_device.open()

    # Create the service
    service = ble_device.database.add_service(constants.DESC_EXAMPLE_SERVICE_UUID)

    # Create a characteristic and add some descriptors
    # NOTE: Some descriptors MUST be added during creation: SCCD, User Description, and Presentation Format
    #       CCCD is added automatically based on the characteristic's Notify and Indicate properties

    # Define the User Description properties and make it writable
    # The simplest use-case in which the user description is read-only can provide just the first parameter
    user_desc_props = gatts.GattsUserDescriptionProperties("UTC Time", write=True, security_level=smp.SecurityLevel.OPEN,
                                                           max_length=20, variable_length=True)
    # Define the presentation format. Returning the time in seconds so set exponent to 0
    presentation_format = PresentationFormat(fmt=Format.uint32, exponent=0, unit=Units.time_second)
    # Create the characteristic properties, including the SCCD, User Description, and Presentation Format
    char_props = gatts.GattsCharacteristicProperties(read=True, write=False, notify=True, max_length=Uint32.byte_count, variable_length=False,
                                                     sccd=True, user_description=user_desc_props, presentation_format=presentation_format)
    char = service.add_characteristic(constants.DESC_EXAMPLE_CHAR_UUID, char_props, Uint32.encode(0))
    char.on_read.register(on_read)

    # Add another descriptor to the list
    char_range_value = Uint32.encode(5555) + Uint32.encode(2**32-1000)
    desc_props = GattsAttributeProperties(read=True, write=False, variable_length=False, max_length=len(char_range_value))
    char.add_descriptor(DescriptorUuid.valid_range, desc_props, char_range_value)

    # Initialize the advertising and scan response data
    adv_data = advertising.AdvertisingData(local_name=constants.PERIPHERAL_NAME, flags=0x06)
    scan_data = advertising.AdvertisingData(service_uuid128s=constants.DESC_EXAMPLE_SERVICE_UUID, has_more_uuid128_services=False)
    ble_device.advertiser.set_advertise_data(adv_data, scan_data)

    # Start advertising
    logger.info("Advertising")
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that will never fire, and wait for some time
    w = GenericWaitable()
    w.wait(60*30, exception_on_timeout=False)  # Keep device active for 30 mins

    logger.info("Done")
    ble_device.close()


if __name__ == '__main__':
    main("COM13")
