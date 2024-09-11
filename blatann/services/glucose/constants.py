from __future__ import annotations

from blatann.bt_sig.uuids import CharacteristicUuid, ServiceUuid

GLUCOSE_SERVICE_UUID = ServiceUuid.glucose

MEASUREMENT_CHARACTERISTIC_UUID = CharacteristicUuid.glucose_measurement
MEASUREMENT_CONTEXT_CHARACTERISTIC_UUID = CharacteristicUuid.glucose_measurement_context
FEATURE_CHARACTERISTIC_UUID = CharacteristicUuid.glucose_feature
RACP_CHARACTERISTIC_UUID = CharacteristicUuid.record_access_control_point
