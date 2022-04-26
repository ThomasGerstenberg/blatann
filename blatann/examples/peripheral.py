"""
This example exhibits some of the functionality of a peripheral BLE device,
such as reading, writing and notifying characteristics.

This peripheral can be used with one of the central examples running on a separate nordic device,
or can be run with the nRF Connect app to explore the contents of the service
"""
import atexit
import binascii
import struct
import threading
import time

from blatann.peer import ConnectionParameters

from blatann import BleDevice
from blatann.bt_sig.assigned_numbers import Appearance
from blatann.uuid import Uuid16
from blatann.examples import example_utils, constants
from blatann.gap import advertising, smp, IoCapabilities
from blatann.waitables import GenericWaitable


logger = example_utils.setup_logger(level="DEBUG")


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


def on_hex_conversion_characteristic_write(characteristic, event_args):
    """
    Event callback for when the client writes to the hex conversion characteristic.
    This takes the data written, converts it to the hex representation, and updates the characteristic
    with this new value. If the client is subscribed to the characteristic, the client will be notified.

    :param characteristic: The hex conversion characteristic
    :type characteristic: blatann.gatt.gatts.GattsCharacteristic
    :param event_args: the event arguments
    :type event_args: blatann.event_args.WriteEventArgs
    """
    new_value = binascii.hexlify(event_args.value)
    logger.info("Got characteristic write - characteristic: {}, data: 0x{}".format(characteristic.uuid, new_value))
    characteristic.set_value(new_value[:characteristic.max_length], notify_client=True)


def on_gatts_subscription_state_changed(characteristic, event_args):
    """
    Event callback for when a client subscribes or unsubscribes from a characteristic. This
    is the equivalent to when a client writes to a CCCD descriptor on a characteristic.

    :type characteristic: blatann.gatt.gatts.GattsCharacteristic
    :type event_args: blatann.event_args.SubscriptionStateChangeEventArgs
    """
    logger.info("Subscription state changed - characteristic: {}, state: {}".format(
        characteristic.uuid, event_args.subscription_state))


def on_time_char_read(characteristic, event_args):
    """
    Event callback for when the client reads our time characteristic. Gets the current time and updates the characteristic.
    This demonstrates "lazy evaluation" of characteristics--instead of having to constantly update this characteristic,
    it is only updated when read/observed by an outside actor.

    :param characteristic: the time characteristic
    :type characteristic: blatann.gatt.gatts.GattsCharacteristic
    :param event_args: None
    """
    t = time.time()
    ms = int((t * 1000) % 1000)
    msg = "Time: {}.{:03}".format(time.strftime("%H:%M:%S", time.localtime(t)), ms)
    characteristic.set_value(msg)


def on_discovery_complete(peer, event_args):
    """
    Callback for when the service discovery completes on the client. This will look for the client's Device name
    characteristic (part of the Generic Access Service) and read the value

    :param peer: The peer the discovery completed on
    :type peer: blatann.peer.Client
    :param event_args: The event arguments (unused)
    :type event_args: blatann.event_args.DatabaseDiscoveryCompleteEventArgs
    """
    device_name_char = peer.database.find_characteristic(Uuid16(0x2A00))
    if device_name_char:
        device_name_char.read().then(lambda c, e: logger.info("Client's device name: {}".format(e.value.decode("utf-8"))))
    else:
        logger.info("Peer does not have a device name characteristic")


def on_security_level_changed(peer, event_args):
    """
    Called when the security level changes, i.e. a bonded device connects and enables encryption or pairing has finished.
    If security has been enabled (i.e. bonded) and the peer's services have yet to be discovered, discover now.

    This code demonstrates that even in a peripheral connection role, the peripheral can still discover the database
    on the client, if the client has a database.

    :param peer: The peer that security was changed to
    :type peer: blatann.peer.Client
    :param event_args: the event arguments
    :type event_args: blatann.event_args.SecurityLevelChangedEventArgs
    """
    if event_args.security_level in [smp.SecurityLevel.MITM, smp.SecurityLevel.LESC_MITM, smp.SecurityLevel.JUST_WORKS]:
        logger.info("Secure connections established, discovering database on the client")
        if not peer.database.services:
            peer.discover_services().then(on_discovery_complete)
        else:
            on_discovery_complete(peer, None)


def on_client_pairing_complete(peer, event_args):
    """
    Event callback for when the pairing process completes with the client

    :param peer: the peer that completed pairing
    :type peer: blatann.peer.Client
    :param event_args: the event arguments
    :type event_args: blatann.event_args.PairingCompleteEventArgs
    """
    logger.info("Client Pairing complete, status: {}".format(event_args.status))


def on_passkey_display(peer, event_args):
    """
    Event callback that is called when a passkey is required to be displayed to a user
    for the pairing process.

    :param peer: The peer the passkey is for
    :type peer: blatann.peer.Client
    :param event_args: The event args
    :type event_args: blatann.event_args.PasskeyDisplayEventArgs
    """
    logger.info("Passkey display: {}, match: {}".format(event_args.passkey, event_args.match_request))
    if event_args.match_request:
        response = input("Passkey: {}, do both devices show same passkey? [y/n]\n".format(event_args.passkey))
        match = response.lower().startswith("y")
        event_args.match_confirm(match)


