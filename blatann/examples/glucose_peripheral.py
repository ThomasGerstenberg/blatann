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
    if peer:
        logger.info("Connected to peer")
    else:
        logger.warning("Connection timed out")


def on_disconnect(peer, event_args):
    logger.info("Disconnected from peer, reason: {}".format(event_args.reason))


def display_passkey(peer, event_args):
    logger.info("Passkey: {}".format(event_args.passkey))


def add_fake_glucose_readings(glucose_database, num_records=15):
    init_time = datetime.datetime.now()

    for i in range(0, num_records):
        # Increment the reading times by 5 mins
        sample_time = init_time + datetime.timedelta(minutes=i * 5)

        # create a sample reading
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
            m.context = context

        glucose_database.add_record(m)


def main(serial_port):
    ble_device = BleDevice(serial_port)
    ble_device.open()

    # Create a database to store the readings
    glucose_database = glucose.BasicGlucoseDatabase()
    # Add the service to the BLE database, using the glucose database just created, require encryption at the minimum
    service = glucose.add_glucose_service(ble_device.database, glucose_database, glucose.SecurityLevel.JUST_WORKS)

    # Set the Glucose Feature values
    features = glucose.GlucoseFeatures(GlucoseFeatureType.low_battery_detection, GlucoseFeatureType.strip_insertion_error_detection)
    service.set_features(features)

    # Add some measurements to the glucose database
    add_fake_glucose_readings(glucose_database)

    # Register listeners for when the client connects and disconnects
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)

    # Set the connection parameters for the client
    ble_device.client.set_connection_parameters(15, 30, 4000)

    # Set the function to display the passkey
    ble_device.client.security.on_passkey_display_required.register(display_passkey)

    # Set the security parameters for the client
    ble_device.client.security.set_security_params(passcode_pairing=False, bond=False,
                                                   io_capabilities=IoCapabilities.DISPLAY_ONLY, out_of_band=False)

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
    main("COM49")
