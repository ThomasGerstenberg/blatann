"""
This example exhibits some of the functionality of a peripheral BLE device,
such as reading, writing, and notifying characteristics,
utilizing asyncio to handle each characteristic in its own coroutine operating on the main thread.
This async example is functionally equivalent to the other peripheral example,
though some logging callbacks and database discovery on the central is not performed.

This example can be used with one of the central examples running on a separate nordic device,
or can be run with the nRF Connect app to explore the contents of the GATT database.
"""
from __future__ import annotations

import asyncio
import binascii
import struct
import time

from blatann import BleDevice
from blatann.bt_sig.assigned_numbers import Appearance
from blatann.event_args import DisconnectionEventArgs, PasskeyDisplayEventArgs, PasskeyEntryEventArgs
from blatann.examples import constants, example_utils
from blatann.gap import IoCapabilities, advertising
from blatann.gatt.gatts import GattsCharacteristic
from blatann.peer import Client
from blatann.waitables import EventWaitable

logger = example_utils.setup_logger(level="DEBUG")


def on_connect(peer: Client, event_args: None):
    """
    Event callback for when a central device connects to us

    :param peer: The peer that connected to us
    :param event_args: None
    """
    if peer:
        logger.info("Connected to peer")
    else:
        logger.warning("Connection timed out")


def on_disconnect(peer: Client, event_args: DisconnectionEventArgs):
    """
    Event callback for when the client disconnects from us (or when we disconnect from the client)

    :param peer: The peer that disconnected
    :param event_args: The event args
    """
    logger.info("Disconnected from peer, reason: {}".format(event_args.reason))


async def handle_hex_conversion_characteristic(peer: Client, characteristic: GattsCharacteristic):
    """
    Coroutine that handles writes on the hex conversion characteristic.
    This coroutine does not exit until cancelled by the main task.

    :param peer: The client object to wait on connections
    :param characteristic: The hex conversion characteristic
    """
    # Run forever (until killed by main)
    while True:
        # Wait for a connection to be made
        await peer.wait_for_connection_async()
        # This will receive each write event that occurs,
        # asynchronously blocking the coroutine until the next write occurs.
        # The iterator exits when the peer disconnects
        async for _, write_event in characteristic.write_queue_async():
            new_value = binascii.hexlify(write_event.value)
            logger.info(f"Got characteristic write - characteristic: {characteristic.uuid}, data: 0x{new_value}")
            characteristic.set_value(new_value[:characteristic.max_length], notify_client=True)


def on_time_char_read(characteristic: GattsCharacteristic, event_args: None):
    """
    Event callback for when the client reads our time characteristic. Gets the current time and updates the characteristic.
    This demonstrates "lazy evaluation" of characteristics--instead of having to constantly update this characteristic,
    it is only updated when read/observed by an outside actor.

    Note: using an async event queue for reads is less useful because setting the characteristic's new value
    must occur before the event handling is finished and the read response is provided to the peer.
    Since the event queue delegates the event to the main context,
    the read response is sent before the event can be handled.

    :param characteristic: the time characteristic
    :param event_args: None
    """
    t = time.time()
    timestamp = time.strftime("%H:%M:%S", time.localtime(t))
    ms = int((t * 1000) % 1000)
    msg = f"Time: {timestamp}.{ms:03}"
    characteristic.set_value(msg)


async def handle_counting_characteristic(peer: Client, characteristic: GattsCharacteristic):
    """
    Coroutine that dispatches notifications on the counting characteristic.
    This coroutine does not exit until cancelled by the main task.

    :param peer: The client object to wait on connections
    :param characteristic: The hex conversion characteristic
    """
    current_value = 0

    # Run forever (until killed by main)
    while True:
        await peer.wait_for_connection_async()
        while peer.connected:

            # Wait for the client to subscribe to the characteristic
            if not characteristic.client_subscribed:
                waitable = EventWaitable(characteristic.on_subscription_change)
                _, event_args = await waitable.as_async()
                if not event_args.subscription_state:
                    continue

            try:
                # Increment the value and pack it
                current_value += 1
                value = struct.pack("<I", current_value)

                # Send out a notification of this new value
                waitable = characteristic.notify(value)
                # Send a burst of 16, then wait for them all to send before trying to send more
                if current_value % 16 == 0:
                    await waitable.as_async()
                    await asyncio.sleep(1)  # Wait a second before sending out the next burst
            except Exception as e:
                logger.exception(e)


