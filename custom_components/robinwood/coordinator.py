"""DataUpdateCoordinator für den Pelletofen."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FourHeatClient, FourHeatError, StoveData, build_write_code
from .const import (
    CODE_OFF,
    CODE_ON,
    CODE_UNLOCK,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class RobinWoodCoordinator(DataUpdateCoordinator[StoveData]):
    """Fragt das Modul zyklisch ab und schreibt Befehle."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: FourHeatClient) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.client = client
        self._failures = 0

    async def _async_update_data(self) -> StoveData:
        try:
            data = await self.client.read_all()
        except FourHeatError as err:
            self._failures += 1
            # Einzelne Aussetzer überbrücken: alte Werte behalten
            if self.data is not None and self._failures < 4:
                _LOGGER.debug("Abfrage fehlgeschlagen (%s), behalte alte Werte", err)
                return self.data
            raise UpdateFailed(str(err)) from err
        self._failures = 0
        return data

    async def _send(self, *codes: str) -> None:
        try:
            await self.client.send_codes(*codes)
        except FourHeatError as err:
            raise UpdateFailed(f"Befehl nicht angekommen: {err}") from err
        # Das Modul braucht etwas, bis der neue Zustand im SEL steht
        await asyncio.sleep(3)
        await self.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self._send(CODE_ON)

    async def async_turn_off(self) -> None:
        await self._send(CODE_OFF)

    async def async_unlock(self) -> None:
        await self._send(CODE_UNLOCK)

    async def async_write(self, pid: str, value: int) -> None:
        await self._send(build_write_code(pid, value))
