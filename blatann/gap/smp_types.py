from __future__ import annotations

import enum
from typing import Union

from blatann.nrf import nrf_types
from blatann.utils import repr_format

# Enum used to report IO Capabilities for the pairing process
IoCapabilities = nrf_types.BLEGapIoCaps

# Enum of the status codes emitted during security procedures
SecurityStatus = nrf_types.BLEGapSecStatus

# Enum of the different Pairing passkeys to be entered by the user (passcode, out-of-band, etc.)
AuthenticationKeyType = nrf_types.BLEGapAuthKeyType


class SecurityLevel(enum.Enum):
    """
    Security levels used for defining GATT server characteristics
    """
    NO_ACCESS = 0
    OPEN = 1
    JUST_WORKS = 2
    MITM = 3
    LESC_MITM = 4


# TODO: Figure out the best way to document enum values
class PairingPolicy(enum.IntFlag):
    allow_all = 0
    # allow_all.__doc__ = "Allows all pairing requests to be initiated"

    reject_new_pairing_requests = enum.auto()
    # reject_new_pairing_requests.__doc__ = "Rejects all pairing requests from non-bonded devices"

    reject_nonbonded_peripheral_requests = enum.auto()
    # reject_nonbonded_peripheral_requests.__doc__ = "Rejects peripheral-initiated security requests from non-bonded devices"

    reject_bonded_peripheral_requests = enum.auto()
    # reject_bonded_peripheral_requests.__doc__ = "Rejects peripheral-initiated security requests from bonded devices. " \
    #                                             "Used for cases where the central wants to control when security is enabled."

    reject_bonded_device_repairing_requests = enum.auto()
    # reject_bonded_device_repairing_requests.__doc__ = "Rejects re-pairing attempts from a central that is already bonded. " \
                                                      # "Requires explicit bond data deletion in order to pair again."

    # Composites
    reject_peripheral_requests = reject_bonded_peripheral_requests | reject_nonbonded_peripheral_requests
    # reject_peripheral_requests.__doc__ = "Rejects all peripheral-initiated security requests"

    reject_all_requests = reject_new_pairing_requests | reject_peripheral_requests | reject_bonded_device_repairing_requests
    # reject_all_requests.__doc__ = "Rejects all security requests, except from already-bonded central devices"

    @staticmethod
    def combine(*policies: PairingPolicy):
        policy = 0
        for p in policies:
            policy |= p
        return policy


class SecurityParameters:
    """
    Class representing the desired security parameters for a given connection
    """
    def __init__(self,
                 passcode_pairing=False,
                 io_capabilities=IoCapabilities.KEYBOARD_DISPLAY,
                 bond=False,
                 out_of_band=False,
                 reject_pairing_requests: Union[bool, PairingPolicy] = False,
                 lesc_pairing=False):
        self.passcode_pairing = passcode_pairing
        self.io_capabilities = io_capabilities
        self.bond = bond
        self.out_of_band = out_of_band
        self.lesc_pairing = lesc_pairing
        self.reject_pairing_requests = reject_pairing_requests
        if not isinstance(reject_pairing_requests, PairingPolicy):
            self.reject_pairing_requests = (PairingPolicy.reject_all_requests if reject_pairing_requests else
                                            PairingPolicy.allow_all)

    def __repr__(self):
        return repr_format(self, passcode_pairing=self.passcode_pairing, io=self.io_capabilities,
                           bond=self.bond, oob=self.out_of_band, lesc=self.lesc_pairing)
