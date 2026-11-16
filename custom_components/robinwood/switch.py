"""Ein/Aus-Schalter."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RobinWoodConfigEntry
from .const import P_STATUS, STATUS_ON
from .entity import RobinWoodEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RobinWoodConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RWPowerSwitch(entry.runtime_data)])


class RWPowerSwitch(RobinWoodEntity, SwitchEntity):
    _attr_name = "Ofen"
    _attr_icon = "mdi:fire"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "ofen")

    @property
    def is_on(self) -> bool | None:
        v = self.value(P_STATUS)
        return None if v is None else int(v) in STATUS_ON

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_turn_off()
