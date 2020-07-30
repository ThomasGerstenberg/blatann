import struct
from blatann.utils import IntEnumWithDescription


class Format(IntEnumWithDescription):
    """
    Format enumeration for use with the :class:`blatann.gatt.PresentationFormat` class
    """
    # Source: https://www.bluetooth.com/specifications/assigned-numbers/format-types/
    # Date: 2020/07/22
    rfu = 0x00, "Reserved for future use"
    boolean = 0x01, "unsigned 1-bit; 0=false, 1=true"
    twobit = 0x02, "unsigned 2-bit integer"
    nibble = 0x03, "unsigned 4-bit integer"
    uint8 = 0x04, "unsigned 8-bit integer"
    uint12 = 0x05, "unsigned 12-bit integer"
    uint16 = 0x06, "unsigned 16-bit integer"
    uint24 = 0x07, "unsigned 24-bit integer"
    uint32 = 0x08, "unsigned 32-bit integer"
    uint48 = 0x09, "unsigned 48-bit integer"
    uint64 = 0x0A, "unsigned 64-bit integer"
    uint128 = 0x0B, "unsigned 128-bit integer"
    sint8 = 0x0C, "signed 8-bit integer"
    sint12 = 0x0D, "signed 12-bit integer"
    sint16 = 0x0E, "signed 16-bit integer"
    sint24 = 0x0F, "signed 24-bit integer"
    sint32 = 0x10, "signed 32-bit integer"
    sint48 = 0x11, "signed 48-bit integer"
    sint64 = 0x12, "signed 64-bit integer"
    sint128 = 0x13, "signed 128-bit integer"
    float32 = 0x14, "IEEE-754 32-bit floating point"
    float64 = 0x15, "IEEE-754 64-bit floating point"
    sfloat = 0x16, "IEEE-11073 16-bit SFLOAT"
    float = 0x17, "IEEE-11073 32-bit FLOAT"
    duint16 = 0x18, "IEEE-20601 format"
    utf8s = 0x19, "UTF-8 string"
    utf16s = 0x1A, "UTF-16 string"
    struct = 0x1B, "Opaque structure"


class Namespace(IntEnumWithDescription):
    """
    Namespace enumeration for use with the :class:`blatann.gatt.PresentationFormat` class
    """
    unknown = 0x0000
    bt_sig = 0x0001, "Bluetooth SIG"


class NamespaceDescriptor(IntEnumWithDescription):
    """
    Namespace descriptor enumeration for use with the :class:`blatann.gatt.PresentationFormat` class
    """
    # Source: https://www.bluetooth.com/specifications/assigned-numbers/gatt-namespace-descriptors/
    # Date: 2020/07/22
    # Trimmed down to the named values (e.g. items like 'twentieth = 20' were stripped)
    auxiliary = 0x0108
    back = 0x0101
    backup = 0x0107
    bottom = 0x0103
    external = 0x0110
    flash = 0x010A
    front = 0x0100
    inside = 0x010B
    internal = 0x010F
    left = 0x010D
    lower = 0x0105
    main = 0x0106
    outside = 0x010C
    right = 0x010E
    supplementary = 0x0109
    top = 0x0102
    unknown = 0x0000
    upper = 0x0104


