import logging
from typing import Optional

from blatann.bt_sig.assigned_numbers import Appearance
from blatann.peer import ConnectionParameters, Union
from blatann.nrf import nrf_types

logger = logging.getLogger(__name__)


class GenericAccessService:
    """
    Class which represents the Generic Access service within the local database
    """
    DEVICE_NAME_MAX_LENGTH = 31

    def __init__(self, ble_driver,
                 device_name=nrf_types.driver.BLE_GAP_DEVNAME_DEFAULT,
                 appearance=Appearance.unknown):
        """
        :type ble_driver: blatann.nrf.nrf_driver.NrfDriver
        :type device_name: str
        """
        self.ble_driver = ble_driver
        self._name = device_name
        self._appearance = appearance
        self._empty_conn_params = None
        self._preferred_conn_params: Optional[ConnectionParameters] = None

    @property
    def device_name(self) -> str:
        """
        The device name that is configured in the Generic Access service of the local GATT database

        :getter: Gets the current device name
        :setter: Sets the current device name. Length (after utf8 encoding) must be <= 31 bytes
        """
        return self._name

    @device_name.setter
    def device_name(self, name: str):
        name_bytes = name.encode("utf8")
        if len(name_bytes) > self.DEVICE_NAME_MAX_LENGTH:
            raise ValueError(f"Encoded device name must be <= {self.DEVICE_NAME_MAX_LENGTH} bytes")
        if self.ble_driver.is_open:
            self.ble_driver.ble_gap_device_name_set(name_bytes)
        self._name = name

    @property
    def appearance(self) -> Appearance:
        """
        The Appearance that is configured in the Generic Access service of the local GATT database

        :getter: Gets the device appearance
        :setter: Sets the device appearance
        """
        return self._appearance

    @appearance.setter
    def appearance(self, value: Union[Appearance, int]):
        if self.ble_driver.is_open:
            self.ble_driver.ble_gap_appearance_set(value)
        self._appearance = value

    @property
    def preferred_peripheral_connection_params(self) -> Optional[ConnectionParameters]:
        """
        The preferred peripheral connection parameters that are configured in the Generic Access service
        of the local GATT Database. If not configured, returns None.

        :getter: Gets the configured connection parameters or None if not configured
        :setter: Sets the configured connection parameters
        """
        return self._preferred_conn_params

    @preferred_peripheral_connection_params.setter
    def preferred_peripheral_connection_params(self, value: ConnectionParameters):
        if self.ble_driver.is_open:
            self.ble_driver.ble_gap_ppcp_set(value)
        self._preferred_conn_params = value

    def update(self):
        """
        **Not to be called by users**

        Used internally to configure the generic access in the case that values were set before
        the driver was opened and configured.
        """
        if not self.ble_driver.is_open:
            return
        name_bytes = self._name.encode("utf8")
        self.ble_driver.ble_gap_device_name_set(name_bytes)
        self.ble_driver.ble_gap_appearance_set(self._appearance)
        if self._preferred_conn_params:
            self.ble_driver.ble_gap_ppcp_set(self._preferred_conn_params)
