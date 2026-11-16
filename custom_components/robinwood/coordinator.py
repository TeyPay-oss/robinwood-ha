"""DataUpdateCoordinator für den Pelletofen."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FourHeatClient, FourHeatError, StoveData, build_write_code
from .const import (
    EXTRA_PIDS,
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
        self._polls = 0

    async def _async_update_data(self) -> StoveData:
        try:
            # Zusatzwerte nur bei jeder 2. Abfrage, alte Werte dazwischen übernehmen
            self._polls += 1
            want_extra = self._polls % 2 == 1
            data = await self.client.read_all(EXTRA_PIDS if want_extra else None)
            if self.data is not None:
                for pid in EXTRA_PIDS:
                    if pid not in data.readings and pid in self.data.readings:
                        data.readings[pid] = self.data.readings[pid]
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
            raise HomeAssistantError(f"Befehl nicht angekommen: {err}") from err
        # Das Modul braucht etwas, bis der neue Zustand im SEL steht
        await asyncio.sleep(3)
        await self.async_request_refresh()

    async def _read_now(self) -> StoveData | None:
        try:
            # Zusatzwerte nur bei jeder 2. Abfrage, alte Werte dazwischen übernehmen
            self._polls += 1
            want_extra = self._polls % 2 == 1
            data = await self.client.read_all(EXTRA_PIDS if want_extra else None)
            if self.data is not None:
                for pid in EXTRA_PIDS:
                    if pid not in data.readings and pid in self.data.readings:
                        data.readings[pid] = self.data.readings[pid]
        except FourHeatError as err:
            _LOGGER.debug("Kontroll-Abfrage fehlgeschlagen: %s", err)
            return None
        self._failures = 0
        self.async_set_updated_data(data)
        return data

    async def async_turn_on(self) -> None:
        await self._send(CODE_ON)

    async def async_turn_off(self) -> None:
        await self._send(CODE_OFF)

    async def async_unlock(self) -> None:
        await self._send(CODE_UNLOCK)

    async def async_write(self, pid: str, value: int) -> None:
        """Wert schreiben und prüfen, ob der Ofen ihn übernommen hat."""
        try:
            await self.client.send_codes(build_write_code(pid, value))
        except FourHeatError as err:
            raise HomeAssistantError(f"Befehl nicht angekommen: {err}") from err
        for _ in range(4):
            await asyncio.sleep(3)
            data = await self._read_now()
            if data is not None and data.get(pid) == value:
                return
        raise HomeAssistantError(
            "Der Ofen hat den neuen Wert nicht bestätigt – bitte am Display prüfen."
        )
