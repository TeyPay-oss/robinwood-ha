"""Tasten: Entsperren, Neu abfragen."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RobinWoodConfigEntry
from .entity import RobinWoodEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RobinWoodConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    async_add_entities([RWUnlockButton(c), RWRefreshButton(c)])


class RWUnlockButton(RobinWoodEntity, ButtonEntity):
    _attr_name = "Störung quittieren"
    _attr_icon = "mdi:lock-open-variant"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "entsperren")

    async def async_press(self) -> None:
        await self.coordinator.async_unlock()


class RWRefreshButton(RobinWoodEntity, ButtonEntity):
    _attr_name = "Jetzt abfragen"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "abfragen")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
