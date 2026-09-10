"""Per-car authentication with bounded global concurrency and expiry."""

import asyncio
import logging
import time
from datetime import timedelta

from homeassistant.components import bluetooth
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DEFAULT_FRESHNESS, DEFAULT_INTERVAL, DOMAIN, SERVICE_UUID
from .protocol import AuthenticationError
from .transport import DeviceUnavailable, authenticate, candidates

_LOGGER = logging.getLogger(__name__)


class ArrivalCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, semaphore):
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry)
        self.entry = entry
        self.semaphore = semaphore
        self.last_success = None
        self.last_source = None
        self.last_source_name = None
        self._expiry_notified = True
        self.last_success_monotonic = None
        self.address = entry.data.get("address")
        self.firmware = entry.data.get("firmware")
        self.status = "awaiting_dongle"
        self.sequence = 0
        self._last_attempt = 0.0
        self._task = None
        self._unsubs = []
        self._stopped = False

    @property
    def fresh(self):
        return (
            self.last_success_monotonic is not None
            and time.monotonic() - self.last_success_monotonic < DEFAULT_FRESHNESS
        )

    @callback
    def start(self):
        self._unsubs.append(
            bluetooth.async_register_callback(
                self.hass,
                self._advertisement,
                {"service_uuid": SERVICE_UUID, "connectable": True},
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(seconds=1)))
        self.async_set_updated_data(self.sequence)
        self.request_attempt()

    @callback
    def _advertisement(self, info, change):
        self.request_attempt()

    @callback
    def _tick(self, now):
        # A failed attempt may change status before freshness expires. Expiry
        # must still publish while a retry is in flight, independently of status.
        if not self._expiry_notified and not self.fresh:
            self._expiry_notified = True
            if self.status == "authenticated":
                self.status = "not_recently_authenticated"
            self.async_set_updated_data(self.sequence)
        self.request_attempt()

    @callback
    def request_attempt(self, force=False):
        if self._stopped or not self.entry.data.get("verified"):
            return
        if self._task is not None and not self._task.done():
            return
        if not force and time.monotonic() - self._last_attempt < DEFAULT_INTERVAL:
            return
        self._last_attempt = time.monotonic()
        self._task = self.hass.async_create_task(self._attempt())

    async def _attempt(self):
        async with self.semaphore:
            if self._stopped:
                return
            # Limit discovery work per cycle; preferred authenticated address goes first.
            infos = candidates(self.hass, self.address)
            preferred_name = "ble-arrival-" + self.entry.data["device_id"][:8]
            infos.sort(key=lambda i: (i.address != self.address, i.name != preferred_name))
            for info in infos[:4]:
                try:
                    result = await authenticate(
                        self.hass,
                        info.address,
                        self.entry.data["device_id"],
                        self.entry.data["key"],
                    )
                except AuthenticationError:
                    self.status = "authentication_failed"
                    continue
                except DeviceUnavailable:
                    self.status = "connection_failed"
                    continue
                self.address = info.address
                self.firmware = result.firmware
                self.last_source = result.source
                self.last_source_name = result.source_name
                self._expiry_notified = False
                self.last_success = dt_util.utcnow()
                self.last_success_monotonic = time.monotonic()
                self.sequence += 1
                self.status = "authenticated"
                self.async_set_updated_data(self.sequence)
                return
            if not self.fresh:
                self.status = self.status if infos else "awaiting_dongle"
            self.async_set_updated_data(self.sequence)

    async def stop(self):
        self._stopped = True
        self.last_success_monotonic = None
        self.status = "revoked_or_unloaded"
        self.async_set_updated_data(self.sequence)
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
