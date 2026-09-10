"""Recent authentication, not arrival or proof of distance."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import ArrivalEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RecentAuthentication(entry.runtime_data)])


class RecentAuthentication(ArrivalEntity, BinarySensorEntity):
    _attr_name = "Recently authenticated"
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(self, coordinator):
        super().__init__(coordinator, "recently_authenticated")

    @property
    def is_on(self):
        return self.coordinator.fresh
