"""
Bluetooth SIG defined UUIDs, populated from their website.

.. seealso:: https://btprodspecificationrefs.blob.core.windows.net/assigned-values/16-bit%20UUID%20Numbers%20Document.pdf

Definitions last scraped on 2022/05/02
"""
from typing import Dict

from blatann.uuid import Uuid, Uuid16, Uuid128
from blatann.utils import snake_case_to_capitalized_words


class DeclarationUuid:
    """
    UUIDs used for declarations within the GATT Database
    """
    primary_service = Uuid16("2800")
    secondary_service = Uuid16("2801")
    include = Uuid16("2802")
    characteristic = Uuid16("2803", "Characteristic Declaration")


class DescriptorUuid:
    """
    UUIDs that are used for characteristic descriptors
    """
    extended_properties       = Uuid16("2900")
    user_description          = Uuid16("2901")
    cccd                      = Uuid16("2902", "Client Characteristic Configuration Descriptor")
    sccd                      = Uuid16("2903", "Server Characteristic Configuration Descriptor")
    presentation_format       = Uuid16("2904")
    aggregate_format          = Uuid16("2905")
    valid_range               = Uuid16("2906")
    external_report_reference = Uuid16("2907")
    report_reference          = Uuid16("2908")
    number_of_digitals        = Uuid16("2909")
    value_trigger_setting     = Uuid16("290a")
    es_configuration          = Uuid16("290b")
    es_measurement            = Uuid16("290c")
    es_trigger_setting        = Uuid16("290d")
    time_trigger_setting      = Uuid16("290e")
    complete_br_edr_transport_block_data = Uuid16("290f")


class ServiceUuid:
    """
    Bluetooth SIG defined service UUIDs
    """
    alert_notification            = Uuid16("1811")
    audio_input_control           = Uuid16("1843")
    audio_stream_control          = Uuid16("184e")
    automation_io                 = Uuid16("1815")
    basic_audio_announcement      = Uuid16("1851")
    battery_service               = Uuid16("180f")
    binary_sensor                 = Uuid16("183b")
    blood_pressure                = Uuid16("1810")
    body_composition              = Uuid16("181b")
    bond_management               = Uuid16("181e")
    broadcast_audio_announcement  = Uuid16("1852")
    broadcast_audio_scan          = Uuid16("184f")
    common_audio                  = Uuid16("1853")
    constant_tone_extension       = Uuid16("184a")
    continuous_glucose_monitoring = Uuid16("181f")
    coordinated_set_identification= Uuid16("1846")
    current_time                  = Uuid16("1805")
    cycling_power                 = Uuid16("1818")
    cycling_speed_and_cadence     = Uuid16("1816")
    device_information            = Uuid16("180a")
    device_time                   = Uuid16("1847")
    emergency_configuration       = Uuid16("183c")
    environmental_sensing         = Uuid16("181a")
    fitness_machine               = Uuid16("1826")
    generic_access                = Uuid16("1800")
    generic_attribute             = Uuid16("1801")
    generic_media_control         = Uuid16("1849")
    generic_telephone_bearer      = Uuid16("184c")
    glucose                       = Uuid16("1808")
    health_thermometer            = Uuid16("1809")
    hearing_access                = Uuid16("1854")
    heart_rate                    = Uuid16("180d")
    http_proxy                    = Uuid16("1823")
    human_interface_device        = Uuid16("1812")
    immediate_alert               = Uuid16("1802")
    indoor_positioning            = Uuid16("1821")
    insulin_delivery              = Uuid16("183a")
    internet_protocol_support     = Uuid16("1820")
    link_loss                     = Uuid16("1803")
    location_and_navigation       = Uuid16("1819")
    media_control                 = Uuid16("1848")
    mesh_provisioning             = Uuid16("1827")
    mesh_proxy                    = Uuid16("1828")
    microphone_control            = Uuid16("184d")
    next_dst_change               = Uuid16("1807")
    object_transfer               = Uuid16("1825")
    phone_alert_status            = Uuid16("180e")
    physical_activity_monitor     = Uuid16("183e")
    published_audio_capabilities  = Uuid16("1850")
    pulse_oximeter                = Uuid16("1822")
    reconnection_configuration    = Uuid16("1829")
    reference_time_update         = Uuid16("1806")
    running_speed_and_cadence     = Uuid16("1814")
    scan_parameters               = Uuid16("1813")
    telephone_bearer              = Uuid16("184b")
    tmas                          = Uuid16("1855")
    transport_discovery           = Uuid16("1824")
    tx_power                      = Uuid16("1804")
    user_data                     = Uuid16("181c")
    volume_control                = Uuid16("1844")
    volume_offset_control         = Uuid16("1845")
    weight_scale                  = Uuid16("181d")


