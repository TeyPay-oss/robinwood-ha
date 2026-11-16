"""Gemeinsame Basisklasse."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RobinWoodCoordinator


class RobinWoodEntity(CoordinatorEntity[RobinWoodCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: RobinWoodCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Pelletofen",
            manufacturer="Robin Wood",
            model="4Heat WLAN-Modul",
        )

    def value(self, pid: str):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(pid)
