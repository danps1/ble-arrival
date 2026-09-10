"""A failed connection must not defer the 30-second freshness notification."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ble_arrival import coordinator as module


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["authenticated", "connection_failed", "authentication_failed"])
async def test_expiry_publishes_during_retry(tmp_path, monkeypatch, status):
    entry = SimpleNamespace(data={"verified": True}, async_on_unload=Mock())
    coordinator = module.ArrivalCoordinator(
        HomeAssistant(str(tmp_path)), entry, asyncio.Semaphore(2)
    )
    coordinator.last_success_monotonic = 100.0
    coordinator._expiry_notified = False
    coordinator.status = status
    coordinator.sequence = 7
    coordinator.request_attempt = Mock()
    coordinator.async_set_updated_data = Mock()
    clock = SimpleNamespace(monotonic=lambda: 129.9)
    monkeypatch.setattr(module, "time", clock)
    coordinator._tick(None)
    coordinator.async_set_updated_data.assert_not_called()
    clock.monotonic = lambda: 130.1
    coordinator._tick(None)
    assert not coordinator.fresh
    coordinator.async_set_updated_data.assert_called_once_with(7)
    assert coordinator.sequence == 7  # Expiry must not emit another authentication event.
    coordinator._tick(None)
    coordinator.async_set_updated_data.assert_called_once()
