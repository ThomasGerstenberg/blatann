import enum
from blatann.nrf import nrf_events, nrf_types
from blatann.gap.smp import (SecurityStatus, IoCapabilities, AuthenticationKeyType,
                             SecurityParameters, PairingPolicy, SecurityLevel)
from blatann.gap.scanning import ScanParameters
from blatann.gap.advertising import AdvertisingData, AdvertisingFlags


HciStatus = nrf_types.BLEHci

"""
The default link-layer packet size used when a connection is established
"""
DLE_SIZE_DEFAULT = 27

"""
The minimum allowed link-layer packet size
"""
DLE_SIZE_MINIMUM = 27

"""
The maximum allowed link-layer packet size
"""
DLE_SIZE_MAXIMUM = 251
