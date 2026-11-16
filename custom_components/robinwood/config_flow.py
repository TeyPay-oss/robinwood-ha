"""Einrichtungsdialog."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .api import FourHeatClient, FourHeatError
from .const import CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL


class RobinWoodConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                data = await FourHeatClient(host, port).read_all()
                if not data.readings:
                    errors["base"] = "no_data"
            except FourHeatError:
                errors["base"] = "cannot_connect"
            if not errors:
                return self.async_create_entry(
                    title="Robin Wood Pelletofen", data={CONF_HOST: host, CONF_PORT: port}
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RobinWoodOptionsFlow()


class RobinWoodOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            host = str(user_input.pop(CONF_HOST, entry.data[CONF_HOST])).strip()
            if host and host != entry.data[CONF_HOST]:
                # IP-Adresse geändert: in den Eintragsdaten speichern
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_HOST: host}
                )
            return self.async_create_entry(data=user_input)
        current = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=600)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
