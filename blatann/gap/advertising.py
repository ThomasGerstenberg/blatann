from __future__ import annotations
import logging
from blatann.nrf import nrf_events, nrf_types
from blatann import exceptions
from blatann.waitables.connection_waitable import ClientConnectionWaitable
from blatann.event_type import Event, EventSource
from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags


logger = logging.getLogger(__name__)


AdvertisingMode = nrf_types.BLEGapAdvType

MIN_ADVERTISING_INTERVAL_MS = nrf_types.adv_interval_range.min
MAX_ADVERTISING_INTERVAL_MS = nrf_types.adv_interval_range.max


class Advertiser(object):
    """
    Class which manages the advertising state of the BLE Device
    """
    # Constant used to indicate that the BLE device should advertise indefinitely, until
    # connected to or stopped manually
    ADVERTISE_FOREVER = 0
    """Special value used to indicate that the BLE device should advertise indefinitely 
       until either a central is connected or stopped manually."""

    def __init__(self, ble_device, client, conn_tag=0):
        """
        :type ble_device: blatann.device.BleDevice
        :type client: blatann.peer.Client
        """
        self.ble_device = ble_device
        self._is_advertising = False
        self._auto_restart = False
        self.client = client
        self.ble_device.ble_driver.event_subscribe(self._handle_adv_timeout, nrf_events.GapEvtTimeout)
        self.client.on_disconnect.register(self._handle_disconnect)
        self.client.on_connect.register(self._handle_connect)
        self._on_advertising_timeout = EventSource("Advertising Timeout", logger)
        self._advertise_interval = 100
        self._timeout = self.ADVERTISE_FOREVER
        self._advertise_mode = AdvertisingMode.connectable_undirected
        self._conn_tag = conn_tag
        self._channel_disable_mask = [False, False, False]

    @property
    def on_advertising_timeout(self) -> Event[Advertiser, None]:
        """
        Event generated whenever advertising times out and finishes with no connections made

        .. note:: If auto-restart advertising is enabled, this will trigger on each advertising timeout configured

        :return: an Event which can have handlers registered to and deregistered from
        """
        return self._on_advertising_timeout

    @property
    def is_advertising(self) -> bool:
        """
        **Read Only**

        Current state of advertising
        """
        return self._is_advertising

    @property
    def min_interval_ms(self) -> float:
        """
        **Read Only**

        The minimum allowed advertising interval, in millseconds.
        This is defined by the Bluetooth specification.
        """
        return MIN_ADVERTISING_INTERVAL_MS

    @property
    def max_interval_ms(self) -> float:
        """
        **Read Only**

        The maximum allowed advertising interval, in milliseconds.
        This is defined by the Bluetooth specification.
        """
        return MAX_ADVERTISING_INTERVAL_MS

    @property
    def auto_restart(self) -> bool:
        """
        Enables/disables whether or not the device should automatically restart
        advertising when an advertising timeout occurs or the client is disconnected.

        .. note:: Auto-restart is disabled automatically when :meth:`stop` is called

        :getter: Gets the auto-restart flag
        :setter: Sets/clears the auto-restart flag
        """
        return self._auto_restart

    @auto_restart.setter
    def auto_restart(self, value: bool):
        self._auto_restart = bool(value)

    def set_channel_mask(self, ch37_enabled=True, ch38_enabled=True, ch39_enabled=True):
        """
        Enables/disables which channels advertising packets are sent out on.
        By default, all 3 channels (37, 38, 39) are enabled.
        At least one of the 3 channels MUST be enabled, otherwise a ValueError exception will be raised.

        This mask will take effect the next time advertising is started or restarted due to timeout/disconnect.

        :param ch37_enabled: True to enable advertising on channel 37, False to disable
        :param ch38_enabled: True to enable advertising on channel 38, False to disable
        :param ch39_enabled: True to enable advertising on channel 39, False to disable
        """
        if not any([ch37_enabled, ch38_enabled, ch39_enabled]):
            raise ValueError("At least one advertising channel must be enabled")
        # nRF API has the mask inverted, but didn't make sense to have this API inverted also
        self._channel_disable_mask = [not ch37_enabled, not ch38_enabled, not ch39_enabled]

    def set_advertise_data(self,
                           advertise_data: AdvertisingData = AdvertisingData(),
                           scan_response: AdvertisingData = AdvertisingData()):
        """
        Sets the advertising and scan response data which will be broadcasted to peers during advertising

        .. note:: BLE Restricts advertise and scan response data to an encoded length of 31 bytes each.
           Use :meth:`AdvertisingData.check_encoded_length() <blatann.gap.advertise_data.AdvertiseData.check_encoded_length>`
           to determine if the payload is too large

        :param advertise_data: The advertising data to use
        :param scan_response: The scan response data to use.
                              This data is only sent when a scanning device requests the scan response packet (active scanning)
        :raises: InvalidOperationException if one of the payloads is too large
        """
        adv_len, adv_pass = advertise_data.check_encoded_length()
        scan_len, scan_pass = scan_response.check_encoded_length()

        if not adv_pass:
            raise exceptions.InvalidOperationException("Encoded Advertising data length is too long ({} bytes). "
                                                       "Max: {} bytes".format(adv_len, advertise_data.MAX_ENCODED_LENGTH))

        if not scan_pass:
            raise exceptions.InvalidOperationException("Encoded Scan Response data length is too long ({} bytes). "
                                                       "Max: {} bytes".format(scan_len, advertise_data.MAX_ENCODED_LENGTH))

        self.ble_device.ble_driver.ble_gap_adv_data_set(advertise_data.to_ble_adv_data(), scan_response.to_ble_adv_data())

    def set_default_advertise_params(self,
                                     advertise_interval_ms: float,
                                     timeout_seconds: int,
                                     advertise_mode: AdvertisingMode = AdvertisingMode.connectable_undirected):
        """
        Sets the default advertising parameters so they do not need to be specified on each start

        :param advertise_interval_ms: The advertising interval, in milliseconds.
                                      Should be a multiple of 0.625ms, otherwise it'll be rounded down to the nearest 0.625ms
        :param timeout_seconds: How long to advertise for before timing out, in seconds. For no timeout, use ADVERTISE_FOREVER (0)
        :param advertise_mode: The mode the advertiser should use
        """
        nrf_types.adv_interval_range.validate(advertise_interval_ms)
        self._advertise_interval = advertise_interval_ms
        self._timeout = timeout_seconds
        self._advertise_mode = advertise_mode

    def start(self,
              adv_interval_ms: float = None,
              timeout_sec: int = None,
              auto_restart: bool = None,
              advertise_mode: AdvertisingMode = None):
        """
        Starts advertising with the given parameters. If none given, will use the default set through :meth:`set_default_advertise_params`

        :param adv_interval_ms: The interval at which to send out advertise packets, in milliseconds.
                                Should be a multiple of 0.625ms, otherwise it'll be round down to the nearest 0.625ms
        :param timeout_sec: The duration which to advertise for. For no timeout, use ADVERTISE_FOREVER (0)
        :param auto_restart: Flag indicating that advertising should restart automatically when the timeout expires, or
                             when the client disconnects
        :param advertise_mode: The mode the advertiser should use
        :return: A waitable that will expire either when the timeout occurs or a client connects.
                 The waitable will return either ``None`` on timeout or :class:`~blatann.peer.Client` on successful connection
        :rtype: ClientConnectionWaitable
        """
        if self._is_advertising:
            self._stop()
        if adv_interval_ms is None:
            adv_interval_ms = self._advertise_interval
        else:
            nrf_types.adv_interval_range.validate(adv_interval_ms)
        if timeout_sec is None:
            timeout_sec = self._timeout
        if advertise_mode is None:
            advertise_mode = self._advertise_mode
        if auto_restart is None:
            auto_restart = self._auto_restart

        self._timeout = timeout_sec
        self._advertise_interval = adv_interval_ms
        self._advertise_mode = advertise_mode
        self._auto_restart = auto_restart

        self._start()

        return ClientConnectionWaitable(self.ble_device, self.client)

    def _start(self):
        params = nrf_types.BLEGapAdvParams(self._advertise_interval, self._timeout,
                                           self._advertise_mode, self._channel_disable_mask)
        logger.info("Starting advertising, params: {}, auto-restart: {}".format(params, self._auto_restart))
        self.ble_device.ble_driver.ble_gap_adv_start(params, self._conn_tag)
        self._is_advertising = True

    def stop(self):
        """
        Stops advertising and disables the auto-restart functionality (if enabled)
        """
        self._auto_restart = False
        self._stop()

    def _stop(self):
        self._is_advertising = False
        try:
            self.ble_device.ble_driver.ble_gap_adv_stop()
        except Exception:
            pass

    def _handle_adv_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.advertising:
            # Notify that advertising timed out first which may call stop() to disable auto-restart
            self._on_advertising_timeout.notify(self)
            if self._auto_restart:
                self._start()
            else:
                self._is_advertising = False

    def _handle_connect(self, peer, event):
        self._is_advertising = False

    def _handle_disconnect(self, peer, event):
        if self._auto_restart:
            self._start()