class CharacteristicUuid:
    """
    Bluetooth SIG defined characteristic UUIDs
    """
    active_preset_index             = Uuid16("2bdc")
    activity_current_session        = Uuid16("2b44")
    activity_goal                   = Uuid16("2b4e")
    adv_constant_tone_interval      = Uuid16("2bb1")
    adv_constant_tone_min_length    = Uuid16("2bae")
    adv_constant_tone_min_tx_count  = Uuid16("2baf")
    adv_constant_tone_phy           = Uuid16("2bb2")
    adv_constant_tone_tx_duration   = Uuid16("2bb0")
    aerobic_heart_rate_lower_limit  = Uuid16("2a7e")
    aerobic_heart_rate_upper_limit  = Uuid16("2a84")
    aerobic_threshold               = Uuid16("2a7f")
    age                             = Uuid16("2a80")
    aggregate                       = Uuid16("2a5a")
    alert_category_id               = Uuid16("2a43")
    alert_category_id_bit_mask      = Uuid16("2a42")
    alert_level                     = Uuid16("2a06")
    alert_notification_control_point = Uuid16("2a44")
    alert_status                    = Uuid16("2a3f")
    altitude                        = Uuid16("2ab3")
    ammonia_concentration           = Uuid16("2bcf")
    anaerobic_heart_rate_lower_limit = Uuid16("2a81")
    anaerobic_heart_rate_upper_limit = Uuid16("2a82")
    anaerobic_threshold             = Uuid16("2a83")
    analog                          = Uuid16("2a58")
    analog_output                   = Uuid16("2a59")
    apparent_wind_direction         = Uuid16("2a73")
    apparent_wind_speed             = Uuid16("2a72")
    appearance                      = Uuid16("2a01")
    ase_control_point               = Uuid16("2bc6")
    audio_input_control_point       = Uuid16("2b7b")
    audio_input_description         = Uuid16("2b7c")
    audio_input_state               = Uuid16("2b77")
    audio_input_status              = Uuid16("2b7a")
    audio_input_type                = Uuid16("2b79")
    audio_location                  = Uuid16("2b81")
    audio_output_description        = Uuid16("2b83")
    available_audio_contexts        = Uuid16("2bcd")
    average_current                 = Uuid16("2ae0")
    average_voltage                 = Uuid16("2ae1")
    barometric_pressure_trend       = Uuid16("2aa3")
    battery_level                   = Uuid16("2a19")
    battery_level_state             = Uuid16("2a1b")
    battery_power_state             = Uuid16("2a1a")
    bearer_list_current_calls       = Uuid16("2bb9")
    bearer_provider_name            = Uuid16("2bb3")
    bearer_signal_strength          = Uuid16("2bb7")
    bearer_signal_strength_reporting_interval = Uuid16("2bb8")
    bearer_technology               = Uuid16("2bb5")
    bearer_uci                      = Uuid16("2bb4")
    bearer_uri_schemes_supported_list = Uuid16("2bb6")
    blood_pressure_feature          = Uuid16("2a49")
    blood_pressure_measurement      = Uuid16("2a35")
    blood_pressure_record           = Uuid16("2b36")
    bluetooth_sig_data              = Uuid16("2b39")
    body_composition_feature        = Uuid16("2a9b")
    body_composition_measurement    = Uuid16("2a9c")
    body_sensor_location            = Uuid16("2a38")
    bond_management_control_point   = Uuid16("2aa4")
    bond_management_feature         = Uuid16("2aa5")
    boolean                         = Uuid16("2ae2")
    boot_keyboard_input_report      = Uuid16("2a22")
    boot_keyboard_output_report     = Uuid16("2a32")
    boot_mouse_input_report         = Uuid16("2a33")
    br_edr_handover_data            = Uuid16("2b38")
    broadcast_audio_scan_control_point = Uuid16("2bc7")
    broadcast_receive_state         = Uuid16("2bc8")
    bss_control_point               = Uuid16("2b2b")
    bss_response                    = Uuid16("2b2c")
    call_control_point              = Uuid16("2bbe")
    call_control_point_optional_opcodes = Uuid16("2bbf")
    call_friendly_name              = Uuid16("2bc2")
    call_state                      = Uuid16("2bbd")
    caloric_intake                  = Uuid16("2b50")
    carbon_monoxide_concentration   = Uuid16("2bd0")
    cardiorespiratory_activity_instantaneous_data = Uuid16("2b3e")
    cardiorespiratory_activity_summary_data = Uuid16("2b3f")
    central_address_resolution      = Uuid16("2aa6")
    cgm_feature                     = Uuid16("2aa8")
    cgm_measurement                 = Uuid16("2aa7")
    cgm_session_run_time            = Uuid16("2aab")
    cgm_session_start_time          = Uuid16("2aaa")
    cgm_specific_ops_control_point  = Uuid16("2aac")
    cgm_status                      = Uuid16("2aa9")
    chromatic_distance_from_planckian = Uuid16("2ae3")
    chromaticity_coordinate         = Uuid16("2b1c")
    chromaticity_coordinates        = Uuid16("2ae4")
    chromaticity_in_cct_and_duv_values = Uuid16("2ae5")
    chromaticity_tolerance          = Uuid16("2ae6")
    cie_color_rendering_index       = Uuid16("2ae7")
    client_supported_features       = Uuid16("2b29")
    coefficient                     = Uuid16("2ae8")
    constant_tone_extension_enable  = Uuid16("2bad")
    content_control_id              = Uuid16("2bba")
    coordinated_set_size            = Uuid16("2b85")
    correlated_color_temperature    = Uuid16("2ae9")
    count_16                        = Uuid16("2aea")
    count_24                        = Uuid16("2aeb")
    country_code                    = Uuid16("2aec")
    cross_trainer_data              = Uuid16("2ace")
    csc_feature                     = Uuid16("2a5c")
    csc_measurement                 = Uuid16("2a5b")
    current_group_object_id         = Uuid16("2ba0")
    current_time                    = Uuid16("2a2b")
    current_track_object_id         = Uuid16("2b9d")
    current_track_segments_object_id = Uuid16("2b9c")
    cycling_power_control_point     = Uuid16("2a66")
    cycling_power_feature           = Uuid16("2a65")
    cycling_power_measurement       = Uuid16("2a63")
    cycling_power_vector            = Uuid16("2a64")
    database_change_increment       = Uuid16("2a99")
    database_hash                   = Uuid16("2b2a")
    date_of_birth                   = Uuid16("2a85")
    date_of_threshold_assessment    = Uuid16("2a86")
    date_time                       = Uuid16("2a08")
    date_utc                        = Uuid16("2aed")
    day_date_time                   = Uuid16("2a0a")
    day_of_week                     = Uuid16("2a09")
    descriptor_value_changed        = Uuid16("2a7d")
    device_name                     = Uuid16("2a00")
    device_time                     = Uuid16("2b90")
    device_time_control_point       = Uuid16("2b91")
    device_time_feature             = Uuid16("2b8e")
    device_time_parameters          = Uuid16("2b8f")
    device_wearing_position         = Uuid16("2b4b")
    dew_point                       = Uuid16("2a7b")
    digital                         = Uuid16("2a56")
    digital_output                  = Uuid16("2a57")
    directory_listing               = Uuid16("2acb")
    dst_offset                      = Uuid16("2a0d")
    electric_current                = Uuid16("2aee")
    electric_current_range          = Uuid16("2aef")
    electric_current_specification  = Uuid16("2af0")
    electric_current_statistics     = Uuid16("2af1")
    elevation                       = Uuid16("2a6c")
    email_address                   = Uuid16("2a87")
    emergency_id                    = Uuid16("2b2d")
    emergency_text                  = Uuid16("2b2e")
    energy                          = Uuid16("2af2")
    energy_in_a_period_of_day       = Uuid16("2af3")
    enhanced_blood_pressure_measurement = Uuid16("2b34")
    enhanced_intermediate_cuff_pressure = Uuid16("2b35")
    event_statistics                = Uuid16("2af4")
    exact_time_100                  = Uuid16("2a0b")
    exact_time_256                  = Uuid16("2a0c")
    fat_burn_heart_rate_lower_limit = Uuid16("2a88")
    fat_burn_heart_rate_upper_limit = Uuid16("2a89")
    firmware_revision_string        = Uuid16("2a26")
    first_name                      = Uuid16("2a8a")
    fitness_machine_control_point   = Uuid16("2ad9")
    fitness_machine_feature         = Uuid16("2acc")
    fitness_machine_status          = Uuid16("2ada")
    five_zone_heart_rate_limits     = Uuid16("2a8b")
    fixed_string_16                 = Uuid16("2af5")
    fixed_string_24                 = Uuid16("2af6")
    fixed_string_36                 = Uuid16("2af7")
    fixed_string_8                  = Uuid16("2af8")
    floor_number                    = Uuid16("2ab2")
    four_zone_heart_rate_limits     = Uuid16("2b4c")
    gain_settings_attribute         = Uuid16("2b78")
    gender                          = Uuid16("2a8c")
    general_activity_instantaneous_data = Uuid16("2b3c")
    general_activity_summary_data   = Uuid16("2b3d")
    generic_level                   = Uuid16("2af9")
    global_trade_item_number        = Uuid16("2afa")
    glucose_feature                 = Uuid16("2a51")
    glucose_measurement             = Uuid16("2a18")
    glucose_measurement_context     = Uuid16("2a34")
    group_object_type               = Uuid16("2bac")
    gust_factor                     = Uuid16("2a74")
    handedness                      = Uuid16("2b4a")
    hardware_revision_string        = Uuid16("2a27")
    hearing_aid_features            = Uuid16("2bda")
    hearing_aid_preset_control_point = Uuid16("2bdb")
    heart_rate_control_point        = Uuid16("2a39")
    heart_rate_max                  = Uuid16("2a8d")
    heart_rate_measurement          = Uuid16("2a37")
    heat_index                      = Uuid16("2a7a")
    height                          = Uuid16("2a8e")
    hid_control_point               = Uuid16("2a4c")
    hid_information                 = Uuid16("2a4a")
    high_intensity_exercise_threshold = Uuid16("2b4d")
    high_resolution_height          = Uuid16("2b47")
    hip_circumference               = Uuid16("2a8f")
    http_control_point              = Uuid16("2aba")
    http_entity_body                = Uuid16("2ab9")
    http_headers                    = Uuid16("2ab7")
    http_status_code                = Uuid16("2ab8")
    https_security                  = Uuid16("2abb")
    humidity                        = Uuid16("2a6f")
    idd_annunciation_status         = Uuid16("2b22")
    idd_command_control_point       = Uuid16("2b25")
    idd_command_data                = Uuid16("2b26")
    idd_features                    = Uuid16("2b23")
    idd_history_data                = Uuid16("2b28")
    idd_record_access_control_point = Uuid16("2b27")
    idd_status                      = Uuid16("2b21")
    idd_status_changed              = Uuid16("2b20")
    idd_status_reader_control_point = Uuid16("2b24")
    ieee11073_20601_regulatory_certification_data_list = Uuid16("2a2a")
    illuminance                     = Uuid16("2afb")
    incoming_call                   = Uuid16("2bc1")
    incoming_call_target_bearer_uri = Uuid16("2bbc")
    indoor_bike_data                = Uuid16("2ad2")
    indoor_positioning_configuration = Uuid16("2aad")
    intermediate_cuff_pressure      = Uuid16("2a36")
    intermediate_temperature        = Uuid16("2a1e")
    irradiance                      = Uuid16("2a77")
    language                        = Uuid16("2aa2")
    last_name                       = Uuid16("2a90")
    latitude                        = Uuid16("2aae")
    ln_control_point                = Uuid16("2a6b")
    ln_feature                      = Uuid16("2a6a")
    local_east_coordinate           = Uuid16("2ab1")
    local_north_coordinate          = Uuid16("2ab0")
    local_time_information          = Uuid16("2a0f")
    location_and_speed              = Uuid16("2a67")
    location_name                   = Uuid16("2ab5")
    longitude                       = Uuid16("2aaf")
    luminous_efficacy               = Uuid16("2afc")
    luminous_energy                 = Uuid16("2afd")
    luminous_exposure               = Uuid16("2afe")
    luminous_flux                   = Uuid16("2aff")
    luminous_flux_range             = Uuid16("2b00")
    luminous_intensity              = Uuid16("2b01")
    magnetic_declination            = Uuid16("2a2c")
    magnetic_flux_density_2d        = Uuid16("2aa0")
    magnetic_flux_density_3d        = Uuid16("2aa1")
    manufacturer_name_string        = Uuid16("2a29")
    mass_flow                       = Uuid16("2b02")
    maximum_recommended_heart_rate  = Uuid16("2a91")
    measurement_interval            = Uuid16("2a21")
    media_control_point             = Uuid16("2ba4")
    media_control_point_opcodes_supported = Uuid16("2ba5")
    media_player_icon_object_id     = Uuid16("2b94")
    media_player_icon_object_type   = Uuid16("2ba9")
    media_player_icon_url           = Uuid16("2b95")
    media_player_name               = Uuid16("2b93")
    media_state                     = Uuid16("2ba3")
    mesh_provisioning_data_in       = Uuid16("2adb")
    mesh_provisioning_data_out      = Uuid16("2adc")
    mesh_proxy_data_in              = Uuid16("2add")
    mesh_proxy_data_out             = Uuid16("2ade")
    methane_concentration           = Uuid16("2bd1")
    middle_name                     = Uuid16("2b48")
    model_number_string             = Uuid16("2a24")
    mute                            = Uuid16("2bc3")
    navigation                      = Uuid16("2a68")
    network_availability            = Uuid16("2a3e")
    new_alert                       = Uuid16("2a46")
    next_track_object_id            = Uuid16("2b9e")
    nitrogen_dioxide_concentration  = Uuid16("2bd2")
    non_methane_volatile_organic_compounds_concentration = Uuid16("2bd3")
    object_action_control_point     = Uuid16("2ac5")
    object_changed                  = Uuid16("2ac8")
    object_first_created            = Uuid16("2ac1")
    object_id                       = Uuid16("2ac3")
    object_last_modified            = Uuid16("2ac2")
    object_list_control_point       = Uuid16("2ac6")
    object_list_filter              = Uuid16("2ac7")
    object_name                     = Uuid16("2abe")
    object_properties               = Uuid16("2ac4")
    object_size                     = Uuid16("2ac0")
    object_type                     = Uuid16("2abf")
    ots_feature                     = Uuid16("2abd")
    ozone_concentration             = Uuid16("2bd4")
    parent_group_object_id          = Uuid16("2b9f")
    particulate_matter_10_concentration  = Uuid16("2bd7")
    particulate_matter_1_concentration   = Uuid16("2bd5")
    particulate_matter_2_5_concentration = Uuid16("2bd6")
    perceived_lightness               = Uuid16("2b03")
    percentage_8                      = Uuid16("2b04")
    peripheral_preferred_connection_parameters = Uuid16("2a04")
    peripheral_privacy_flag         = Uuid16("2a02")
    physical_activity_monitor_control_point = Uuid16("2b43")
    physical_activity_monitor_features      = Uuid16("2b3b")
    physical_activity_session_descriptor    = Uuid16("2b45")
    playback_speed                  = Uuid16("2b9a")
    playing_order                   = Uuid16("2ba1")
    playing_orders_supported        = Uuid16("2ba2")
    plx_continuous_measurement      = Uuid16("2a5f")
    plx_features                    = Uuid16("2a60")
    plx_spot_check_measurement      = Uuid16("2a5e")
    pnp_id                          = Uuid16("2a50")
    pollen_concentration            = Uuid16("2a75")
    position_2d                     = Uuid16("2a2f")
    position_3d                     = Uuid16("2a30")
    position_quality                = Uuid16("2a69")
    power                           = Uuid16("2b05")
    power_specification             = Uuid16("2b06")
    preferred_units                 = Uuid16("2b46")
    pressure                        = Uuid16("2a6d")
    protocol_mode                   = Uuid16("2a4e")
    pulse_oximetry_control_point    = Uuid16("2a62")
    rainfall                        = Uuid16("2a78")
    rc_feature                      = Uuid16("2b1d")
    rc_settings                     = Uuid16("2b1e")
    reconnection_address            = Uuid16("2a03")
    reconnection_configuration_control_point = Uuid16("2b1f")
    record_access_control_point     = Uuid16("2a52")
    reference_time_information      = Uuid16("2a14")
    registered_user_characteristic  = Uuid16("2b37")
    relative_runtime_current_range       = Uuid16("2b07")
    relative_runtime_generic_level_range = Uuid16("2b08")
    relative_value_period_of_day         = Uuid16("2b0b")
    relative_value_temperature_range     = Uuid16("2b0c")
    relative_value_voltage_range         = Uuid16("2b09")
    relative_value_illuminance_range     = Uuid16("2b0a")
    removable                       = Uuid16("2a3a")
    report                          = Uuid16("2a4d")
    report_map                      = Uuid16("2a4b")
    resolvable_private_address_only = Uuid16("2ac9")
    resting_heart_rate              = Uuid16("2a92")
    ringer_control_point            = Uuid16("2a40")
    ringer_setting                  = Uuid16("2a41")
    rower_data                      = Uuid16("2ad1")
    rsc_feature                     = Uuid16("2a54")
    rsc_measurement                 = Uuid16("2a53")
    sc_control_point                = Uuid16("2a55")
    scan_interval_window            = Uuid16("2a4f")
    scan_refresh                    = Uuid16("2a31")
    scientific_temperature_celsius  = Uuid16("2a3c")
    secondary_time_zone             = Uuid16("2a10")
    search_control_point            = Uuid16("2ba7")
    search_results_object_id        = Uuid16("2ba6")
    sedentary_interval_notification = Uuid16("2b4f")
    seeking_speed                   = Uuid16("2b9b")
    sensor_location                 = Uuid16("2a5d")
    serial_number_string            = Uuid16("2a25")
    server_supported_features       = Uuid16("2b3a")
    service_changed                 = Uuid16("2a05")
    service_required                = Uuid16("2a3b")
    set_identity_resolving_key      = Uuid16("2b84")
    set_member_lock                 = Uuid16("2b86")
    set_member_rank                 = Uuid16("2b87")
    sink_ase                        = Uuid16("2bc4")
    sink_audio_locations            = Uuid16("2bca")
    sink_pac                        = Uuid16("2bc9")
    sleep_activity_instantaneous_data = Uuid16("2b41")
    sleep_activity_summary_data     = Uuid16("2b42")
    software_revision_string        = Uuid16("2a28")
    source_ase                      = Uuid16("2bc5")
    source_audio_locations          = Uuid16("2bcc")
    source_pac                      = Uuid16("2bcb")
    sport_type_for_aerobic_and_anaerobic_thresholds = Uuid16("2a93")
    stair_climber_data              = Uuid16("2ad0")
    status_flags                    = Uuid16("2bbb")
    step_climber_data               = Uuid16("2acf")
    step_counter_activity_summary_data = Uuid16("2b40")
    stride_length                   = Uuid16("2b49")
    string                          = Uuid16("2a3d")
    sulfur_dioxide_concentration    = Uuid16("2bd8")
    sulfur_hexafluoride_concentration = Uuid16("2bd9")
    supported_audio_contexts        = Uuid16("2bce")
    supported_heart_rate_range      = Uuid16("2ad7")
    supported_inclination_range     = Uuid16("2ad5")
    supported_new_alert_category    = Uuid16("2a47")
    supported_power_range           = Uuid16("2ad8")
    supported_resistance_level_range = Uuid16("2ad6")
    supported_speed_range           = Uuid16("2ad4")
    supported_unread_alert_category = Uuid16("2a48")
    system_id                       = Uuid16("2a23")
    tds_control_point               = Uuid16("2abc")
    temperature                     = Uuid16("2a6e")
    temperature_celsius             = Uuid16("2a1f")
    temperature_fahrenheit          = Uuid16("2a20")
    temperature_8                   = Uuid16("2b0d")
    temperature_8_in_a_period_of_day = Uuid16("2b0e")
    temperature_8_statistics        = Uuid16("2b0f")
    temperature_measurement         = Uuid16("2a1c")
    temperature_range               = Uuid16("2b10")
    temperature_statistics          = Uuid16("2b11")
    temperature_type                = Uuid16("2a1d")
    termination_reason              = Uuid16("2bc0")
    three_zone_heart_rate_limits    = Uuid16("2a94")
    time_accuracy                   = Uuid16("2a12")
    time_broadcast                  = Uuid16("2a15")
    time_change_log_data            = Uuid16("2b92")
    time_decihour_8                 = Uuid16("2b12")
    time_exponential_8              = Uuid16("2b13")
    time_hour_24                    = Uuid16("2b14")
    time_millisecond_24             = Uuid16("2b15")
    time_second_16                  = Uuid16("2b16")
    time_second_8                   = Uuid16("2b17")
    time_source                     = Uuid16("2a13")
    time_update_control_point       = Uuid16("2a16")
    time_update_state               = Uuid16("2a17")
    time_with_dst                   = Uuid16("2a11")
    time_zone                       = Uuid16("2a0e")
    tmap_role                       = Uuid16("2b51")
    track_changed                   = Uuid16("2b96")
    track_duration                  = Uuid16("2b98")
    track_object_type               = Uuid16("2bab")
    track_position                  = Uuid16("2b99")
    track_segments_object_type      = Uuid16("2baa")
    track_title                     = Uuid16("2b97")
    training_status                 = Uuid16("2ad3")
    treadmill_data                  = Uuid16("2acd")
    true_wind_direction             = Uuid16("2a71")
    true_wind_speed                 = Uuid16("2a70")
    two_zone_heart_rate_limit       = Uuid16("2a95")
    tx_power_level                  = Uuid16("2a07")
    uncertainty                     = Uuid16("2ab4")
    unread_alert_status             = Uuid16("2a45")
    unspecified                     = Uuid16("2aca")
    uri                             = Uuid16("2ab6")
    user_control_point              = Uuid16("2a9f")
    user_index                      = Uuid16("2a9a")
    uv_index                        = Uuid16("2a76")
    vo2_max                         = Uuid16("2a96")
    voltage                         = Uuid16("2b18")
    voltage_specification           = Uuid16("2b19")
    voltage_statistics              = Uuid16("2b1a")
    volume_control_point            = Uuid16("2b7e")
    volume_flags                    = Uuid16("2b7f")
    volume_flow                     = Uuid16("2b1b")
    volume_offset_control_point     = Uuid16("2b82")
    volume_offset_state             = Uuid16("2b80")
    volume_state                    = Uuid16("2b7d")
    waist_circumference             = Uuid16("2a97")
    weight                          = Uuid16("2a98")
    weight_measurement              = Uuid16("2a9d")
    weight_scale_feature            = Uuid16("2a9e")
    wind_chill                      = Uuid16("2a79")


