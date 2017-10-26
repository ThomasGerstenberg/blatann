import logging
import threading
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


class SecurityParameters(object):
    """
    Class representing the desired security parameters for a given connection
    """
    def __init__(self, passcode_pairing=False, io_capabilities=IoCapabilities.KEYBOARD_DISPLAY,
                 bond=False, out_of_band=False, reject_pairing_requests=False):
        self.passcode_pairing = passcode_pairing
        self.io_capabilities = io_capabilities
        self.bond = bond
        self.out_of_band = out_of_band
        self.reject_pairing_requests = reject_pairing_requests


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
        self._busy = False
        self._on_authentication_complete_event = EventSource("On Authentication Complete", logger)
        self._on_passkey_display_event = EventSource("On Passkey Display", logger)
        self._on_passkey_entry_event = EventSource("On Passkey Entry", logger)
        self.peer.on_connect.register(self._on_peer_connected)
        self._auth_key_resolve_thread = threading.Thread()

    """
    Events
    """

    @property
    def on_pairing_complete(self):
        """
        Event that is triggered when pairing completes with the peer
        EventArgs type: PairingCompleteEventArgs

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_authentication_complete_event

    @property
    def on_passkey_display_required(self):
        """
        Event that is triggered when a passkey needs to be displayed to the user
        EventArgs type: PasskeyDisplayEventArgs

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_passkey_display_event

    @property
    def on_passkey_required(self):
        """
        Event that is triggered when a passkey needs to be entered by the user
        EventArgs type: PasskeyEntryEventArgs

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_passkey_entry_event

    """
    Public Methods
    """

    def set_security_params(self, passcode_pairing, io_capabilities, bond, out_of_band, reject_pairing_requests=False):
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
        """
        self.security_params = SecurityParameters(passcode_pairing, io_capabilities, bond, out_of_band,
                                                  reject_pairing_requests)

    def pair(self):
        """
        Starts the pairing process with the peer given the set security parameters
        and returns a Waitable which will fire when the pairing process completes, whether successful or not.
        Waitable returns two parameters: (Peer, PairingCompleteEventArgs)

        :return: A waitiable that will fire when pairing is complete
        :rtype: blatann.waitables.EventWaitable
        """
        if self._busy:
            raise InvalidStateException("Security manager busy")
        if self.security_params.reject_pairing_requests:
            raise InvalidOperationException("Cannot initiate pairing while rejecting pairing requests")

        sec_params = self._get_security_params()
        self.ble_device.ble_driver.ble_gap_authenticate(self.peer.conn_handle, sec_params)
        self._busy = True
        return EventWaitable(self.on_pairing_complete)

    """
    Private Methods
    """

    def _on_peer_connected(self, peer, event_args):
        self._busy = False
        self.peer.driver_event_subscribe(self._on_security_params_request, nrf_events.GapEvtSecParamsRequest)
        self.peer.driver_event_subscribe(self._on_authentication_status, nrf_events.GapEvtAuthStatus)
        self.peer.driver_event_subscribe(self._on_auth_key_request, nrf_events.GapEvtAuthKeyRequest)
        self.peer.driver_event_subscribe(self._on_passkey_display, nrf_events.GapEvtPasskeyDisplay)

    def _get_security_params(self):
        keyset_own = nrf_types.BLEGapSecKeyDist()
        keyset_peer = nrf_types.BLEGapSecKeyDist()
        sec_params = nrf_types.BLEGapSecParams(self.security_params.bond, self.security_params.passcode_pairing,
                                               False, False, self.security_params.io_capabilities,
                                               self.security_params.out_of_band, 7, 16, keyset_own, keyset_peer)
        return sec_params

    def _on_security_params_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtSecParamsRequest
        """
        # Security parameters are only provided for clients
        sec_params = self._get_security_params() if self.peer.is_client else None
        keyset = nrf_types.BLEGapSecKeyset()

        if self.security_params.reject_pairing_requests:
            status = nrf_types.BLEGapSecStatus.pairing_not_supp
        else:
            status = nrf_types.BLEGapSecStatus.success

        self.ble_device.ble_driver.ble_gap_sec_params_reply(event.conn_handle, status, sec_params, keyset)

        if not self.security_params.reject_pairing_requests:
            self._busy = True

    def _on_security_request(self, driver, event):
        # TODO: Event not implemented
        pass

    def _on_authentication_status(self, driver, event):
        """
        :type event: nrf_events.GapEvtAuthStatus
        """
        self._busy = False
        self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(event.auth_status))

    def _on_passkey_display(self, driver, event):
        """
        :type event: nrf_events.GapEvtPasskeyDisplay
        """
        # TODO: Better way to handle match request
        self._on_passkey_display_event.notify(self.peer, PasskeyDisplayEventArgs(event.passkey, event.match_request))

    def _on_auth_key_request(self, driver, event):
        """
        :type event: nrf_events.GapEvtAuthKeyRequest
        """
        def resolve(passkey):
            if not self._busy:
                return
            if isinstance(passkey, (long, int)):
                passkey = "{:06d}".format(passkey)
            elif isinstance(passkey, unicode):
                passkey = str(passkey)
            self.ble_device.ble_driver.ble_gap_auth_key_reply(self.peer.conn_handle, event.key_type, passkey)

        self._auth_key_resolve_thread = threading.Thread(name="{} Passkey Entry".format(self.peer.conn_handle),
                                                         target=self._on_passkey_entry_event.notify,
                                                         args=(self.peer, PasskeyEntryEventArgs(event.key_type, resolve)))
        self._auth_key_resolve_thread.start()

    def _on_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src != nrf_types.BLEGapTimeoutSrc.security_req:
            return
        self._on_authentication_complete_event.notify(self.peer, PairingCompleteEventArgs(SecurityStatus.timeout))
