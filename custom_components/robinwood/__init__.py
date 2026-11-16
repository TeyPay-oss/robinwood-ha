"""Robin Wood Pelletofen über das 4Heat-WLAN-Modul (lokal)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol

from .api import FourHeatClient
from .api import FourHeatError
from .const import DEFAULT_PORT, DOMAIN
from .coordinator import RobinWoodCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type RobinWoodConfigEntry = ConfigEntry[RobinWoodCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: RobinWoodConfigEntry) -> bool:
    client = FourHeatClient(entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    coordinator = RobinWoodCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    _register_services(hass)
    return True


READ_SCHEMA = vol.Schema(
    {
        vol.Required("start"): vol.All(vol.Coerce(int), vol.Range(min=30000, max=59999)),
        vol.Optional("ende"): vol.All(vol.Coerce(int), vol.Range(min=30000, max=59999)),
        vol.Optional("nur_treffer", default=True): bool,
    }
)


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "parameter_lesen"):
        return

    async def _read(call: ServiceCall) -> ServiceResponse:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("Kein Pelletofen eingerichtet")
        client: FourHeatClient = entries[0].runtime_data.client
        start = call.data["start"]
        end = call.data.get("ende", start)
        if end < start or end - start > 200:
            raise HomeAssistantError("Bereich ungültig (max. 200 Parameter pro Aufruf)")
        pids = [f"{n:05d}" for n in range(start, end + 1) if str(n)[0] in "35"]
        found: dict[str, float | int | None] = {}
        for i in range(0, len(pids), 8):
            chunk = pids[i : i + 8]
            try:
                found.update(await client.read_codes(chunk))
            except FourHeatError:
                # Einzeln nachfassen, falls ein Parameter den Block stört
                for pid in chunk:
                    try:
                        found.update(await client.read_codes([pid]))
                    except FourHeatError:
                        found[pid] = None
        if call.data["nur_treffer"]:
            found = {k: v for k, v in found.items() if v is not None}
        return {"werte": found}

    hass.services.async_register(
        DOMAIN,
        "parameter_lesen",
        _read,
        schema=READ_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


async def _async_reload(hass: HomeAssistant, entry: RobinWoodConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: RobinWoodConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
