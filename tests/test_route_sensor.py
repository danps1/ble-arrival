"""Only a successful exchange may replace the displayed authentication route."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ble_arrival import coordinator as module
from custom_components.ble_arrival.sensor import LastAuthenticatedVia
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
    sensor = LastAuthenticatedVia(coordinator)
    assert sensor.native_value is None
    info = SimpleNamespace(address="dongle", name="test")
    monkeypatch.setattr(module, "candidates", lambda *a: [info])
    exchange = AsyncMock(return_value=AuthenticationResult("00" * 16, "0.1.0", "proxy-a", "Garage"))
    monkeypatch.setattr(module, "authenticate", exchange)
    await coordinator._attempt()
    assert sensor.native_value == "Garage"
    assert sensor.extra_state_attributes["source"] == "proxy-a"
    first_time = sensor.extra_state_attributes["authenticated_at"]
    exchange.side_effect = DeviceUnavailable()
    await coordinator._attempt()
    assert sensor.native_value == "Garage"
    assert sensor.extra_state_attributes["authenticated_at"] == first_time
    exchange.side_effect = None
    exchange.return_value = AuthenticationResult("00" * 16, "0.1.0", "proxy-b", "Hallway")
    await coordinator._attempt()
    assert sensor.native_value == "Hallway"
    assert sensor.extra_state_attributes["source"] == "proxy-b"
    exchange.return_value = AuthenticationResult("00" * 16, "0.1.0")
    await coordinator._attempt()
    assert sensor.native_value is None  # Do not label a new exchange with an older route.
