"""Freshness and revocation tests using the actual HA coordinator and flow APIs."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ble_arrival.config_flow import BLEArrivalOptionsFlow
from custom_components.ble_arrival.coordinator import ArrivalCoordinator
from custom_components.ble_arrival.provisioning import new_car


@pytest.mark.asyncio
async def test_stop_cancels_inflight_and_clears_freshness(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    entry = SimpleNamespace(
        data={**new_car("Car", "t_dongle_s3"), "verified": True}, async_on_unload=Mock()
    )
    coordinator = ArrivalCoordinator(hass, entry, asyncio.Semaphore(2))
    coordinator.last_success_monotonic = __import__("time").monotonic()
    coordinator._task = asyncio.create_task(asyncio.sleep(100))
    assert coordinator.fresh
    await coordinator.stop()
    assert not coordinator.fresh
    assert coordinator._task.cancelled()
    coordinator.request_attempt(force=True)
    assert coordinator._task.cancelled()


@pytest.mark.asyncio
async def test_revoke_stops_before_replacing_key():
    data = {**new_car("Car", "t_dongle_s3"), "verified": True}
    entry = SimpleNamespace(data=data, title="Car", runtime_data=SimpleNamespace(stop=AsyncMock()))

    def update(target, *, data):
        entry.runtime_data.stop.assert_awaited_once()
        assert data["key"] != entry.data["key"]
        assert data["device_id"] == entry.data["device_id"]
        assert data["verified"] is False

    flow = BLEArrivalOptionsFlow()
    flow.handler = "entry"
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_get_known_entry=lambda _: entry, async_update_entry=Mock(side_effect=update)
        )
    )
    result = await flow.async_step_revoke({})
    assert result["type"] == "create_entry"
    flow.hass.config_entries.async_update_entry.assert_called_once()


@pytest.mark.asyncio
async def test_copy_configuration_is_resumable():
    entry = SimpleNamespace(data=new_car("Car", "t_dongle_s3"))
    flow = BLEArrivalOptionsFlow()
    flow.handler = "entry"
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_get_known_entry=lambda _: entry)
    )
    first = await flow.async_step_configuration()
    second = await flow.async_step_configuration()
    assert first["description_placeholders"] == second["description_placeholders"]
    assert entry.data["key"] in first["description_placeholders"]["secret"]


@pytest.mark.asyncio
async def test_verification_keeps_identity_and_credential(monkeypatch):
    from custom_components.ble_arrival import config_flow
    from custom_components.ble_arrival.transport import AuthenticationResult

    data = new_car("Test car", "t_dongle_s3")
    entry = SimpleNamespace(data=data)
    updates = Mock()
    flow = BLEArrivalOptionsFlow()
    flow.handler = "entry"
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_get_known_entry=lambda _: entry, async_update_entry=updates
        )
    )
    monkeypatch.setattr(
        config_flow, "candidates", lambda *a: [SimpleNamespace(address="dongle", name="Test")]
    )
    monkeypatch.setattr(
        config_flow,
        "authenticate",
        AsyncMock(
            return_value=AuthenticationResult(data["device_id"], "0.1.0", "proxy-b", "Garage")
        ),
    )
    result = await flow.async_step_verify({})
    assert result["type"] == "create_entry"
    saved = updates.call_args.kwargs["data"]
    assert saved["verified"] is True
    assert saved["key"] == data["key"]
    assert saved["device_id"] == data["device_id"]
    assert saved["firmware"] == "0.1.0"
