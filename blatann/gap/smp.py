import logging
import threading
import enum

from blatann.gap import smp_crypto
from blatann.gap.bond_db import BondingData
from blatann.nrf import nrf_types, nrf_events
from blatann.exceptions import InvalidStateException, InvalidOperationException
from blatann.event_type import EventSource, Event
from blatann.waitables.event_waitable import EventWaitable
from blatann.event_args import *


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


class SecurityParameters(object):
    """
    Class representing the desired security parameters for a given connection
    """
    def __init__(self, passcode_pairing=False, io_capabilities=IoCapabilities.KEYBOARD_DISPLAY,
                 bond=False, out_of_band=False, reject_pairing_requests=False, lesc_pairing=False):
        self.passcode_pairing = passcode_pairing
        self.io_capabilities = io_capabilities
        self.bond = bond
        self.out_of_band = out_of_band
        self.reject_pairing_requests = reject_pairing_requests
        self.lesc_pairing = lesc_pairing


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
        self.peer = peer
        self.security_params = security_parameters
        self._pairing_in_process = False
        self._initiated_encryption = False
        self._is_previously_bonded_device = False
        self._on_authentication_complete_event = EventSource("On Authentication Complete", logger)
        self._on_passkey_display_event = EventSource("On Passkey Display", logger)
        self._on_passkey_entry_event = EventSource("On Passkey Entry", logger)
        self._on_security_level_changed_event = EventSource("Security Level Changed", logger)
        self.peer.on_connect.register(self._on_peer_connected)
        self._auth_key_resolve_thread = threading.Thread()
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
    def on_pairing_complete(self):
        """
        Event that is triggered when pairing completes with the peer
        EventArgs type: PairingCompleteEventArgs

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_authentication_complete_event

    @property
    def on_security_level_changed(self):
        """
        Event that is triggered when the security/encryption level changes. This can be triggered from
        a pairing sequence or if a bonded client starts the encryption handshaking using the stored LTKs.

        Note: This event is triggered before on_pairing_complete

        EventArgs type: SecurityLevelChangedEventArgs
        :return: an Event which can have handlers registered to and deregestestered from
        :rtype: Event
        """
        return self._on_security_level_changed_event

    @property
    def on_passkey_display_required(self):
        """
        Event that is triggered when a passkey needs to be displayed to the user
        EventArgs type: PasskeyDisplayEventArgs

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_passkey_display_event

    @property
    def on_passkey_required(self):
        """
        Event that is triggered when a passkey needs to be entered by the user
        EventArgs type: PasskeyEntryEventArgs

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_passkey_entry_event

    @property
    def is_previously_bonded(self):
        """
        Gets if the peer this security manager is for was bonded in a previous connection

        :return: True if previously bonded, False if not
        """
        return self._is_previously_bonded_device

    @property
    def security_level(self):
        """
        Gets the current security level of the connection

        :rtype: SecurityLevel
        """
        return self._security_level

    """
    Public Methods
    """

    def set_security_params(self, passcode_pairing, io_capabilities, bond, out_of_band, reject_pairing_requests=False,
                            lesc_pairing=False):
        """
        Sets the security parameters to use with the peer

        :param passcode_pairing: Flag indicating that passcode pairing is required
        :type passcode_pairing: bool
        :param io_capabilities: The input/output capabilities of this device
        :type io_capabilities: IoCapabilities
        :param bond: Flag indicating that long-term bonding should be performed
        :type bond: bool
        :param out_of_band: Flag indicating if out-of-band pairing is supported
        :type out_of_band: bool
        :param reject_pairing_requests: Flag indicating that all security requests by the peer should be rejected
        :type reject_pairing_requests: bool
        :param lesc_pairing: Flag indicating that LE Secure Pairing methods are supported
        """
        self.security_params = SecurityParameters(passcode_pairing, io_capabilities, bond, out_of_band,
                                                  reject_pairing_requests, lesc_pairing)

    def pair(self, force_repairing=False):
        """
        Starts the encrypting process with the peer. If the peer has already been bonded to,
        Starts the pairing process with the peer given the set security parameters
        and returns a Waitable which will fire when the pairing process completes, whether successful or not.
        Waitable returns two parameters: (Peer, PairingCompleteEventArgs)

        :return: A waitiable that will fire when pairing is complete
        :rtype: blatann.waitables.EventWaitable
        """
        if self._pairing_in_process or self._initiated_encryption:
            raise InvalidStateException("Security manager busy")
        if self.security_params.reject_pairing_requests:
            raise InvalidOperationException("Cannot initiate pairing while rejecting pairing requests")

        # if in the client role and don't want to force a re-pair, check for bonding data first
        if self.peer.is_peripheral and not force_repairing:
            bond_entry = self._find_db_entry(self.peer.peer_address)
            if bond_entry:
                logger.info("Re-establishing encryption with peer using LTKs")
                self.ble_device.ble_driver.ble_gap_encrypt(self.peer.conn_handle,
                                                           bond_entry.bonding_data.own_ltk.master_id,
                                                           bond_entry.bonding_data.own_ltk.enc_info)
                self._initiated_encryption = True

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

    """
    Private Methods
    """

    def _on_peer_connected(self, peer, event_args):
        # Reset the
        self._pairing_in_process = False
        self._initiated_encryption = False
        self._security_level = SecurityLevel.OPEN
        self.peer.driver_event_subscribe(self._on_security_params_request, nrf_events.GapEvtSecParamsRequest)
        self.peer.driver_event_subscribe(self._on_authentication_status, nrf_events.GapEvtAuthStatus)
        self.peer.driver_event_subscribe(self._on_conn_sec_status, nrf_events.GapEvtConnSecUpdate)
        self.peer.driver_event_subscribe(self._on_auth_key_request, nrf_events.GapEvtAuthKeyRequest)
        self.peer.driver_event_subscribe(self._on_passkey_display, nrf_events.GapEvtPasskeyDisplay)
        self.peer.driver_event_subscribe(self._on_security_info_request, nrf_events.GapEvtSecInfoRequest)
        self.peer.driver_event_subscribe(self._on_lesc_dhkey_request, nrf_events.GapEvtLescDhKeyRequest)
        # Search the bonding DB for this peer's info
        self.bond_db_entry = self._find_db_entry(self.peer.peer_address)
        if self.bond_db_entry:
            logger.info("Connected to previously bonded device {}".format(self.bond_db_entry.peer_addr))
            self._is_previously_bonded_device = True

    def _find_db_entry(self, peer_address):
        if peer_address.addr_type == nrf_types.BLEGapAddrTypes.random_private_non_resolvable:
            return None

        for r in self.ble_device.bond_db:
            if self.peer.is_client != r.peer_is_client:
                continue

            # If peer address is public or random static, check directly if they match (no IRK needed)
            if peer_address.addr_type in [nrf_types.BLEGapAddrTypes.random_static, nrf_types.BLEGapAddrTypes.public]:
                if r.peer_addr == peer_address:
                    return r
            elif smp_crypto.private_address_resolves(peer_address, r.bonding_data.peer_id.irk):
                logger.info("Resolved Peer ID to {}".format(r.peer_addr))
                return r

        return None

    def _get_security_params(self):
        keyset_own = nrf_types.BLEGapSecKeyDist(True, True, False, False)
        keyset_peer = nrf_types.BLEGapSecKeyDist(True, True, False, False)
        sec_params = nrf_types.BLEGapSecParams(self.security_params.bond, self.security_params.passcode_pairing,
                                               self.security_params.lesc_pairing, False,
                                               self.security_params.io_capabilities,
                                               self.security_params.out_of_band, 7, 16, keyset_own, keyset_peer)
        return sec_params

    def _on_security_params_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtSecParamsRequest
        """
        # Security parameters are only provided for clients
        sec_params = self._get_security_params() if self.peer.is_client else None

        if self.security_params.reject_pairing_requests:
            status = nrf_types.BLEGapSecStatus.pairing_not_supp
        else:
            status = nrf_types.BLEGapSecStatus.success

        self.ble_device.ble_driver.ble_gap_sec_params_reply(event.conn_handle, status, sec_params, self.keyset)

        if not self.security_params.reject_pairing_requests:
            self._pairing_in_process = True

    def _on_security_info_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtSecInfoRequest
        """
        found_record = None
        # Find the database entry based on the sec info given
        for r in self.ble_device.bond_db:
            # Check that roles match
            if r.peer_is_client != self.peer.is_client:
                continue
            own_mid = r.bonding_data.own_ltk.master_id
            peer_mid = r.bonding_data.peer_ltk.master_id
            if event.master_id.ediv == own_mid.ediv and event.master_id.rand == own_mid.rand:
                logger.info("Found matching record with own master ID for sec info request")
                found_record = r
                break
            if event.master_id.ediv == peer_mid.ediv and event.master_id.rand == peer_mid.rand:
                logger.info("Found matching record with peer master ID for sec info request")
                found_record = r
                break

        if not found_record:
            logger.info("Unable to find Bonding record for peer master id {}".format(event.master_id))
            self.ble_device.ble_driver.ble_gap_sec_info_reply(event.conn_handle)
        else:
            self.bond_db_entry = found_record
            ltk = found_record.bonding_data.own_ltk
            id_key = found_record.bonding_data.peer_id
            self.ble_device.ble_driver.ble_gap_sec_info_reply(event.conn_handle, ltk.enc_info, id_key, None)

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
            self._initiated_encryption = False
            if event.sec_level > 0 and event.sec_mode > 0:
                status = SecurityStatus.success
            else:
                # Peer failed to find/load the keys, return failure status code
                status = SecurityStatus.unspecified
            self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(status, self.security_level))

    def _on_authentication_status(self, driver, event):
        """
        :type event: nrf_events.GapEvtAuthStatus
        """
        self._pairing_in_process = False
        self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(event.auth_status,
                                                                                          self.security_level))
        # Save keys in the database if authenticated+bonded successfullly
        if event.auth_status == SecurityStatus.success and event.bonded:
            # Reload the keys from the C Memory space (were updated during the pairing process)
            self.keyset.reload()

            # If there wasn't a bond record initially, try again a second time using the new public peer address
            if not self.bond_db_entry:
                self.bond_db_entry = self._find_db_entry(self.keyset.peer_keys.id_key.peer_addr)

            # Still no bond DB entry, create a new one
            if not self.bond_db_entry:
                logger.info("New bonded device, creating a DB Entry")
                self.bond_db_entry = self.ble_device.bond_db.create()
                self.bond_db_entry.peer_is_client = self.peer.is_client
                self.bond_db_entry.peer_addr = self.keyset.peer_keys.id_key.peer_addr
                self.bond_db_entry.bonding_data = BondingData(self.keyset)
                self.ble_device.bond_db.add(self.bond_db_entry)
            else:  # update the bonding info
                logger.info("Updating bond key for peer {}".format(self.keyset.peer_keys.id_key.peer_addr))
                self.bond_db_entry.bonding_data = BondingData(self.keyset)

            # TODO: This doesn't belong here..
            self.ble_device.bond_db_loader.save(self.ble_device.bond_db)

    def _on_passkey_display(self, driver, event):
        """
        :type event: nrf_events.GapEvtPasskeyDisplay
        """
        def match_confirm(keys_match):
            if not self._pairing_in_process:
                return
            if keys_match:
                key_type = nrf_types.BLEGapAuthKeyType.PASSKEY
            else:
                key_type = nrf_types.BLEGapAuthKeyType.NONE

            self.ble_device.ble_driver.ble_gap_auth_key_reply(event.conn_handle, key_type, None)

        event_args = PasskeyDisplayEventArgs(event.passkey, event.match_request, match_confirm)
        if event.match_request:
            self._auth_key_resolve_thread = threading.Thread(name="{} Passkey Confirm".format(self.peer.conn_handle),
                                                             target=self._on_passkey_display_event.notify,
                                                             args=(self.peer, event_args))
            self._auth_key_resolve_thread.daemon = True
            self._auth_key_resolve_thread.start()
        else:
            self._on_passkey_display_event.notify(self.peer, event_args)

    def _on_auth_key_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtAuthKeyRequest
        """
        def resolve(passkey):
            if not self._pairing_in_process:
                return
            if isinstance(passkey, (long, int)):
                passkey = "{:06d}".format(passkey)
            elif isinstance(passkey, unicode):
                passkey = str(passkey)
            self.ble_device.ble_driver.ble_gap_auth_key_reply(self.peer.conn_handle, event.key_type, passkey)

        self._auth_key_resolve_thread = threading.Thread(name="{} Passkey Entry".format(self.peer.conn_handle),
                                                         target=self._on_passkey_entry_event.notify,
                                                         args=(self.peer, PasskeyEntryEventArgs(event.key_type, resolve)))
        self._auth_key_resolve_thread.daemon = True
        self._auth_key_resolve_thread.start()

    def _on_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src != nrf_types.BLEGapTimeoutSrc.security_req:
            return
        self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(SecurityStatus.timeout,
                                                                                          self.security_level))
