"""Common device identity."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class ArrivalEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.data['device_id']}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.data["device_id"])},
            name=coordinator.entry.title,
            manufacturer="BLE Arrival",
            model="ESPHome BLE credential",
            sw_version=coordinator.firmware,
        )