"""Maps UUIDs in this file to a string description of the UUID"""
UUID_DESCRIPTION_MAP: Dict[Uuid, str] = {}

for t in [DeclarationUuid, DescriptorUuid, ServiceUuid, CharacteristicUuid]:
    for k, v in t.__dict__.items():
        if not isinstance(v, Uuid):
            continue
        if not v.description:
            v.description = snake_case_to_capitalized_words(k)
        UUID_DESCRIPTION_MAP[v] = v.description


company_assigned_uuid16s = {
    Uuid16("fce1"): "Sony Group Corporation",
    Uuid16("fce2"): "Baracoda Daily Healthtech",
    Uuid16("fce3"): "Smith & Nephew Medical Limited",
    Uuid16("fce4"): "Samsara Networks, Inc",
    Uuid16("fce5"): "Samsara Networks, Inc",
    Uuid16("fce6"): "Guard RFID Solutions Inc.",
    Uuid16("fce7"): "TKH Security B.V.",
    Uuid16("fce8"): "ITT Industries",
    Uuid16("fce9"): "MindRhythm, Inc.",
    Uuid16("fcea"): "Chess Wise B.V.",
    Uuid16("fceb"): "Avi-On",
    Uuid16("fcec"): "Griffwerk GmbH",
    Uuid16("fced"): "Workaround Gmbh",
    Uuid16("fcee"): "Velentium, LLC",
    Uuid16("fcef"): "Divesoft s.r.o.",
    Uuid16("fcf0"): "Security Enhancement Systems, LLC",
    Uuid16("fcf1"): "Google LLC",
    Uuid16("fcf2"): "Bitwards Oy",
    Uuid16("fcf3"): "Armatura LLC",
    Uuid16("fcf4"): "Allegion",
    Uuid16("fcf5"): "Trident Communication Technology, LLC",
    Uuid16("fcf6"): "The Linux Foundation",
    Uuid16("fcf7"): "Honor Device Co., Ltd.",
    Uuid16("fcf8"): "Honor Device Co., Ltd.",
    Uuid16("fcf9"): "Leupold & Stevens, Inc.",
    Uuid16("fcfa"): "Leupold & Stevens, Inc.",
    Uuid16("fcfb"): "Shenzhen Benwei Media Co., Ltd.",
    Uuid16("fcfc"): "Barrot Technology Limited",
    Uuid16("fcfd"): "Barrot Technology Limited",
    Uuid16("fcfe"): "Sennheiser Consumer Audio GmbH",
    Uuid16("fcff"): "701x",
    Uuid16("fd00"): "FUTEK Advanced Sensor Technology, Inc.",
    Uuid16("fd01"): "Sanvita Medical Corporation",
    Uuid16("fd02"): "LEGO System A/S",
    Uuid16("fd03"): "Quuppa Oy",
    Uuid16("fd04"): "Shure Inc.",
    Uuid16("fd05"): "Qualcomm Technologies, Inc.",
    Uuid16("fd06"): "RACE-AI LLC",
    Uuid16("fd07"): "Swedlock AB",
    Uuid16("fd08"): "Bull Group Incorporated Company",
    Uuid16("fd09"): "Cousins and Sears LLC",
    Uuid16("fd0a"): "Luminostics, Inc.",
    Uuid16("fd0b"): "Luminostics, Inc.",
    Uuid16("fd0c"): "OSM HK Limited",
    Uuid16("fd0d"): "Blecon Ltd",
    Uuid16("fd0e"): "HerdDogg, Inc",
    Uuid16("fd0f"): "AEON MOTOR CO.,LTD.",
    Uuid16("fd10"): "AEON MOTOR CO.,LTD.",
    Uuid16("fd11"): "AEON MOTOR CO.,LTD.",
    Uuid16("fd12"): "AEON MOTOR CO.,LTD.",
    Uuid16("fd13"): "BRG Sports, Inc.",
    Uuid16("fd14"): "BRG Sports, Inc.",
    Uuid16("fd15"): "Panasonic Corporation",
    Uuid16("fd16"): "Sensitech, Inc.",
    Uuid16("fd17"): "LEGIC Identsystems AG",
    Uuid16("fd18"): "LEGIC Identsystems AG",
    Uuid16("fd19"): "Smith & Nephew Medical Limited",
    Uuid16("fd1a"): "CSIRO",
    Uuid16("fd1b"): "Helios Sports, Inc.",
    Uuid16("fd1c"): "Brady Worldwide Inc.",
    Uuid16("fd1d"): "Samsung Electronics Co., Ltd",
    Uuid16("fd1e"): "Plume Design Inc.",
    Uuid16("fd1f"): "3M",
    Uuid16("fd20"): "GN Hearing A/S",
    Uuid16("fd21"): "Huawei Technologies Co., Ltd.",
    Uuid16("fd22"): "Huawei Technologies Co., Ltd.",
    Uuid16("fd23"): "DOM Sicherheitstechnik GmbH & Co. KG",
    Uuid16("fd24"): "GD Midea Air-Conditioning Equipment Co., Ltd.",
    Uuid16("fd25"): "GD Midea Air-Conditioning Equipment Co., Ltd.",
    Uuid16("fd26"): "Novo Nordisk A/S",
    Uuid16("fd27"): "i2Systems",
    Uuid16("fd28"): "Julius Blum GmbH",
    Uuid16("fd29"): "Asahi Kasei Corporation",
    Uuid16("fd2a"): "Sony Corporation",
    Uuid16("fd2b"): "The Access Technologies",
    Uuid16("fd2c"): "The Access Technologies",
    Uuid16("fd2d"): "Xiaomi Inc.",
    Uuid16("fd2e"): "Bitstrata Systems Inc.",
    Uuid16("fd2f"): "Bitstrata Systems Inc.",
    Uuid16("fd30"): "Sesam Solutions BV",
    Uuid16("fd31"): "LG Electronics Inc.",
    Uuid16("fd32"): "Gemalto Holding BV",
    Uuid16("fd33"): "DashLogic, Inc.",
    Uuid16("fd34"): "Aerosens LLC.",
    Uuid16("fd35"): "Transsion Holdings Limited",
    Uuid16("fd36"): "Google LLC",
    Uuid16("fd37"): "TireCheck GmbH",
    Uuid16("fd38"): "Danfoss A/S",
    Uuid16("fd39"): "PREDIKTAS",
    Uuid16("fd3a"): "Verkada Inc.",
    Uuid16("fd3b"): "Verkada Inc.",
    Uuid16("fd3c"): "Redline Communications Inc.",
    Uuid16("fd3d"): "Woan Technology (Shenzhen) Co., Ltd.",
    Uuid16("fd3e"): "Pure Watercraft, inc.",
    Uuid16("fd3f"): "Cognosos, Inc",
    Uuid16("fd40"): "Beflex Inc.",
    Uuid16("fd41"): "Amazon Lab126",
    Uuid16("fd42"): "Globe (Jiangsu) Co.,Ltd",
    Uuid16("fd43"): "Apple Inc.",
    Uuid16("fd44"): "Apple Inc.",
    Uuid16("fd45"): "GB Solution co.,Ltd",
    Uuid16("fd46"): "Lemco IKE",
    Uuid16("fd47"): "Liberty Global Inc.",
    Uuid16("fd48"): "Geberit International AG",
    Uuid16("fd49"): "Panasonic Corporation",
    Uuid16("fd4a"): "Sigma Elektro GmbH",
    Uuid16("fd4b"): "Samsung Electronics Co., Ltd.",
    Uuid16("fd4c"): "Adolf Wuerth GmbH & Co KG",
    Uuid16("fd4d"): "70mai Co.,Ltd.",
    Uuid16("fd4e"): "70mai Co.,Ltd.",
    Uuid16("fd4f"): "Forkbeard Technologies AS",
    Uuid16("fd50"): "Hangzhou Tuya Information Technology Co., Ltd",
    Uuid16("fd51"): "UTC Fire and Security",
    Uuid16("fd52"): "UTC Fire and Security",
    Uuid16("fd53"): "PCI Private Limited",
    Uuid16("fd54"): "Qingdao Haier Technology Co., Ltd.",
    Uuid16("fd55"): "Braveheart Wireless, Inc.",
    Uuid16("fd57"): "Volvo Car Corporation",
    Uuid16("fd58"): "Volvo Car Corporation",
    Uuid16("fd59"): "Samsung Electronics Co., Ltd.",
    Uuid16("fd5a"): "Samsung Electronics Co., Ltd.",
    Uuid16("fd5b"): "V2SOFT INC.",
    Uuid16("fd5c"): "React Mobile",
    Uuid16("fd5d"): "maxon motor ltd.",
    Uuid16("fd5e"): "Tapkey GmbH",
    Uuid16("fd5f"): "Oculus VR, LLC",
    Uuid16("fd60"): "Sercomm Corporation",
    Uuid16("fd61"): "Arendi AG",
    Uuid16("fd62"): "Fitbit, Inc.",
    Uuid16("fd63"): "Fitbit, Inc.",
    Uuid16("fd64"): "INRIA",
    Uuid16("fd65"): "Razer Inc.",
    Uuid16("fd66"): "Zebra Technologies Corporation",
    Uuid16("fd67"): "Montblanc Simplo GmbH",
    Uuid16("fd68"): "Ubique Innovation AG",
    Uuid16("fd69"): "Samsung Electronics Co., Ltd.",
    Uuid16("fd6a"): "Emerson",
    Uuid16("fd6b"): "rapitag GmbH",
    Uuid16("fd6c"): "Samsung Electronics Co., Ltd.",
    Uuid16("fd6d"): "Sigma Elektro GmbH",
    Uuid16("fd6e"): "Polidea sp. z o.o.",
    Uuid16("fd6f"): "Apple, Inc.",
    Uuid16("fd70"): "GuangDong Oppo Mobile Telecommunications Corp., Ltd.",
    Uuid16("fd71"): "GN Hearing A/S",
    Uuid16("fd72"): "Logitech International SA",
    Uuid16("fd73"): "BRControls Products BV",
    Uuid16("fd74"): "BRControls Products BV",
    Uuid16("fd75"): "Insulet Corporation",
    Uuid16("fd76"): "Insulet Corporation",
    Uuid16("fd77"): "Withings",
    Uuid16("fd78"): "Withings",
    Uuid16("fd79"): "Withings",
    Uuid16("fd7a"): "Withings",
    Uuid16("fd7b"): "WYZE LABS, INC.",
    Uuid16("fd7c"): "Toshiba Information Systems(Japan) Corporation",
    Uuid16("fd7d"): "Center for Advanced Research Wernher Von Braun",
    Uuid16("fd7e"): "Samsung Electronics Co., Ltd.",
    Uuid16("fd7f"): "Husqvarna AB",
    Uuid16("fd80"): "Phindex Technologies, Inc",
    Uuid16("fd81"): "CANDY HOUSE, Inc.",
    Uuid16("fd82"): "Sony Corporation",
    Uuid16("fd83"): "iNFORM Technology GmbH",
    Uuid16("fd84"): "Tile, Inc.",
    Uuid16("fd85"): "Husqvarna AB",
    Uuid16("fd86"): "Abbott",
    Uuid16("fd87"): "Google LLC",
    Uuid16("fd88"): "Urbanminded LTD",
    Uuid16("fd89"): "Urbanminded LTD",
    Uuid16("fd8a"): "Signify Netherlands B.V.",
    Uuid16("fd8b"): "Jigowatts Inc.",
    Uuid16("fd8c"): "Google LLC",
    Uuid16("fd8d"): "quip NYC Inc.",
    Uuid16("fd8e"): "Motorola Solutions",
    Uuid16("fd8f"): "Matrix ComSec Pvt. Ltd.",
    Uuid16("fd90"): "Guangzhou SuperSound Information Technology Co.,Ltd",
    Uuid16("fd91"): "Groove X, Inc.",
    Uuid16("fd92"): "Qualcomm Technologies International, Ltd. (QTIL)",
    Uuid16("fd93"): "Bayerische Motoren Werke AG",
    Uuid16("fd94"): "Hewlett Packard Enterprise",
    Uuid16("fd95"): "Rigado",
    Uuid16("fd96"): "Google LLC",
    Uuid16("fd97"): "June Life, Inc.",
    Uuid16("fd98"): "Disney Worldwide Services, Inc.",
    Uuid16("fd99"): "ABB Oy",
    Uuid16("fd9a"): "Huawei Technologies Co., Ltd.",
    Uuid16("fd9b"): "Huawei Technologies Co., Ltd.",
    Uuid16("fd9c"): "Huawei Technologies Co., Ltd.",
    Uuid16("fd9d"): "Gastec Corporation",
    Uuid16("fd9e"): "The Coca-Cola Company",
    Uuid16("fd9f"): "VitalTech Affiliates LLC",
    Uuid16("fda0"): "Secugen Corporation",
    Uuid16("fda1"): "Groove X, Inc",
    Uuid16("fda2"): "Groove X, Inc",
    Uuid16("fda3"): "Inseego Corp.",
    Uuid16("fda4"): "Inseego Corp.",
    Uuid16("fda5"): "Neurostim OAB, Inc.",
    Uuid16("fda6"): "WWZN Information Technology Company Limited",
    Uuid16("fda7"): "WWZN Information Technology Company Limited",
    Uuid16("fda8"): "PSA Peugeot Citroën",
    Uuid16("fda9"): "Rhombus Systems, Inc.",
    Uuid16("fdaa"): "Xiaomi Inc.",
    Uuid16("fdab"): "Xiaomi Inc.",
    Uuid16("fdac"): "Tentacle Sync GmbH",
    Uuid16("fdad"): "Houwa System Design, k.k.",
    Uuid16("fdae"): "Houwa System Design, k.k.",
    Uuid16("fdaf"): "Wiliot LTD",
    Uuid16("fdb0"): "Proxy Technologies, Inc.",
    Uuid16("fdb1"): "Proxy Technologies, Inc.",
    Uuid16("fdb2"): "Portable Multimedia Ltd",
    Uuid16("fdb3"): "Audiodo AB",
    Uuid16("fdb4"): "HP Inc",
    Uuid16("fdb5"): "ECSG",
    Uuid16("fdb6"): "GWA Hygiene GmbH",
    Uuid16("fdb7"): "LivaNova USA Inc.",
    Uuid16("fdb8"): "LivaNova USA Inc.",
    Uuid16("fdb9"): "Comcast Cable Corporation",
    Uuid16("fdba"): "Comcast Cable Corporation",
    Uuid16("fdbb"): "Profoto",
    Uuid16("fdbc"): "Emerson",
    Uuid16("fdbd"): "Clover Network, Inc.",
    Uuid16("fdbe"): "California Things Inc.",
    Uuid16("fdbf"): "California Things Inc.",
    Uuid16("fdc0"): "Hunter Douglas",
    Uuid16("fdc1"): "Hunter Douglas",
    Uuid16("fdc2"): "Baidu Online Network Technology (Beijing) Co., Ltd",
    Uuid16("fdc3"): "Baidu Online Network Technology (Beijing) Co., Ltd",
    Uuid16("fdc4"): "Simavita (Aust) Pty Ltd",
    Uuid16("fdc5"): "Automatic Labs",
    Uuid16("fdc6"): "Eli Lilly and Company",
    Uuid16("fdc7"): "Eli Lilly and Company",
    Uuid16("fdc8"): "Hach – Danaher",
    Uuid16("fdc9"): "Busch-Jaeger Elektro GmbH",
    Uuid16("fdca"): "Fortin Electronic Systems",
    Uuid16("fdcb"): "Meggitt SA",
    Uuid16("fdcc"): "Shoof Technologies",
    Uuid16("fdcd"): "Qingping Technology (Beijing) Co., Ltd.",
    Uuid16("fdce"): "SENNHEISER electronic GmbH & Co. KG",
    Uuid16("fdcf"): "Nalu Medical, Inc",
    Uuid16("fdd0"): "Huawei Technologies Co., Ltd",
    Uuid16("fdd1"): "Huawei Technologies Co., Ltd",
    Uuid16("fdd2"): "Bose Corporation",
    Uuid16("fdd3"): "FUBA Automotive Electronics GmbH",
    Uuid16("fdd4"): "LX Solutions Pty Limited",
    Uuid16("fdd5"): "Brompton Bicycle Ltd",
    Uuid16("fdd6"): "Ministry of Supply",
    Uuid16("fdd7"): "Emerson",
    Uuid16("fdd8"): "Jiangsu Teranovo Tech Co., Ltd.",
    Uuid16("fdd9"): "Jiangsu Teranovo Tech Co., Ltd.",
    Uuid16("fdda"): "MHCS",
    Uuid16("fddb"): "Samsung Electronics Co., Ltd.",
    Uuid16("fddc"): "4iiii Innovations Inc.",
    Uuid16("fddd"): "Arch Systems Inc",
    Uuid16("fdde"): "Noodle Technology Inc.",
    Uuid16("fddf"): "Harman International",
    Uuid16("fde0"): "John Deere",
    Uuid16("fde1"): "Fortin Electronic Systems",
    Uuid16("fde2"): "Google Inc.",
    Uuid16("fde3"): "Abbott Diabetes Care",
    Uuid16("fde4"): "JUUL Labs, Inc.",
    Uuid16("fde5"): "SMK Corporation",
    Uuid16("fde6"): "Intelletto Technologies Inc",
    Uuid16("fde7"): "SECOM Co., LTD",
    Uuid16("fde8"): "Robert Bosch GmbH",
    Uuid16("fde9"): "Spacesaver Corporation",
    Uuid16("fdea"): "SeeScan, Inc",
    Uuid16("fdeb"): "Syntronix Corporation",
    Uuid16("fdec"): "Mannkind Corporation",
    Uuid16("fded"): "Pole Star",
    Uuid16("fdee"): "Huawei Technologies Co., Ltd.",
    Uuid16("fdef"): "ART AND PROGRAM, INC.",
    Uuid16("fdf0"): "Google Inc.",
    Uuid16("fdf1"): "LAMPLIGHT Co.,Ltd",
    Uuid16("fdf2"): "AMICCOM Electronics Corporation",
    Uuid16("fdf3"): "Amersports",
    Uuid16("fdf4"): "O. E. M. Controls, Inc.",
    Uuid16("fdf5"): "Milwaukee Electric Tools",
    Uuid16("fdf6"): "AIAIAI ApS",
    Uuid16("fdf7"): "HP Inc.",
    Uuid16("fdf8"): "Onvocal",
    Uuid16("fdf9"): "INIA",
    Uuid16("fdfa"): "Tandem Diabetes Care",
    Uuid16("fdfb"): "Tandem Diabetes Care",
    Uuid16("fdfc"): "Optrel AG",
    Uuid16("fdfd"): "RecursiveSoft Inc.",
    Uuid16("fdfe"): "ADHERIUM(NZ) LIMITED",
    Uuid16("fdff"): "OSRAM GmbH",
    Uuid16("fe00"): "Amazon.com Services, Inc.",
    Uuid16("fe01"): "Duracell U.S. Operations Inc.",
    Uuid16("fe02"): "Robert Bosch GmbH",
    Uuid16("fe03"): "Amazon.com Services, Inc.",
    Uuid16("fe04"): "OpenPath Security Inc",
    Uuid16("fe05"): "CORE Transport Technologies NZ Limited",
    Uuid16("fe06"): "Qualcomm Technologies, Inc.",
    Uuid16("fe07"): "Sonos, Inc.",
    Uuid16("fe08"): "Microsoft",
    Uuid16("fe09"): "Pillsy, Inc.",
    Uuid16("fe0a"): "ruwido austria gmbh",
    Uuid16("fe0b"): "ruwido austria gmbh",
    Uuid16("fe0c"): "Procter & Gamble",
    Uuid16("fe0d"): "Procter & Gamble",
    Uuid16("fe0e"): "Setec Pty Ltd",
    Uuid16("fe0f"): "Signify Netherlands B.V. (formerly Philips Lighting B.V.)",
    Uuid16("fe10"): "Lapis Semiconductor Co., Ltd.",
    Uuid16("fe11"): "GMC-I Messtechnik GmbH",
    Uuid16("fe12"): "M-Way Solutions GmbH",
    Uuid16("fe13"): "Apple Inc.",
    Uuid16("fe14"): "Flextronics International USA Inc.",
    Uuid16("fe15"): "Amazon.com Services, Inc..",
    Uuid16("fe16"): "Footmarks, Inc.",
    Uuid16("fe17"): "Telit Wireless Solutions GmbH",
    Uuid16("fe18"): "Runtime, Inc.",
    Uuid16("fe19"): "Google, Inc",
    Uuid16("fe1a"): "Tyto Life LLC",
    Uuid16("fe1b"): "Tyto Life LLC",
    Uuid16("fe1c"): "NetMedia, Inc.",
    Uuid16("fe1d"): "Illuminati Instrument Corporation",
    Uuid16("fe1e"): "Smart Innovations Co., Ltd",
    Uuid16("fe1f"): "Garmin International, Inc.",
    Uuid16("fe20"): "Emerson",
    Uuid16("fe21"): "Bose Corporation",
    Uuid16("fe22"): "Zoll Medical Corporation",
    Uuid16("fe23"): "Zoll Medical Corporation",
    Uuid16("fe24"): "August Home Inc",
    Uuid16("fe25"): "Apple, Inc.",
    Uuid16("fe26"): "Google",
    Uuid16("fe27"): "Google",
    Uuid16("fe28"): "Ayla Networks",
    Uuid16("fe29"): "Gibson Innovations",
    Uuid16("fe2a"): "DaisyWorks, Inc.",
    Uuid16("fe2b"): "ITT Industries",
    Uuid16("fe2c"): "Google",
    Uuid16("fe2d"): "SMART INNOVATION Co.,Ltd",
    Uuid16("fe2e"): "ERi,Inc.",
    Uuid16("fe2f"): "CRESCO Wireless, Inc",
    Uuid16("fe30"): "Volkswagen AG",
    Uuid16("fe31"): "Volkswagen AG",
    Uuid16("fe32"): "Pro-Mark, Inc.",
    Uuid16("fe33"): "CHIPOLO d.o.o.",
    Uuid16("fe34"): "SmallLoop LLC",
    Uuid16("fe35"): "HUAWEI Technologies Co., Ltd",
    Uuid16("fe36"): "HUAWEI Technologies Co., Ltd",
    Uuid16("fe37"): "Spaceek LTD",
    Uuid16("fe38"): "Spaceek LTD",
    Uuid16("fe39"): "TTS Tooltechnic Systems AG & Co. KG",
    Uuid16("fe3a"): "TTS Tooltechnic Systems AG & Co. KG",
    Uuid16("fe3b"): "Dobly Laboratories",
    Uuid16("fe3c"): "alibaba",
    Uuid16("fe3d"): "BD Medical",
    Uuid16("fe3e"): "BD Medical",
    Uuid16("fe3f"): "Friday Labs Limited",
    Uuid16("fe40"): "Inugo Systems Limited",
    Uuid16("fe41"): "Inugo Systems Limited",
    Uuid16("fe42"): "Nets A/S",
    Uuid16("fe43"): "Andreas Stihl AG & Co. KG",
    Uuid16("fe44"): "SK Telecom",
    Uuid16("fe45"): "Snapchat Inc",
    Uuid16("fe46"): "B&O Play A/S",
    Uuid16("fe47"): "General Motors",
    Uuid16("fe48"): "General Motors",
    Uuid16("fe49"): "SenionLab AB",
    Uuid16("fe4a"): "OMRON HEALTHCARE Co., Ltd.",
    Uuid16("fe4b"): "Signify Netherlands B.V. (formerly Philips Lighting B.V.)",
    Uuid16("fe4c"): "Volkswagen AG",
    Uuid16("fe4d"): "Casambi Technologies Oy",
    Uuid16("fe4e"): "NTT docomo",
    Uuid16("fe4f"): "Molekule, Inc.",
    Uuid16("fe50"): "Google Inc.",
    Uuid16("fe51"): "SRAM",
    Uuid16("fe52"): "SetPoint Medical",
    Uuid16("fe53"): "3M",
    Uuid16("fe54"): "Motiv, Inc.",
    Uuid16("fe55"): "Google Inc.",
    Uuid16("fe56"): "Google Inc.",
    Uuid16("fe57"): "Dotted Labs",
    Uuid16("fe58"): "Nordic Semiconductor ASA",
    Uuid16("fe59"): "Nordic Semiconductor ASA",
    Uuid16("fe5a"): "Cronologics Corporation",
    Uuid16("fe5b"): "GT-tronics HK Ltd",
    Uuid16("fe5c"): "million hunters GmbH",
    Uuid16("fe5d"): "Grundfos A/S",
    Uuid16("fe5e"): "Plastc Corporation",
    Uuid16("fe5f"): "Eyefi, Inc.",
    Uuid16("fe60"): "Lierda Science & Technology Group Co., Ltd.",
    Uuid16("fe61"): "Logitech International SA",
    Uuid16("fe62"): "Indagem Tech LLC",
    Uuid16("fe63"): "Connected Yard, Inc.",
    Uuid16("fe64"): "Siemens AG",
    Uuid16("fe65"): "CHIPOLO d.o.o.",
    Uuid16("fe66"): "Intel Corporation",
    Uuid16("fe67"): "Lab Sensor Solutions",
    Uuid16("fe68"): "Capsule Technologies Inc.",
    Uuid16("fe69"): "Capsule Technologies Inc.",
    Uuid16("fe6a"): "Kontakt Micro-Location Sp. z o.o.",
    Uuid16("fe6b"): "TASER International, Inc.",
    Uuid16("fe6c"): "TASER International, Inc.",
    Uuid16("fe6d"): "The University of Tokyo",
    Uuid16("fe6e"): "The University of Tokyo",
    Uuid16("fe6f"): "LINE Corporation",
    Uuid16("fe70"): "Beijing Jingdong Century Trading Co., Ltd.",
    Uuid16("fe71"): "Plume Design Inc",
    Uuid16("fe72"): "Abbott (formerly St. Jude Medical, Inc.)",
    Uuid16("fe73"): "Abbott (formerly St. Jude Medical, Inc.)",
    Uuid16("fe74"): "unwire",
    Uuid16("fe75"): "TangoMe",
    Uuid16("fe76"): "TangoMe",
    Uuid16("fe77"): "Hewlett-Packard Company",
    Uuid16("fe78"): "Hewlett-Packard Company",
    Uuid16("fe79"): "Zebra Technologies",
    Uuid16("fe7a"): "Bragi GmbH",
    Uuid16("fe7b"): "Orion Labs, Inc.",
    Uuid16("fe7c"): "Telit Wireless Solutions (Formerly Stollmann E+V GmbH)",
    Uuid16("fe7d"): "Aterica Health Inc.",
    Uuid16("fe7e"): "Awear Solutions Ltd",
    Uuid16("fe7f"): "Doppler Lab",
    Uuid16("fe80"): "Doppler Lab",
    Uuid16("fe81"): "Medtronic Inc.",
    Uuid16("fe82"): "Medtronic Inc.",
    Uuid16("fe83"): "Blue Bite",
    Uuid16("fe84"): "RF Digital Corp",
    Uuid16("fe85"): "RF Digital Corp",
    Uuid16("fe86"): "HUAWEI Technologies Co., Ltd. ( 华为技术有限公司 )",
    Uuid16("fe87"): "Qingdao Yeelink Information Technology Co., Ltd. ( 青岛亿联客信息技术有限公司 )",
    Uuid16("fe88"): "SALTO SYSTEMS S.L.",
    Uuid16("fe89"): "B&O Play A/S",
    Uuid16("fe8a"): "Apple, Inc.",
    Uuid16("fe8b"): "Apple, Inc.",
    Uuid16("fe8c"): "TRON Forum",
    Uuid16("fe8d"): "Interaxon Inc.",
    Uuid16("fe8e"): "ARM Ltd",
    Uuid16("fe8f"): "CSR",
    Uuid16("fe90"): "JUMA",
    Uuid16("fe91"): "Shanghai Imilab Technology Co.,Ltd",
    Uuid16("fe92"): "Jarden Safety & Security",
    Uuid16("fe93"): "OttoQ In",
    Uuid16("fe94"): "OttoQ In",
    Uuid16("fe95"): "Xiaomi Inc.",
    Uuid16("fe96"): "Tesla Motors Inc.",
    Uuid16("fe97"): "Tesla Motors Inc.",
    Uuid16("fe98"): "Currant Inc",
    Uuid16("fe99"): "Currant Inc",
    Uuid16("fe9a"): "Estimote",
    Uuid16("fe9b"): "Samsara Networks, Inc",
    Uuid16("fe9c"): "GSI Laboratories, Inc.",
    Uuid16("fe9d"): "Mobiquity Networks Inc",
    Uuid16("fe9e"): "Dialog Semiconductor B.V.",
    Uuid16("fe9f"): "Google",
    Uuid16("fea0"): "Google",
    Uuid16("fea1"): "Intrepid Control Systems, Inc.",
    Uuid16("fea2"): "Intrepid Control Systems, Inc.",
    Uuid16("fea3"): "ITT Industries",
    Uuid16("fea4"): "Paxton Access Ltd",
    Uuid16("fea5"): "GoPro, Inc.",
    Uuid16("fea6"): "GoPro, Inc.",
    Uuid16("fea7"): "UTC Fire and Security",
    Uuid16("fea8"): "Savant Systems LLC",
    Uuid16("fea9"): "Savant Systems LLC",
    Uuid16("feaa"): "Google",
    Uuid16("feab"): "Nokia",
    Uuid16("feac"): "Nokia",
    Uuid16("fead"): "Nokia",
    Uuid16("feae"): "Nokia",
    Uuid16("feaf"): "Nest Labs Inc",
    Uuid16("feb0"): "Nest Labs Inc",
    Uuid16("feb1"): "Electronics Tomorrow Limited",
    Uuid16("feb2"): "Microsoft Corporation",
    Uuid16("feb3"): "Taobao",
    Uuid16("feb4"): "WiSilica Inc.",
    Uuid16("feb5"): "WiSilica Inc.",
    Uuid16("feb6"): "Vencer Co., Ltd",
    Uuid16("feb7"): "Facebook, Inc.",
    Uuid16("feb8"): "Facebook, Inc.",
    Uuid16("feb9"): "LG Electronics",
    Uuid16("feba"): "Tencent Holdings Limited",
    Uuid16("febb"): "adafruit industries",
    Uuid16("febc"): "Dexcom Inc",
    Uuid16("febd"): "Clover Network, Inc",
    Uuid16("febe"): "Bose Corporation",
    Uuid16("febf"): "Nod, Inc.",
    Uuid16("fec0"): "KDDI Corporation",
    Uuid16("fec1"): "KDDI Corporation",
    Uuid16("fec2"): "Blue Spark Technologies, Inc.",
    Uuid16("fec3"): "360fly, Inc.",
    Uuid16("fec4"): "PLUS Location Systems",
    Uuid16("fec5"): "Realtek Semiconductor Corp.",
    Uuid16("fec6"): "Kocomojo, LLC",
    Uuid16("fec7"): "Apple, Inc.",
    Uuid16("fec8"): "Apple, Inc.",
    Uuid16("fec9"): "Apple, Inc.",
    Uuid16("feca"): "Apple, Inc.",
    Uuid16("fecb"): "Apple, Inc.",
    Uuid16("fecc"): "Apple, Inc.",
    Uuid16("fecd"): "Apple, Inc.",
    Uuid16("fece"): "Apple, Inc.",
    Uuid16("fecf"): "Apple, Inc.",
    Uuid16("fed0"): "Apple, Inc.",
    Uuid16("fed1"): "Apple, Inc.",
    Uuid16("fed2"): "Apple, Inc.",
    Uuid16("fed3"): "Apple, Inc.",
    Uuid16("fed4"): "Apple, Inc.",
    Uuid16("fed5"): "Plantronics Inc.",
    Uuid16("fed6"): "Broadcom",
    Uuid16("fed7"): "Broadcom",
    Uuid16("fed8"): "Google",
    Uuid16("fed9"): "Pebble Technology Corporation",
    Uuid16("feda"): "ISSC Technologies Corp.",
    Uuid16("fedb"): "Perka, Inc.",
    Uuid16("fedc"): "Jawbone",
    Uuid16("fedd"): "Jawbone",
    Uuid16("fede"): "Coin, Inc.",
    Uuid16("fedf"): "Design SHIFT",
    Uuid16("fee0"): "Anhui Huami Information Technology Co., Ltd.",
    Uuid16("fee1"): "Anhui Huami Information Technology Co., Ltd.",
    Uuid16("fee2"): "Anki, Inc.",
    Uuid16("fee3"): "Anki, Inc.",
    Uuid16("fee4"): "Nordic Semiconductor ASA",
    Uuid16("fee5"): "Nordic Semiconductor ASA",
    Uuid16("fee6"): "Silvair, Inc.",
    Uuid16("fee7"): "Tencent Holdings Limited.",
    Uuid16("fee8"): "Quintic Corp.",
    Uuid16("fee9"): "Quintic Corp.",
    Uuid16("feea"): "Swirl Networks, Inc.",
    Uuid16("feeb"): "Swirl Networks, Inc.",
    Uuid16("feec"): "Tile, Inc.",
    Uuid16("feed"): "Tile, Inc.",
    Uuid16("feee"): "Polar Electro Oy",
    Uuid16("feef"): "Polar Electro Oy",
    Uuid16("fef0"): "Intel",
    Uuid16("fef1"): "CSR",
    Uuid16("fef2"): "CSR",
    Uuid16("fef3"): "Google",
    Uuid16("fef4"): "Google",
    Uuid16("fef5"): "Dialog Semiconductor GmbH",
    Uuid16("fef6"): "Wicentric, Inc.",
    Uuid16("fef7"): "Aplix Corporation",
    Uuid16("fef8"): "Aplix Corporation",
    Uuid16("fef9"): "PayPal, Inc.",
    Uuid16("fefa"): "PayPal, Inc.",
    Uuid16("fefb"): "Telit Wireless Solutions (Formerly Stollmann E+V GmbH)",
    Uuid16("fefc"): "Gimbal, Inc.",
    Uuid16("fefd"): "Gimbal, Inc.",
    Uuid16("fefe"): "GN ReSound A/S",
    Uuid16("feff"): "GN Netcom",
}
"""16-bit UUIDs assigned to companies by Bluetooth SIG"""

UUID_DESCRIPTION_MAP.update(company_assigned_uuid16s)