def on_passkey_entry(peer, passkey_event_args):
    """
    Callback for when the user is requested to enter a passkey to resume the pairing process.
    Requests the user to enter the passkey and resolves the event with the passkey entered

    :param peer: the peer the passkey is for
    :param passkey_event_args:
    :type passkey_event_args: blatann.event_args.PasskeyEntryEventArgs
    """
    passkey = input("Enter passkey: ")
    passkey_event_args.resolve(passkey)


class CountingCharacteristicThread(object):
    """
    Thread which updates the counting characteristic and notifies
    the client each time its updated.
    This also demonstrates the notification queuing functionality--if a notification/indication
    is already in progress, future notifications will be queued and sent out when the previous ones complete.
    """
    def __init__(self, characteristic):
        """
        :param characteristic: the counting characteristic
        :type characteristic: blatann.gatt.gatts.GattsCharacteristic
        """
        self.current_value = 0
        self._stop_event = threading.Event()
        self._stopped = threading.Event()
        self.characteristic = characteristic
        self.characteristic.on_notify_complete.register(self._on_notify_complete)
        self.thread = threading.Thread(target=self.run)
        atexit.register(self.join)
        self.thread.daemon = True
        self.thread.start()

    def join(self):
        """
        Used to stop and join the thread
        """
        self._stop_event.set()
        self._stopped.wait(3)

    def _on_notify_complete(self, characteristic, event_args):
        """
        Event callback that is triggered when the notification finishes sending

        :param characteristic: The characteristic the notification was on
        :type characteristic: blatann.gatt.gatts.GattsCharacteristic
        :param event_args: The event arguments
        :type event_args: blatann.event_args.NotificationCompleteEventArgs
        """
        logger.info("Notification Complete, id: {}, reason: {}".format(event_args.id, event_args.reason))

    def run(self):
        while not self._stop_event.is_set():
            try:
                if not self.characteristic.client_subscribed:  # Do nothing until a client is subscribed
                    time.sleep(1)
                    continue
                # Increment the value and pack it
                self.current_value += 1
                value = struct.pack("<I", self.current_value)

                # Send out a notification of this new value
                waitable = self.characteristic.notify(value)
                # Send a burst of 16, then wait for them all to send before trying to send more
                if self.current_value % 16 == 0:
                    waitable.wait()
                    time.sleep(1)  # Wait a second before sending out the next burst
            except Exception as e:
                logger.exception(e)

        self._stopped.set()


def on_conn_params_updated(peer, event_args):
    print(f"Conn params updated to {event_args.active_connection_params}")


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.configure()
    ble_device.open()

    # Demo of setting parameters in the Generic Access service, not required tp set any parameters here
    ble_device.generic_access_service.device_name = "Peripheral Example"
    ble_device.generic_access_service.appearance = Appearance.computer

    # Set up desired security parameters
    ble_device.client.security.set_security_params(passcode_pairing=False, bond=False, lesc_pairing=False,
                                                   io_capabilities=IoCapabilities.DISPLAY_ONLY, out_of_band=False)
    ble_device.client.security.on_pairing_complete.register(on_client_pairing_complete)
    ble_device.client.security.on_passkey_display_required.register(on_passkey_display)
    ble_device.client.security.on_passkey_required.register(on_passkey_entry)
    ble_device.client.security.on_security_level_changed.register(on_security_level_changed)
    ble_device.client.on_connection_parameters_updated.register(on_conn_params_updated)

    # Create and add the math service
    service = ble_device.database.add_service(constants.MATH_SERVICE_UUID)

    # Create and add the hex conversion characteristic to the service
    hex_conv_char = service.add_characteristic(constants.HEX_CONVERT_CHAR_UUID,
                                               constants.HEX_CONVERT_CHAR_PROPERTIES, "Test Data")
    # Register the callback for when a write occurs and subscription state changes
    hex_conv_char.on_write.register(on_hex_conversion_characteristic_write)
    hex_conv_char.on_subscription_change.register(on_gatts_subscription_state_changed)

    # Create and add the counting characteristic, initializing the data to [0, 0, 0, 0]
    counting_char = service.add_characteristic(constants.COUNTING_CHAR_UUID, constants.COUNTING_CHAR_PROPERTIES, [0]*4)
    counting_char.on_subscription_change.register(on_gatts_subscription_state_changed)

    # Create the thread for the counting characteristic
    counting_char_thread = CountingCharacteristicThread(counting_char)

    # Create and add the time service
    time_service = ble_device.database.add_service(constants.TIME_SERVICE_UUID)

    # Add the time characteristic and register the callback for when its read
    time_char = time_service.add_characteristic(constants.TIME_CHAR_UUID, constants.TIME_CHAR_PROPERTIES, "Time")
    time_char.on_read.register(on_time_char_read)

    # Initialize the advertising and scan response data
    adv_data = advertising.AdvertisingData(local_name=constants.PERIPHERAL_NAME, flags=0x06)
    scan_data = advertising.AdvertisingData(service_uuid128s=constants.TIME_SERVICE_UUID, has_more_uuid128_services=True,
                                            appearance=ble_device.generic_access_service.appearance)
    ble_device.advertiser.set_advertise_data(adv_data, scan_data)

    # Start advertising
    logger.info("Advertising")
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that will never fire, and wait for some time
    w = GenericWaitable()
    w.wait(60*30, exception_on_timeout=False)  # Keep device active for 30 mins

    # Cleanup
    counting_char_thread.join()
    logger.info("Done")
    ble_device.close()
    

if __name__ == '__main__':
    main("COM4")
