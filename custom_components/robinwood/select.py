"""Verbrennungsleistung wählen (P1 … Pn, Auto)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RobinWoodConfigEntry
from .const import P_POWER_MAX, P_POWER_SET
from .entity import RobinWoodEntity

AUTO = "Auto"


async def async_setup_entry(
    hass: HomeAssistant, entry: RobinWoodConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RWPowerSelect(entry.runtime_data)])


def power_label(raw: int | None, levels: int) -> str | None:
    """Rohwert 1..n = P1..Pn, n+1 = Auto (wie im Menü am Ofen)."""
    if raw is None:
        return None
    raw = int(raw)
    if 1 <= raw <= levels:
        return f"P{raw}"
    if raw == levels + 1:
        return AUTO
    return None


class RWPowerSelect(RobinWoodEntity, SelectEntity):
    _attr_name = "Verbrennungsleistung"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "leistungsstufe")

    def _levels(self) -> int:
        try:
            m = int(self.value(P_POWER_MAX))
        except (TypeError, ValueError):
            m = 5
        return max(1, min(m, 9))

    @property
    def options(self) -> list[str]:
        return [f"P{i}" for i in range(1, self._levels() + 1)] + [AUTO]

    @property
    def available(self) -> bool:
        return super().available and self.value(P_POWER_SET) is not None

    @property
    def current_option(self) -> str | None:
        return power_label(self.value(P_POWER_SET), self._levels())

    async def async_select_option(self, option: str) -> None:
        n = self._levels()
        if option == AUTO:
            raw = n + 1
        else:
            raw = int(option.lstrip("P"))
            if not 1 <= raw <= n:
                raise ValueError(f"Ungültige Leistung: {option}")
        await self.coordinator.async_write(P_POWER_SET, raw)