class Units(IntEnumWithDescription):
    """
    Units enumeration for use with the :class:`blatann.gatt.PresentationFormat` class
    """
    # Source: https://www.bluetooth.com/specifications/assigned-numbers/units/
    # Date: 2020/07/22

    unitless = 0x2700, "unitless"
    absorbed_dose_gray = 0x2733, "absorbed dose (gray)"
    absorbed_dose_rate_gray_per_second = 0x2754, "absorbed dose rate (gray per second)"
    acceleration_metres_per_second_squared = 0x2713, "acceleration (metres per second squared)"
    activity_referred_to_a_radionuclide_becquerel = 0x2732, "activity referred to a radionuclide (becquerel)"
    amount_concentration_mole_per_cubic_metre = 0x271a, "amount concentration (mole per cubic metre)"
    amount_of_substance_mole = 0x2706, "amount of substance (mole)"
    angular_acceleration_radian_per_second_squared = 0x2744, "angular acceleration (radian per second squared)"
    angular_velocity_radian_per_second = 0x2743, "angular velocity (radian per second)"
    angular_velocity_revolution_per_minute = 0x27a8, "angular velocity (revolution per minute)"
    area_barn = 0x2784, "area (barn)"
    area_hectare = 0x2766, "area (hectare)"
    area_square_metres = 0x2710, "area (square metres)"
    capacitance_farad = 0x2729, "capacitance (farad)"
    catalytic_activity_concentration_katal_per_cubic_metre = 0x2757, "catalytic activity concentration (katal per cubic metre)"
    catalytic_activity_katal = 0x2735, "catalytic activity (katal)"
    concentration_count_per_cubic_metre = 0x27b5, "concentration (count per cubic metre)"
    concentration_parts_per_billion = 0x27c5, "concentration (parts per billion)"
    concentration_parts_per_million = 0x27c4, "concentration (parts per million)"
    current_density_ampere_per_square_metre = 0x2718, "current density (ampere per square metre)"
    density_kilogram_per_cubic_metre = 0x2715, "density (kilogram per cubic metre)"
    dose_equivalent_sievert = 0x2734, "dose equivalent (sievert)"
    dynamic_viscosity_pascal_second = 0x2740, "dynamic viscosity (pascal second)"
    electric_charge_ampere_hours = 0x27b0, "electric charge (ampere hours)"
    electric_charge_coulomb = 0x2727, "electric charge (coulomb)"
    electric_charge_density_coulomb_per_cubic_metre = 0x274c, "electric charge density (coulomb per cubic metre)"
    electric_conductance_siemens = 0x272b, "electric conductance (siemens)"
    electric_current_ampere = 0x2704, "electric current (ampere)"
    electric_field_strength_volt_per_metre = 0x274b, "electric field strength (volt per metre)"
    electric_flux_density_coulomb_per_square_metre = 0x274e, "electric flux density (coulomb per square metre)"
    electric_potential_difference_volt = 0x2728, "electric potential difference (volt)"
    electric_resistance_ohm = 0x272a, "electric resistance (ohm)"
    energy_density_joule_per_cubic_metre = 0x274a, "energy density (joule per cubic metre)"
    energy_gram_calorie = 0x27a9, "energy (gram calorie)"
    energy_joule = 0x2725, "energy (joule)"
    energy_kilogram_calorie = 0x27aa, "energy (kilogram calorie)"
    energy_kilowatt_hour = 0x27ab, "energy (kilowatt hour)"
    exposure_coulomb_per_kilogram = 0x2753, "exposure (coulomb per kilogram)"
    force_newton = 0x2723, "force (newton)"
    frequency_hertz = 0x2722, "frequency (hertz)"
    heat_capacity_joule_per_kelvin = 0x2746, "heat capacity (joule per kelvin)"
    heat_flux_density_watt_per_square_metre = 0x2745, "heat flux density (watt per square metre)"
    illuminance_lux = 0x2731, "illuminance (lux)"
    inductance_henry = 0x272e, "inductance (henry)"
    irradiance_watt_per_square_metre = 0x27b6, "irradiance (watt per square metre)"
    length_foot = 0x27a3, "length (foot)"
    length_inch = 0x27a2, "length (inch)"
    length_metre = 0x2701, "length (metre)"
    length_mile = 0x27a4, "length (mile)"
    length_nautical_mile = 0x2783, "length (nautical mile)"
    length_parsec = 0x27a1, "length (parsec)"
    length_yard = 0x27a0, "length (yard)"
    length_angstrom = 0x2782, "length (ångström)"
    logarithmic_radio_quantity_bel = 0x2787, "logarithmic radio quantity (bel)"
    logarithmic_radio_quantity_neper = 0x2786, "logarithmic radio quantity (neper)"
    luminance_candela_per_square_metre = 0x271c, "luminance (candela per square metre)"
    luminous_efficacy_lumen_per_watt = 0x27be, "luminous efficacy (lumen per watt)"
    luminous_energy_lumen_hour = 0x27bf, "luminous energy (lumen hour)"
    luminous_exposure_lux_hour = 0x27c0, "luminous exposure (lux hour)"
    luminous_flux_lumen = 0x2730, "luminous flux (lumen)"
    luminous_intensity_candela = 0x2707, "luminous intensity (candela)"
    magnetic_field_strength_ampere_per_metre = 0x2719, "magnetic field strength (ampere per metre)"
    magnetic_flux_density_tesla = 0x272d, "magnetic flux density (tesla)"
    magnetic_flux_weber = 0x272c, "magnetic flux (weber)"
    mass_concentration_kilogram_per_cubic_metre = 0x271b, "mass concentration (kilogram per cubic metre)"
    mass_density_milligram_per_decilitre = 0x27b1, "mass density (milligram per decilitre)"
    mass_density_millimole_per_litre = 0x27b2, "mass density (millimole per litre)"
    mass_flow_gram_per_second = 0x27c1, "mass flow (gram per second)"
    mass_kilogram = 0x2702, "mass (kilogram)"
    mass_pound = 0x27b8, "mass (pound)"
    mass_tonne = 0x2768, "mass (tonne)"
    metabolic_equivalent = 0x27b9, "metabolic equivalent"
    molar_energy_joule_per_mole = 0x2751, "molar energy (joule per mole)"
    molar_entropy_joule_per_mole_kelvin = 0x2752, "molar entropy (joule per mole kelvin)"
    moment_of_force_newton_metre = 0x2741, "moment of force (newton metre)"
    per_mille = 0x27ae, "per mille"
    percentage = 0x27ad, "percentage"
    period_beats_per_minute = 0x27af, "period (beats per minute)"
    permeability_henry_per_metre = 0x2750, "permeability (henry per metre)"
    permittivity_farad_per_metre = 0x274f, "permittivity (farad per metre)"
    plane_angle_degree = 0x2763, "plane angle (degree)"
    plane_angle_minute = 0x2764, "plane angle (minute)"
    plane_angle_radian = 0x2720, "plane angle (radian)"
    plane_angle_second = 0x2765, "plane angle (second)"
    power_watt = 0x2726, "power (watt)"
    pressure_bar = 0x2780, "pressure (bar)"
    pressure_millimetre_of_mercury = 0x2781, "pressure (millimetre of mercury)"
    pressure_pascal = 0x2724, "pressure (pascal)"
    pressure_pound_force_per_square_inch = 0x27a5, "pressure (pound-force per square inch)"
    radiance_watt_per_square_metre_steradian = 0x2756, "radiance (watt per square metre steradian)"
    radiant_intensity_watt_per_steradian = 0x2755, "radiant intensity (watt per steradian)"
    refractive_index = 0x271d, "refractive index"
    relative_permeability = 0x271e, "relative permeability"
    solid_angle_steradian = 0x2721, "solid angle (steradian)"
    sound_pressure_decibel_spl = 0x27c3, "sound pressure (decibel)"
    specific_energy_joule_per_kilogram = 0x2748, "specific energy (joule per kilogram)"
    specific_heat_capacity_joule_per_kilogram_kelvin = 0x2747, "specific heat capacity (joule per kilogram kelvin)"
    specific_volume_cubic_metre_per_kilogram = 0x2717, "specific volume (cubic metre per kilogram)"
    step_per_minute = 0x27ba, "step (per minute)"
    stroke_per_minute = 0x27bc, "stroke (per minute)"
    surface_charge_density_coulomb_per_square_metre = 0x274d, "surface charge density (coulomb per square metre)"
    surface_density_kilogram_per_square_metre = 0x2716, "surface density (kilogram per square metre)"
    surface_tension_newton_per_metre = 0x2742, "surface tension (newton per metre)"
    thermal_conductivity_watt_per_metre_kelvin = 0x2749, "thermal conductivity (watt per metre kelvin)"
    thermodynamic_temperature_degree_celsius = 0x272f, "Celsius temperature (degree Celsius)"
    thermodynamic_temperature_degree_fahrenheit = 0x27ac, "thermodynamic temperature (degree Fahrenheit)"
    thermodynamic_temperature_kelvin = 0x2705, "thermodynamic temperature (kelvin)"
    time_day = 0x2762, "time (day)"
    time_hour = 0x2761, "time (hour)"
    time_minute = 0x2760, "time (minute)"
    time_month = 0x27b4, "time (month)"
    time_second = 0x2703, "time (second)"
    time_year = 0x27b3, "time (year)"
    transfer_rate_milliliter_per_kilogram_per_minute = 0x27b7, "milliliter (per kilogram per minute)"
    velocity_kilometer_per_minute = 0x27bd, "pace (kilometre per minute)"
    velocity_kilometre_per_hour = 0x27a6, "velocity (kilometre per hour)"
    velocity_knot = 0x2785, "velocity (knot)"
    velocity_metres_per_second = 0x2712, "velocity (metres per second)"
    velocity_mile_per_hour = 0x27a7, "velocity (mile per hour)"
    volume_cubic_metres = 0x2711, "volume (cubic metres)"
    volume_flow_litre_per_second = 0x27c2, "volume flow (litre per second)"
    volume_litre = 0x2767, "volume (litre)"
    wavenumber_reciprocal_metre = 0x2714, "wavenumber (reciprocal metre)"


