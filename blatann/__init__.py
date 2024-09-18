from __future__ import annotations

from pc_ble_driver_py import config

config.__conn_ic_id__ = "NRF52"

__version__ = "0.6.0"

from blatann.device import BleDevice  # noqa: E402
