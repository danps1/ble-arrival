"""Only a successful exchange may replace the displayed authentication route."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ble_arrival import coordinator as module
from custom_components.ble_arrival.event import AuthenticationEvent
from custom_components.ble_arrival.sensor import LastAuthenticatedVia, UptimeAtAuthentication
from custom_components.ble_arrival.transport import AuthenticationResult, DeviceUnavailable


@pytest.mark.asyncio
async def test_route_updates_only_after_success(tmp_path, monkeypatch):
    entry = SimpleNamespace(
        data={"verified": True, "device_id": "00" * 16, "key": "01" * 32},
        title="Test car",
        async_on_unload=Mock(),
    )
    coordinator = module.ArrivalCoordinator(
        HomeAssistant(str(tmp_path)), entry, asyncio.Semaphore(2)
    )
    uptime = UptimeAtAuthentication(coordinator)
    event = AuthenticationEvent(coordinator)
    event._trigger_event = Mock()
    event.async_write_ha_state = Mock()
    assert uptime.native_value is None
    sensor = LastAuthenticatedVia(coordinator)
    assert sensor.native_value is None
    info = SimpleNamespace(address="dongle", name="test")
    monkeypatch.setattr(module, "candidates", lambda *a: [info])
    exchange = AsyncMock(
        return_value=AuthenticationResult("00" * 16, "0.1.0", "proxy-a", "Garage", 301)
    )
    monkeypatch.setattr(module, "authenticate", exchange)
    await coordinator._attempt()
    assert sensor.native_value == "Garage"
    assert sensor.extra_state_attributes["source"] == "proxy-a"
    first_time = sensor.extra_state_attributes["authenticated_at"]
    assert uptime.native_value == 301
    assert uptime.extra_state_attributes["authenticated_at"] == first_time
    event._handle_coordinator_update()
    event._trigger_event.assert_called_once_with("authenticated", {"uptime_seconds": 301})
    event._trigger_event.reset_mock()
    exchange.side_effect = DeviceUnavailable()
    await coordinator._attempt()
    assert sensor.native_value == "Garage"
    assert sensor.extra_state_attributes["authenticated_at"] == first_time
    assert uptime.native_value == 301
    event._handle_coordinator_update()
    event._trigger_event.assert_not_called()
    exchange.side_effect = None
    exchange.return_value = AuthenticationResult("00" * 16, "0.1.0", "proxy-b", "Hallway", 2)
    await coordinator._attempt()
    assert sensor.native_value == "Hallway"
    assert uptime.native_value == 2  # Reboot replaces the old reading, even if lower.
    assert sensor.extra_state_attributes["source"] == "proxy-b"
    exchange.return_value = AuthenticationResult("00" * 16, "0.1.0")
    await coordinator._attempt()
    assert uptime.native_value is None  # Legacy success clears stale uptime.
    assert sensor.native_value is None  # Do not label a new exchange with an older route.
