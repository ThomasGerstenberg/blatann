from __future__ import annotations
import logging
import threading
import enum
import typing

from blatann.gap import smp_crypto
from blatann.gap.bond_db import BondingData
from blatann.gap.gap_types import PeerAddress
from blatann.nrf import nrf_types, nrf_events
from blatann.exceptions import InvalidStateException, InvalidOperationException
from blatann.event_type import EventSource, Event
from blatann.waitables.event_waitable import EventWaitable
from blatann.event_args import *

if typing.TYPE_CHECKING:
    from blatann.peer import Peer


logger = logging.getLogger(__name__)

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


class SecurityParameters(object):
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


class SecurityManager(object):
    """
    Handles performing security procedures with a connected peer
    """
    def __init__(self, ble_device, peer, security_parameters):
        """
        :type ble_device: blatann.BleDevice
        :type peer: blatann.peer.Peer
        :type security_parameters: SecurityParameters
        """
        self.ble_device = ble_device
        self.address: PeerAddress = None
        self.peer = peer
        self._security_params = security_parameters
        self._pairing_in_process = False
        self._initiated_encryption = False
        self._is_previously_bonded_device = False

        self._on_authentication_complete_event = EventSource("On Authentication Complete", logger)
        self._on_passkey_display_event = EventSource("On Passkey Display", logger)
        self._on_passkey_entry_event = EventSource("On Passkey Entry", logger)
        self._on_security_level_changed_event = EventSource("Security Level Changed", logger)
        self._on_peripheral_security_request_event = EventSource("Peripheral Security Request", logger)
        self._on_pairing_request_rejected_event = EventSource("Pairing Attempt Rejected", logger)
        self.peer.on_connect.register(self._on_peer_connected)
        self._auth_key_resolve_thread = threading.Thread(daemon=True)
        self._peripheral_security_request_thread = threading.Thread(daemon=True)
        self.keyset = nrf_types.BLEGapSecKeyset()
        self.bond_db_entry = None
        self._security_level = SecurityLevel.NO_ACCESS
        self._private_key = smp_crypto.lesc_generate_private_key()
        self._public_key = self._private_key.public_key()
        self.keyset.own_keys.public_key.key = smp_crypto.lesc_pubkey_to_raw(self._public_key)

    """
    Events
    """

    @property
    def on_pairing_complete(self) -> Event[Peer, PairingCompleteEventArgs]:
        """
        Event that is triggered when pairing completes with the peer

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_authentication_complete_event

    @property
    def on_security_level_changed(self) -> Event[Peer, SecurityLevelChangedEventArgs]:
        """
        Event that is triggered when the security/encryption level changes. This can be triggered from
        a pairing sequence or if a bonded client starts the encryption handshaking using the stored LTKs.

        Note: This event is triggered before on_pairing_complete

        :return: an Event which can have handlers registered to and deregestestered from
        """
        return self._on_security_level_changed_event

    @property
    def on_passkey_display_required(self) -> Event[Peer, PasskeyDisplayEventArgs]:
        """
        Event that is triggered when a passkey needs to be displayed to the user and depending on
        the pairing mode the user must confirm that keys match (PasskeyDisplayEventArgs.match_request == True).

        .. note:: If multiple handlers are registered to this event, the first handler which resolves the match
           confirmation will set the response. All others will be ignored.

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_passkey_display_event

    @property
    def on_passkey_required(self) -> Event[Peer, PasskeyEntryEventArgs]:
        """
        Event that is triggered when a passkey needs to be entered by the user

        .. note:: If multiple handlers are registered to this event, the first handler which resolves the passkey will
           set the value. All others will be ignored.

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_passkey_entry_event

    @property
    def on_peripheral_security_request(self) -> Event[Peer, PeripheralSecurityRequestEventArgs]:
        """
        Event that is triggered when the connected peripheral explicitly requests pairing/encryption
        to be enabled. The event provides the higher levels an opportunity to accept, reject,
        or force re-pair with the peripheral.

        If no handler is registered to this event, pairing requests will be accepted unless the reject_pairing_requests
        parameter is set.

        .. note:: If a handler is registered to this event, it **must** respond with one of the options (accept/reject/repair).

        .. note:: If multiple handlers are registered to this event, the first handler to respond is the response used.
           All other inputs will be ignored

        :return: Event that is triggered when the peripheral requests a secure connection
        """
        return self._on_peripheral_security_request_event

    @property
    def on_pairing_request_rejected(self) -> Event[Peer, PairingRejectedEventArgs]:
        """
        Event that's emitted when a pairing request is rejected locally, either due to the user
        event handler or due to the rejection policy set in the security parameters

        :return: Event that is triggered when a pairing request is rejected
        """
        return self._on_pairing_request_rejected_event

    """
    Properties
    """

    @property
    def is_previously_bonded(self) -> bool:
        """
        Gets if the peer this security manager is for was bonded in a previous connection

        :return: True if previously bonded, False if not
        """
        return self._is_previously_bonded_device

    @property
    def pairing_in_process(self) -> bool:
        """
        Gets whether or not pairing/encryption is currently in process
        """
        return self._pairing_in_process or self._initiated_encryption

    @property
    def security_level(self) -> SecurityLevel:
        """
        Gets the current security level of the connection
        """
        return self._security_level

    @property
    def security_params(self) -> SecurityParameters:
        """
        Gets the security parameters structure
        """
        return self._security_params

    @security_params.setter
    def security_params(self, params: SecurityParameters):
        """
        Sets the security parameters
        """
        self._security_params = params

    """
    Public Methods
    """

    def set_security_params(self, passcode_pairing: bool,
                            io_capabilities: IoCapabilities,
                            bond: bool,
                            out_of_band: bool,
                            reject_pairing_requests: Union[bool, PairingPolicy] = False,
                            lesc_pairing: bool = False):
        """
        Sets the security parameters to use with the peer

        :param passcode_pairing: Flag indicating that passcode pairing is required
        :param io_capabilities: The input/output capabilities of this device
        :param bond: Flag indicating that long-term bonding should be performed
        :param out_of_band: Flag indicating if out-of-band pairing is supported
        :param reject_pairing_requests: Flag indicating that all security requests by the peer should be rejected
        :param lesc_pairing: Flag indicating that LE Secure Pairing methods are supported
        """
        self._security_params = SecurityParameters(passcode_pairing, io_capabilities, bond, out_of_band,
                                                   reject_pairing_requests, lesc_pairing)

    def pair(self, force_repairing=False) -> EventWaitable[Peer, PairingCompleteEventArgs]:
        """
        Starts the pairing process with the peer with the set security parameters.

        If the peer is already bonded, initiates the encryption process unless force_repairing is set to True

        If the peer is a central and we are a local device, sends the peripheral security request to the central
        so they can start the pairing/encryption process

        :return: A waitable that will trigger when pairing is complete
        """
        if self.pairing_in_process:
            logger.warning("Attempted to pair while pairing/encryption already in progress. Returning waitable for when it finishes")
            return EventWaitable(self.on_pairing_complete)

        # if in the client role and don't want to force a re-pair, check for bonding data first
        if self.peer.is_peripheral and not force_repairing:
            bond_entry = self.ble_device.bond_db.find_entry(self.address, self.peer.peer_address, self.peer.is_client)
            if bond_entry:
                logger.info("Re-establishing encryption with peer using LTKs")
                # If bonding data was created using LESC use our own LTKs, otherwise use the peer's
                if bond_entry.bonding_data.own_ltk.enc_info.lesc:
                    ltk = bond_entry.bonding_data.own_ltk
                else:
                    ltk = bond_entry.bonding_data.peer_ltk

                self.ble_device.ble_driver.ble_gap_encrypt(self.peer.conn_handle, ltk.master_id, ltk.enc_info)
                self._initiated_encryption = True
                return EventWaitable(self.on_pairing_complete)

        sec_params = self._get_security_params()
        self.ble_device.ble_driver.ble_gap_authenticate(self.peer.conn_handle, sec_params)
        self._pairing_in_process = True
        return EventWaitable(self.on_pairing_complete)

    def use_debug_lesc_key(self):
        """
        Changes the security settings to use the debug public/private key-pair for future LESC pairing interactions.
        The key is defined in the Core Bluetooth Specification v4.2 Vol.3, Part H, Section 2.3.5.6.

        .. warning:: Using this key allows Bluetooth sniffers to be able to decode the encrypted traffic over the air
        """
        self._private_key = smp_crypto.LESC_DEBUG_PRIVATE_KEY
        self._public_key = smp_crypto.LESC_DEBUG_PUBLIC_KEY
        self.keyset.own_keys.public_key.key = smp_crypto.lesc_pubkey_to_raw(self._public_key)

    def delete_bonding_data(self):
        """
        Deletes the bonding data for the peer, if any.
        Cannot be called during pairing, will throw an InvalidOperationException
        """
        if self.pairing_in_process:
            raise InvalidOperationException("Cannot clear bonding data while pairing is in progress")
        if self.bond_db_entry:
            db_entry = self.bond_db_entry
            self.bond_db_entry = None
            self.ble_device.bond_db.delete(db_entry)
            self._is_previously_bonded_device = False
            # TODO: This doesn't belong here..
            self.ble_device.bond_db_loader.save(self.ble_device.bond_db)

    """
    Private Methods
    """

    @property
    def _pairing_policy(self) -> PairingPolicy:
        return self._security_params.reject_pairing_requests

    def _on_peer_connected(self, peer, event_args):
        # Reset the
        self._pairing_in_process = False
        self._initiated_encryption = False
        self._security_level = SecurityLevel.OPEN
        self.address = self.ble_device.address
        self.keyset = nrf_types.BLEGapSecKeyset()
        self.keyset.own_keys.public_key.key = smp_crypto.lesc_pubkey_to_raw(self._public_key)

        self.peer.driver_event_subscribe(self._on_security_params_request, nrf_events.GapEvtSecParamsRequest)
        self.peer.driver_event_subscribe(self._on_authentication_status, nrf_events.GapEvtAuthStatus)
        self.peer.driver_event_subscribe(self._on_conn_sec_status, nrf_events.GapEvtConnSecUpdate)
        self.peer.driver_event_subscribe(self._on_auth_key_request, nrf_events.GapEvtAuthKeyRequest)
        self.peer.driver_event_subscribe(self._on_passkey_display, nrf_events.GapEvtPasskeyDisplay)
        self.peer.driver_event_subscribe(self._on_security_info_request, nrf_events.GapEvtSecInfoRequest)
        self.peer.driver_event_subscribe(self._on_lesc_dhkey_request, nrf_events.GapEvtLescDhKeyRequest)
        self.peer.driver_event_subscribe(self._on_security_request, nrf_events.GapEvtSecRequest)

        # Search the bonding DB for this peer's info
        self.bond_db_entry = self.ble_device.bond_db.find_entry(self.address,
                                                                self.peer.peer_address,
                                                                self.peer.is_client)
        if self.bond_db_entry:
            logger.info("Connected to previously bonded device {}".format(self.bond_db_entry.peer_addr))
            self._is_previously_bonded_device = True
        else:
            self._is_previously_bonded_device = False

    def _get_security_params(self):
        keyset_own = nrf_types.BLEGapSecKeyDist(True, True, False, False)
        keyset_peer = nrf_types.BLEGapSecKeyDist(True, True, False, False)
        sec_params = nrf_types.BLEGapSecParams(self._security_params.bond, self._security_params.passcode_pairing,
                                               self._security_params.lesc_pairing, False,
                                               self._security_params.io_capabilities,
                                               self._security_params.out_of_band, 7, 16, keyset_own, keyset_peer)
        return sec_params

    def _on_security_params_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtSecParamsRequest
        """
        # Security parameters are only provided for clients
        sec_params = self._get_security_params() if self.peer.is_client else None
        rejection_reason = None

        # Check if the pairing request should be rejected
        if self.peer.is_client:
            if self.is_previously_bonded and PairingPolicy.reject_bonded_device_repairing_requests in self._pairing_policy:
                rejection_reason = PairingRejectedReason.bonded_device_repairing
            elif PairingPolicy.reject_new_pairing_requests in self._pairing_policy:
                rejection_reason = PairingRejectedReason.non_bonded_central_request

        if not rejection_reason:
            status = nrf_types.BLEGapSecStatus.success
            self.ble_device.ble_driver.ble_gap_sec_params_reply(event.conn_handle, nrf_types.BLEGapSecStatus.success, sec_params, self.keyset)
            self._pairing_in_process = True
        else:
            self.ble_device.ble_driver.ble_gap_sec_params_reply(event.conn_handle, nrf_types.BLEGapSecStatus.pairing_not_supp, sec_params, self.keyset)
            self._on_pairing_request_rejected_event.notify(self.peer, PairingRejectedEventArgs(rejection_reason))

    def _on_security_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtSecRequest
        """
        if self._on_peripheral_security_request_event.has_handlers:
            request_handled = threading.Event()

            def handle_request(mode=PeripheralSecurityRequestEventArgs.Response.accept):
                if request_handled.is_set():
                    return
                if mode == PeripheralSecurityRequestEventArgs.Response.reject:
                    self.ble_device.ble_driver.ble_gap_authenticate(event.conn_handle, None)
                    args = PairingRejectedEventArgs(PairingRejectedReason.user_rejected)
                    self._on_pairing_request_rejected_event.notify(self.peer, args)
                else:
                    force_repair = mode == PeripheralSecurityRequestEventArgs.Response.force_repair
                    self.pair(force_repair)
                request_handled.set()

            event_args = PeripheralSecurityRequestEventArgs(event.bond, event.mitm, event.lesc,
                                                            event.keypress, self.is_previously_bonded,
                                                            handle_request)
            self._peripheral_security_request_thread = threading.Thread(
                name=f"{self.peer.conn_handle} Security Request",
                target=self._on_peripheral_security_request_event.notify,
                args=(self.peer, event_args),
                daemon=True)
            self._peripheral_security_request_thread.start()
            return

        # No handler specified, use pairing policy to reject if needed
        rejection_reason = None
        if self.is_previously_bonded:
            if PairingPolicy.reject_bonded_peripheral_requests in self._pairing_policy:
                rejection_reason = PairingRejectedReason.bonded_peripheral_request
        else:
            policy_checks = [PairingPolicy.reject_nonbonded_peripheral_requests,
                             PairingPolicy.reject_new_pairing_requests]
            if any(p in self._pairing_policy for p in policy_checks):
                rejection_reason = PairingRejectedReason.non_bonded_peripheral_request

        if rejection_reason:
            self.ble_device.ble_driver.ble_gap_authenticate(event.conn_handle, None)
            self._on_pairing_request_rejected_event.notify(self.peer, PairingRejectedEventArgs(rejection_reason))
        else:
            self.pair()
        return

    def _on_security_info_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtSecInfoRequest
        """
        # If bond entry wasn't found on connect, try another time now just in case
        if not self.bond_db_entry:
            self.bond_db_entry = self.ble_device.bond_db.find_entry(self.address,
                                                                    self.peer.peer_address,
                                                                    self.peer.is_client,
                                                                    event.master_id)

        if self.bond_db_entry:
            self._initiated_encryption = True
            ltk = self.bond_db_entry.bonding_data.own_ltk
            id_key = self.bond_db_entry.bonding_data.peer_id
            self.ble_device.ble_driver.ble_gap_sec_info_reply(event.conn_handle, ltk.enc_info, id_key, None)
        else:
            logger.info("Unable to find Bonding record for peer master id {}".format(event.master_id))
            self.ble_device.ble_driver.ble_gap_sec_info_reply(event.conn_handle)

    def _on_lesc_dhkey_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtLescDhKeyRequest
        """
        peer_public_key = smp_crypto.lesc_pubkey_from_raw(event.remote_public_key.key)
        dh_key = smp_crypto.lesc_compute_dh_key(self._private_key, peer_public_key, little_endian=True)
        self.ble_device.ble_driver.ble_gap_lesc_dhkey_reply(event.conn_handle, nrf_types.BLEGapDhKey(dh_key))

    def _on_conn_sec_status(self, driver, event):
        """
        :type event: nrf_events.GapEvtConnSecUpdate
        """
        self._security_level = SecurityLevel(event.sec_level)
        self._on_security_level_changed_event.notify(self.peer, SecurityLevelChangedEventArgs(self._security_level))
        if self._initiated_encryption:
            # Re-established using existing keys, notify auth complete event
            self._initiated_encryption = False
            if event.sec_level > 0 and event.sec_mode > 0:
                status = SecurityStatus.success
            else:
                logger.warning("Peer failed to load bonding data, deleting bond entry from database")
                # Peer failed to find/load the keys, return failure status code and remove key from database
                self.delete_bonding_data()
                status = SecurityStatus.unspecified
            self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(status, self.security_level, SecurityProcess.ENCRYPTION))

    def _on_authentication_status(self, driver, event):
        """
        :type event: nrf_events.GapEvtAuthStatus
        """
        self._pairing_in_process = False
        security_process = SecurityProcess.BONDING if event.bonded else SecurityProcess.PAIRING
        self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(event.auth_status,
                                                                                          self.security_level,
                                                                                          security_process))
        # Save keys in the database if authenticated+bonded successfully
        if event.auth_status == SecurityStatus.success and event.bonded:
            # Reload the keys from the C Memory space (were updated during the pairing process)
            self.keyset.reload()

            # If there wasn't a bond record initially, try again a second time using the new public peer address
            if not self.bond_db_entry:
                self.bond_db_entry = self.ble_device.bond_db.find_entry(self.address,
                                                                        self.keyset.peer_keys.id_key.peer_addr,
                                                                        self.peer.is_client)

            # Still no bond DB entry, create a new one
            if not self.bond_db_entry:
                logger.info("New bonded device, creating a DB Entry")
                self.bond_db_entry = self.ble_device.bond_db.create()
                self.bond_db_entry.own_addr = self.address
                self.bond_db_entry.peer_is_client = self.peer.is_client
                self.bond_db_entry.peer_addr = self.keyset.peer_keys.id_key.peer_addr
                self.bond_db_entry.bonding_data = BondingData.from_keyset(self.keyset)
                self.bond_db_entry.name = self.peer.name
                self.ble_device.bond_db.add(self.bond_db_entry)
            else:  # update the bonding info
                logger.info("Updating bond key for peer {}".format(self.keyset.peer_keys.id_key.peer_addr))
                self.bond_db_entry.bonding_data = BondingData.from_keyset(self.keyset)

            # TODO: This doesn't belong here..
            self.ble_device.bond_db_loader.save(self.ble_device.bond_db)

    def _on_passkey_display(self, driver, event):
        """
        :type event: nrf_events.GapEvtPasskeyDisplay
        """
        match_confirmed = threading.Event()

        def match_confirm(keys_match):
            if not self._pairing_in_process or match_confirmed.is_set():
                return
            if keys_match:
                key_type = nrf_types.BLEGapAuthKeyType.PASSKEY
            else:
                key_type = nrf_types.BLEGapAuthKeyType.NONE

            self.ble_device.ble_driver.ble_gap_auth_key_reply(event.conn_handle, key_type, None)
            match_confirmed.set()

        event_args = PasskeyDisplayEventArgs(event.passkey, event.match_request, match_confirm)
        if event.match_request:
            self._auth_key_resolve_thread = threading.Thread(name="{} Passkey Confirm".format(self.peer.conn_handle),
                                                             target=self._on_passkey_display_event.notify,
                                                             args=(self.peer, event_args),
                                                             daemon=True)
            self._auth_key_resolve_thread.daemon = True
            self._auth_key_resolve_thread.start()
        else:
            self._on_passkey_display_event.notify(self.peer, event_args)

    def _on_auth_key_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtAuthKeyRequest
        """
        passkey_entered = threading.Event()

        def resolve(passkey):
            if not self._pairing_in_process or passkey_entered.is_set():
                return
            if isinstance(passkey, int):
                passkey = "{:06d}".format(passkey).encode("ascii")
            elif isinstance(passkey, str):
                passkey = passkey.encode("ascii")
            self.ble_device.ble_driver.ble_gap_auth_key_reply(self.peer.conn_handle, event.key_type, passkey)
            passkey_entered.set()

        self._auth_key_resolve_thread = threading.Thread(name="{} Passkey Entry".format(self.peer.conn_handle),
                                                         target=self._on_passkey_entry_event.notify,
                                                         args=(self.peer, PasskeyEntryEventArgs(event.key_type, resolve)),
                                                         daemon=True)
        self._auth_key_resolve_thread.start()

    def _on_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src != nrf_types.BLEGapTimeoutSrc.security_req:
            return
        self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(SecurityStatus.timeout,
                                                                                          self.security_level))
