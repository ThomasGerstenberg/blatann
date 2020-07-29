"""
This example demonstrates using Bluetooth SIG's defined Glucose service as a peripheral.
The peripheral creates a range of fake glucose readings that can be queried from the central.

This can be used in conjunction with the nRF Connect apps to explore the peripheral's functionality
"""
import logging
import datetime

from blatann import BleDevice
from blatann.gap import advertising, IoCapabilities
from blatann.utils import setup_logger
from blatann.services import glucose
from blatann.services.glucose import GlucoseFeatureType
from blatann.waitables import GenericWaitable


logger = setup_logger(level="INFO")


def on_connect(peer, event_args):
    """
    Event callback for when a central device connects to us

    :param peer: The peer that connected to us
    :type peer: blatann.peer.Client
    :param event_args: None
    """
    if peer:
        logger.info("Connected to {} peer".format("previously-bonded" if peer.is_previously_bonded else "new"))
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


def on_security_level_changed(peer, event_args):
    """
    Event callback for when the security level changes on a connection with a peer

    :param peer: The peer the security level changed on
    :type peer: blatann.peer.Client
    :param event_args: The event args
    :type event_args: blatann.event_args.SecurityLevelChangedEventArgs
    """
    logger.info("Security level changed to {}".format(event_args.security_level))


def display_passkey(peer, event_args):
    """
    Event callback that is called when a passkey is required to be displayed to a user
    for the pairing process.

    :param peer: The peer the passkey is for
    :type peer: blatann.peer.Client
    :param event_args: The event args
    :type event_args: blatann.event_args.PasskeyDisplayEventArgs
    """
    if not event_args.match_request:
        logger.info("Passkey: {}".format(event_args.passkey))
    else:
        response = input("Passkey: {}, do both devices show same passkey? [y/n]\n".format(event_args.passkey))
        match_confirmed = response.lower().startswith("y")
        event_args.match_confirm(match_confirmed)


def add_fake_glucose_readings(glucose_database, num_records=15):
    """
    Helper method to create some glucose readings and add them to the glucose database

    :param glucose_database: The database to add readings to
    :type glucose_database: glucose.BasicGlucoseDatabase
    :param num_records: The number of records to generate
    """
    init_time = datetime.datetime.now()

    for i in range(0, num_records):
        # Increment the reading times by 5 mins
        sample_time = init_time + datetime.timedelta(minutes=i * 5)

        # create a sample reading with some random data
        sample = glucose.GlucoseSample(glucose.GlucoseType.capillary_plasma, glucose.SampleLocation.finger,
                                       12.345 * i, glucose.GlucoseConcentrationUnits.mol_per_liter)

        # Create the measurement
        m = glucose.GlucoseMeasurement(i, sample_time, sample=sample)

        # Add some records with context
        if i % 4 == 0:
            carbs = glucose.CarbsInfo(carbs_grams=50 * i, carb_type=glucose.CarbohydrateType.lunch)
            medication = glucose.MedicationInfo(glucose.MedicationType.long_acting_insulin, 5.41 * i,
                                                glucose.MedicationUnits.milligrams)
            context = glucose.GlucoseContext(i, carbs=carbs, medication=medication, hba1c_percent=i * 6.05)
            # Add the context to the measurement
            m.context = context

        glucose_database.add_record(m)


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.open()

    # Create a database to store the readings
    glucose_database = glucose.BasicGlucoseDatabase()
    # Add the service to the BLE database, using the glucose database just created, require encryption at the minimum
    service = glucose.add_glucose_service(ble_device.database, glucose_database, glucose.SecurityLevel.MITM)

    # Set the features of this "glucose sensor"
    features = glucose.GlucoseFeatures(GlucoseFeatureType.low_battery_detection, GlucoseFeatureType.strip_insertion_error_detection)
    service.set_features(features)

    # Add some measurements to the glucose database
    add_fake_glucose_readings(glucose_database)

    # Register listeners for when the client connects and disconnects
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)

    # Set the connection parameters for the client
    ble_device.client.set_connection_parameters(15, 100, 4000)

    # Set the function to display the passkey
    ble_device.client.security.on_passkey_display_required.register(display_passkey)

    # Add a callback for when the security level changes
    ble_device.client.security.on_security_level_changed.register(on_security_level_changed)

    # Set the security parameters for the client
    ble_device.client.security.set_security_params(passcode_pairing=False, bond=True, lesc_pairing=True,
                                                   io_capabilities=IoCapabilities.KEYBOARD_DISPLAY, out_of_band=False)

    # Advertise the Glucose service
    adv_data = advertising.AdvertisingData(local_name="Glucose Test", flags=0x06,
                                           service_uuid16s=glucose.GLUCOSE_SERVICE_UUID)
    ble_device.advertiser.set_advertise_data(adv_data)

    logger.info("Advertising")
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that will never fire, and wait for some time
    w = GenericWaitable()
    w.wait(60*30, exception_on_timeout=False)  # Keep device active for 30 mins

    logger.info("Done")
    ble_device.close()


if __name__ == '__main__':
    main("COM13")
