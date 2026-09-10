"""Allowlist diagnostics. Never dump a config entry or raw BLE frames."""


async def async_get_config_entry_diagnostics(hass, entry):
    c = entry.runtime_data
    return {
        "verified": bool(entry.data.get("verified")),
        "board": entry.data.get("board"),
        "firmware": c.firmware,
        "status": c.status,
        "recently_authenticated": c.fresh,
        "successful_exchanges_this_session": c.sequence,
    }
