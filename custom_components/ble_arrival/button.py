"""Explicit connection test without controlling anything."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .entity import ArrivalEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([TestConnection(entry.runtime_data)])


class TestConnection(ArrivalEntity, ButtonEntity):
    _attr_name = "Test connection"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "test_connection")

    async def async_press(self):
        self.coordinator.request_attempt(force=True)
