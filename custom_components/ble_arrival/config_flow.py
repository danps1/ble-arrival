"""Resumable setup: persist the credential before asking the user to flash."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN
from .protocol import AuthenticationError, decode_hex
from .provisioning import BOARDS, configuration, new_car
from .transport import DeviceUnavailable, authenticate, candidates

NAME_SCHEMA = vol.Schema(
    {
        vol.Required("name"): selector.TextSelector(),
        vol.Required("board", default="t_dongle_s3"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[{"value": k, "label": v} for k, v in BOARDS.items()]
            )
        ),
    }
)


def secret_selector():
    return selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
    )


class BLEArrivalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return self.async_show_menu(step_id="user", menu_options=["new", "existing"])

    async def async_step_new(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                data = new_car(user_input["name"], user_input["board"])
            except ValueError:
                errors["base"] = "invalid_input"
            else:
                await self.async_set_unique_id(data["device_id"])
                self._abort_if_unique_id_configured()
                # This is an intentionally pending entry. No entities or authentication
                # tasks exist until the user flashes and verifies in the options flow.
                return self.async_create_entry(title=data["name"], data=data)
        return self.async_show_form(step_id="new", data_schema=NAME_SCHEMA, errors=errors)

    async def async_step_existing(self, user_input=None):
        infos = candidates(self.hass)
        errors = {}
        if user_input is not None and (
            not user_input["name"].strip() or len(user_input["name"]) > 64
        ):
            errors["base"] = "invalid_input"
            user_input = None
        if user_input is not None:
            try:
                decode_hex(user_input["key"], 32)
            except ValueError:
                errors["base"] = "invalid_key"
            else:
                try:
                    result = await authenticate(
                        self.hass, user_input["address"], None, user_input["key"]
                    )
                except AuthenticationError:
                    errors["base"] = "invalid_auth"
                except DeviceUnavailable:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(result.device_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input["name"].strip(),
                        data={
                            "name": user_input["name"].strip(),
                            "board": "esp32_s3",
                            "device_id": result.device_id,
                            "key": user_input["key"].lower(),
                            "verified": True,
                            "address": user_input["address"],
                            "firmware": result.firmware,
                        },
                    )
        if not infos:
            errors.setdefault("base", "no_dongles")
        schema = vol.Schema(
            {
                vol.Required("name"): selector.TextSelector(),
                vol.Required("address"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": i.address, "label": i.name or i.address} for i in infos]
                    )
                ),
                vol.Required("key"): secret_selector(),
            }
        )
        return self.async_show_form(step_id="existing", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BLEArrivalOptionsFlow()


class BLEArrivalOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        options = ["configuration"]
        if not self.config_entry.data.get("verified"):
            options.append("verify")
        if self.config_entry.data.get("verified"):
            options.append("revoke")
        return self.async_show_menu(step_id="init", menu_options=options)

    async def async_step_configuration(self, user_input=None):
        if user_input is not None:
            if self.config_entry.data.get("verified"):
                return self.async_create_entry(title="", data={})
            return await self.async_step_verify()
        full, snippet, secret = configuration(self.config_entry.data)
        return self.async_show_form(
            step_id="configuration",
            data_schema=vol.Schema({}),
            description_placeholders={
                "full_yaml": full,
                "snippet": snippet,
                "secret": secret,
            },
        )

    async def async_step_verify(self, user_input=None):
        errors = {}
        if user_input is not None:
            data = dict(self.config_entry.data)
            infos = candidates(self.hass, data.get("address"))
            infos.sort(
                key=lambda i: (
                    i.address != data.get("address"),
                    i.name != "ble-arrival-" + data["device_id"][:8],
                )
            )
            errors["base"] = "no_dongles" if not infos else "cannot_verify"
            for info in infos[:8]:
                try:
                    result = await authenticate(
                        self.hass, info.address, data["device_id"], data["key"]
                    )
                except AuthenticationError, DeviceUnavailable:
                    continue
                data.update(verified=True, address=info.address, firmware=result.firmware)
                self.hass.config_entries.async_update_entry(self.config_entry, data=data)
                return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="verify", data_schema=vol.Schema({}), errors=errors)

    async def async_step_revoke(self, user_input=None):
        if user_input is not None:
            await self.config_entry.runtime_data.stop()
            # Replacing the credential immediately retires the old dongle. The same
            # identity/entity IDs are kept for a deliberate subsequent USB reflash.
            data = new_car(self.config_entry.title, self.config_entry.data["board"])
            data["device_id"] = self.config_entry.data["device_id"]
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="revoke", data_schema=vol.Schema({}))
