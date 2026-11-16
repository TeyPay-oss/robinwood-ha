"""Störungsmelder."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RobinWoodConfigEntry
from .const import P_ERROR, P_STATUS, STATUS_BLOCK
from .entity import RobinWoodEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RobinWoodConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RWFaultSensor(entry.runtime_data)])


class RWFaultSensor(RobinWoodEntity, BinarySensorEntity):
    _attr_name = "Störung"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "stoerung")

    @property
    def is_on(self) -> bool | None:
        err = self.value(P_ERROR)
        st = self.value(P_STATUS)
        if err is None and st is None:
            return None
        return bool(err) or (st is not None and int(st) == STATUS_BLOCK)
