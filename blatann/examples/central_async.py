"""
This example demonstrates implementing a central BLE connection using async/asyncio event loop. Each bluetooth operation
performed is done sequentially in a linear fashion, but the event loop is unblocked during the bluetooth operations
(such as connecting, reading characteristics, etc.).

This is designed to run alongside the peripheral example running on a separate Nordic nRF52 device
"""
from __future__ import annotations

import asyncio
import struct

from blatann import BleDevice
from blatann.examples import constants, example_utils
from blatann.gap import PairingPolicy, smp
from blatann.gatt.gattc import GattcCharacteristic
from blatann.nrf import nrf_events

logger = example_utils.setup_logger(level="DEBUG")


async def handle_counting_char(characteristic: GattcCharacteristic):
    """
    Example of a coroutine that subscribes to characteristic notifications
    and uses the AsyncEventQueue to create an iterable that returns each notification
    received by the server

    :param characteristic:
    """
    logger.info("Subscribing to the counting characteristic")
    await characteristic.subscribe().as_async()

    # iterator does not exit until peer disconnects
    async for _, event_args in characteristic.notification_queue_async():
        current_count = struct.unpack("<I", event_args.value)[0]
        logger.info("Counting char notification. Current count: {}".format(current_count))
    logger.info("Peer disconnected, coroutine is exiting")


def on_passkey_entry(peer, passkey_event_args):
    """
    Callback for when the user is requested to enter a passkey to resume the pairing process.
    Requests the user to enter the passkey and resolves the event with the passkey entered

    :param peer: the peer the passkey is for
    :param passkey_event_args:
    :type passkey_event_args: blatann.event_args.PasskeyEntryEventArgs
    """
    passkey = input("Enter peripheral passkey: ")
    passkey_event_args.resolve(passkey)


async def _main(ble_device: BleDevice):
    # Set the target to the peripheral's advertised name
    target_device_name = constants.PERIPHERAL_NAME

    # Open the BLE device (and suppress spammy logs)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    ble_device.open()

    # Set the scanner to scan for 4 seconds
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)

    logger.info("Scanning for '{}'".format(target_device_name))
    target_address = await example_utils.find_target_device_async(ble_device, target_device_name)

    if not target_address:
        logger.info("Did not find target peripheral")
        return

    # Initiate the connection and wait for it to finish
    logger.info("Found match: connecting to address {}".format(target_address))
    peer = await ble_device.connect(target_address).as_async()
    if not peer:
        logger.warning("Timed out connecting to device")
        return
    logger.info("Connected, conn_handle: {}".format(peer.conn_handle))

    # Setup the security parameters and register a handler for when passkey entry is needed.
    # Should be done right after connection in case the peripheral initiates a security request
    peer.security.set_security_params(passcode_pairing=True, io_capabilities=smp.IoCapabilities.KEYBOARD_DISPLAY,
                                      bond=False, out_of_band=False, reject_pairing_requests=PairingPolicy.allow_all)
    # Register the callback for when a passkey needs to be entered by the user
    peer.security.on_passkey_required.register(on_passkey_entry)

    # Wait up to 10 seconds for service discovery to complete
    _, event_args = await peer.discover_services().as_async(timeout=10, exception_on_timeout=False)
    logger.info("Service discovery complete! status: {}".format(event_args.status))

    # Log each service found
    for service in peer.database.services:
        logger.info(service)

    peer.set_connection_parameters(100, 120, 6000)  # Discovery complete, go to a longer connection interval

    # Wait up to 60 seconds for the pairing process, if the link is not secured yet
    if peer.security.security_level == smp.SecurityLevel.OPEN:
        await peer.security.pair().as_async(timeout=60)

    # Find the counting characteristic
    counting_char = peer.database.find_characteristic(constants.COUNTING_CHAR_UUID)

    if counting_char:
        # Create the task that will handle all notifications from this characteristic
        counting_task = asyncio.create_task(
            handle_counting_char(counting_char)
        )
    else:
        counting_task = None
        logger.warning("Failed to find counting characteristic")

    # Find the hex conversion characteristic. This characteristic takes in a bytestream and converts it to its
    # hex representation. e.g. '0123' -> '30313233'
    hex_convert_char = peer.database.find_characteristic(constants.HEX_CONVERT_CHAR_UUID)
    if hex_convert_char:
        # Generate some data ABCDEFG... Then, incrementally send increasing lengths of strings.
        # i.e. first send 'A', then 'AB', then 'ABC'...
        data_to_convert = bytes(ord('A') + i for i in range(12))
        for i in range(len(data_to_convert)):
            data_to_send = data_to_convert[:i+1]
            logger.info("Converting to hex data: '{}'".format(data_to_send))

            # Write the data, waiting up to 5 seconds for then write to complete
            if not await hex_convert_char.write(data_to_send).as_async(timeout=5, exception_on_timeout=False):
                logger.error("Failed to write data, i={}".format(i))
                break

            # Write was successful, when we read the characteristic the peripheral should have converted the string
            # Once again, initiate a read and wait up to 5 seconds for the read to complete
            char, event_args = await hex_convert_char.read().as_async(5, False)
            logger.info("Hex: '{}'".format(event_args.value.decode("ascii")))
    else:
        logger.warning("Failed to find hex convert char")

    # Clean up
    logger.info("Disconnecting from peripheral")
    await peer.disconnect().as_async()
    ble_device.close()

    # Wait for the counting task to exit
    if counting_task:
        await counting_task


def main(serial_port):
    ble_device = BleDevice(serial_port)
    asyncio.run(_main(ble_device), debug=True)


if __name__ == '__main__':
    main("COM4")
