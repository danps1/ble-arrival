"""An event is emitted only for a newly verified exchange."""

from homeassistant.components.event import EventEntity
from homeassistant.core import callback

from .entity import ArrivalEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AuthenticationEvent(entry.runtime_data)])


class AuthenticationEvent(ArrivalEntity, EventEntity):
    _attr_name = "Authentication"
    _attr_event_types = ["authenticated"]

    def __init__(self, coordinator):
        super().__init__(coordinator, "authentication")
        self._sequence = coordinator.sequence

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.sequence > self._sequence:
            self._sequence = self.coordinator.sequence
            self._trigger_event(
                "authenticated",
                {"uptime_seconds": self.coordinator.uptime_seconds},
            )
        self.async_write_ha_state()
