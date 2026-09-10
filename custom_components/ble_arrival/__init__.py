"""BLE Arrival: authenticated detections, never door control."""

import asyncio

from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import ArrivalCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.EVENT, Platform.BUTTON]


async def async_setup_entry(hass, entry):
    shared = hass.data.setdefault(DOMAIN, {})
    semaphore = shared.setdefault("semaphore", asyncio.Semaphore(2))
    coordinator = ArrivalCoordinator(hass, entry, semaphore)
    entry.runtime_data = coordinator
    coordinator.platforms_loaded = False
    entry.async_on_unload(entry.add_update_listener(_reload))
    if entry.data.get("verified"):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        coordinator.platforms_loaded = True
        coordinator.start()
    return True


async def _reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    await entry.runtime_data.stop()
    if not entry.runtime_data.platforms_loaded:
        return True
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