def on_passkey_display(peer: Client, event_args: PasskeyDisplayEventArgs):
    """
    Event callback that is called when a passkey is required to be displayed to a user
    for the pairing process.

    :param peer: The peer the passkey is for
    :param event_args: The event args
    """
    logger.info("Passkey display: {}, match: {}".format(event_args.passkey, event_args.match_request))
    if event_args.match_request:
        response = input("Passkey: {}, do both devices show same passkey? [y/n]\n".format(event_args.passkey))
        match = response.lower().startswith("y")
        event_args.match_confirm(match)


def on_passkey_entry(peer: Client, passkey_event_args: PasskeyEntryEventArgs):
    """
    Callback for when the user is requested to enter a passkey to resume the pairing process.
    Requests the user to enter the passkey and resolves the event with the passkey entered

    :param peer: the peer the passkey is for
    :param passkey_event_args:
    """
    passkey = input("Enter passkey: ")
    passkey_event_args.resolve(passkey)


async def _main(ble_device: BleDevice):
    # Open the device
    ble_device.configure()
    ble_device.open()

    # Demo of setting parameters in the Generic Access service, not required tp set any parameters here
    ble_device.generic_access_service.device_name = "Peripheral Example"
    ble_device.generic_access_service.appearance = Appearance.computer

    # Set up desired security parameters
    ble_device.client.security.set_security_params(passcode_pairing=False, bond=False, lesc_pairing=False,
                                                   io_capabilities=IoCapabilities.DISPLAY_ONLY, out_of_band=False)
    ble_device.client.security.on_passkey_display_required.register(on_passkey_display)
    ble_device.client.security.on_passkey_required.register(on_passkey_entry)

    # Create and add the math service
    service = ble_device.database.add_service(constants.MATH_SERVICE_UUID)

    # Create and add the hex conversion characteristic to the service
    hex_conv_char = service.add_characteristic(constants.HEX_CONVERT_CHAR_UUID,
                                               constants.HEX_CONVERT_CHAR_PROPERTIES, "Test Data")

    # Create and add the counting characteristic, initializing the data to [0, 0, 0, 0]
    counting_char = service.add_characteristic(constants.COUNTING_CHAR_UUID, constants.COUNTING_CHAR_PROPERTIES,
                                               [0] * 4)

    # Create and add the time service
    time_service = ble_device.database.add_service(constants.TIME_SERVICE_UUID)

    # Add the time characteristic and register the callback for when its read
    time_char = time_service.add_characteristic(constants.TIME_CHAR_UUID, constants.TIME_CHAR_PROPERTIES, "Time")

    # Initialize the advertising and scan response data
    adv_data = advertising.AdvertisingData(local_name=constants.PERIPHERAL_NAME, flags=0x06)
    scan_data = advertising.AdvertisingData(service_uuid128s=constants.TIME_SERVICE_UUID,
                                            has_more_uuid128_services=True,
                                            appearance=ble_device.generic_access_service.appearance)
    ble_device.advertiser.set_advertise_data(adv_data, scan_data)

    # Start up the coroutine tasks to handle the different characteristics
    tasks = [
        asyncio.create_task(handle_counting_characteristic(ble_device.client, counting_char), name="Counting Task"),
        asyncio.create_task(handle_hex_conversion_characteristic(ble_device.client, hex_conv_char), name="Hex Task")
    ]
    # Add the time read handler. See the on_time_char_read() docs for why this isn't a coroutine
    time_char.on_read.register(on_time_char_read)

    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)

    # Start advertising
    logger.info("Advertising")
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Sleep the main task, keeping the device alive for 30mins.
    await asyncio.sleep(30 * 60)

    # Cleanup, kill the tasks
    for task in tasks:
        task.cancel()

    logger.info("Done")
    ble_device.close()


def main(serial_port):
    ble_device = BleDevice(serial_port)
    try:
        asyncio.run(_main(ble_device), debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure the device is closed
        ble_device.close()


if __name__ == '__main__':
    main("COM6")
