from __future__ import annotations

from pc_ble_driver_py.exceptions import NordicSemiException

from blatann.nrf.nrf_types.config import *
from blatann.nrf.nrf_types.enums import *
from blatann.nrf.nrf_types.gap import *
from blatann.nrf.nrf_types.gatt import *
from blatann.nrf.nrf_types.generic import *
from blatann.nrf.nrf_types.smp import *

from blatann.nrf.nrf_types import (  # isort: skip
    config as _config,
    enums as _enums,
    gap as _gap,
    gatt as _gatt,
    generic as _generic,
    smp as _smp
)

__all__ = [  # noqa PLE0604 - *_mod.__all__ is rexporting the submodules
    "NordicSemiException",
    *_config.__all__,
    *_enums.__all__,
    *_gap.__all__,
    *_gatt.__all__,
    *_generic.__all__,
    *_smp.__all__,
]
