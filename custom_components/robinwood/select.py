"""Leistungsstufe wählen."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RobinWoodConfigEntry
from .const import P_POWER_MAX, P_POWER_SET, POWER_OFFSET
from .entity import RobinWoodEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RobinWoodConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RWPowerSelect(entry.runtime_data)])


class RWPowerSelect(RobinWoodEntity, SelectEntity):
    _attr_name = "Leistungsstufe"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "leistungsstufe")

    def _max(self) -> int:
        m = self.value(P_POWER_MAX)
        try:
            m = int(m)
        except (TypeError, ValueError):
            m = 5
        return max(1, min(m, 9))

    @property
    def options(self) -> list[str]:
        return [f"Stufe {i}" for i in range(1, self._max() + 1)]

    @property
    def available(self) -> bool:
        return super().available and self.value(P_POWER_SET) is not None

    @property
    def current_option(self) -> str | None:
        v = self.value(P_POWER_SET)
        if v is None:
            return None
        stufe = int(v) - POWER_OFFSET
        opt = f"Stufe {stufe}"
        return opt if opt in self.options else None

    async def async_select_option(self, option: str) -> None:
        stufe = int(option.split()[-1])
        if not 1 <= stufe <= self._max():
            raise ValueError(f"Ungültige Stufe: {option}")
        await self.coordinator.async_write(P_POWER_SET, stufe + POWER_OFFSET)