class Appearance(IntEnumWithDescription):
    """
    Appearance enumeration for use with advertising data
    """
    unknown = 0, "Unknown"
    phone = 64, "Phone"
    computer = 128, "Computer"
    watch = 192, "Watch"
    sports_watch = 193, "Sports Watch"
    clock = 256, "Clock"
    display = 320, "Display"
    remote_control = 384, "Remote Control"
    eye_glasses = 448, "Eye-glasses"
    tag = 512, "Tag"
    keyring = 576, "Keyring"
    media_player = 640, "Media Player"
    barcode_scanner = 704, "Barcode Scanner"
    thermometer = 768, "Thermometer"
    thermometer_ear = 769, "Thermometer: Ear"
    heart_rate_sensor = 832, "Heart rate Sensor"
    heart_rate_sensor_heart_rate_belt = 833, "Heart Rate Sensor: Heart Rate Belt"
    blood_pressure = 896, "Blood Pressure"
    blood_pressure_arm = 897, "Blood Pressure: Arm"
    blood_pressure_wrist = 898, "Blood Pressure: Wrist"
    hid = 960, "Human Interface Device (HID)"
    hid_keyboard = 961, "Keyboard"
    hid_mouse = 962, "Mouse"
    hid_joystick = 963, "Joystick"
    hid_gamepad = 964, "Gamepadtype)"
    hid_digitizer = 965, "Digitizer Tablet"
    hid_card_reader = 966, "Card Reader"
    hid_digital_pen = 967, "Digital Pen"
    hid_barcode = 968, "Barcode Scanner"
    glucose_meter = 1024, "Glucose Meter"
    running_walking_sensor = 1088, "Running Walking Sensor"
    running_walking_sensor_in_shoe = 1089, "Running Walking Sensor: In-Shoe"
    running_walking_sensor_on_shoe = 1090, "Running Walking Sensor: On-Shoe"
    running_walking_sensor_on_hip = 1091, "Running Walking Sensor: On-Hip"
    cycling = 1152, "Cycling"
    cycling_cycling_computer = 1153, "Cycling: Cycling Computer"
    cycling_speed_sensor = 1154, "Cycling: Speed Sensor"
    cycling_cadence_sensor = 1155, "Cycling: Cadence Sensor"
    cycling_power_sensor = 1156, "Cycling: Power Sensor"
    cycling_speed_cadence_sensor = 1157, "Cycling: Speed and Cadence Sensor"
    pulse_oximeter = 3136, "Pulse Oximeter"
    pulse_oximeter_fingertip = 3137, "Fingertip Pulse Oximeter"
    pulse_oximeter_wrist_worn = 3138, "Wrist Pulse Oximeter"
    weight_scale = 3200, "Weight Scale"
    outdoor_sports_act = 5184, "Outdoor Sports Activity"
    outdoor_sports_act_loc_disp = 5185, "Location Display Device"
    outdoor_sports_act_loc_and_nav_disp = 5186, "Location and Navigation Display Device"
    outdoor_sports_act_loc_pod = 5187, "Location Pod"
    outdoor_sports_act_loc_and_nav_pod = 5188, "Location and Navigation Pod"

    def as_bytes(self):
        return struct.pack("<H", self)
