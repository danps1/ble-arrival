"""Non-secret diagnostics."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory

from .entity import ArrivalEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [LastAuthentication(entry.runtime_data), ConnectionStatus(entry.runtime_data)]
    )


class LastAuthentication(ArrivalEntity, SensorEntity):
    _attr_name = "Last authentication"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "last_authentication")

    @property
    def native_value(self):
        return self.coordinator.last_success


class ConnectionStatus(ArrivalEntity, SensorEntity):
    _attr_name = "Connection status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "connection_status")

    @property
    def native_value(self):
        return self.coordinator.status
