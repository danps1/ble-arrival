"""Non-secret diagnostics."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory, UnitOfTime

from .entity import ArrivalEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            LastAuthentication(entry.runtime_data),
            ConnectionStatus(entry.runtime_data),
            LastAuthenticatedVia(entry.runtime_data),
            UptimeAtAuthentication(entry.runtime_data),
        ]
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


class LastAuthenticatedVia(ArrivalEntity, SensorEntity):
    """Last successful connection route, retained when the car goes away."""

    _attr_name = "Last authenticated via"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(self, coordinator):
        super().__init__(coordinator, "last_authenticated_via")

    @property
    def native_value(self):
        return self.coordinator.last_source_name

    @property
    def extra_state_attributes(self):
        return {
            "source": self.coordinator.last_source,
            "authenticated_at": self.coordinator.last_success,
        }


class UptimeAtAuthentication(ArrivalEntity, SensorEntity):
    """Authenticated snapshot, never an extrapolated live counter."""

    _attr_name = "Uptime at last authentication"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer-outline"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator):
        super().__init__(coordinator, "uptime_at_last_authentication")

    @property
    def native_value(self):
        return self.coordinator.uptime_seconds

    @property
    def extra_state_attributes(self):
        return {"authenticated_at": self.coordinator.last_success}
