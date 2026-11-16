"""Sensoren."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfPressure, UnitOfTemperature, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RobinWoodConfigEntry
from .const import (
    ERROR_TEXT,
    P_AIRFLOW,
    P_DEPRESSION,
    P_ERROR,
    P_EXHAUST,
    P_OUTDOOR,
    P_POWER_MAX,
    P_POWER_SET,
    P_POWER_WOOD,
    P_PUFFER,
    P_RETURN,
    P_STATUS,
    P_WATER,
    POWER_OFFSET,
    STATUS_TEXT,
)
from .entity import RobinWoodEntity


@dataclass(frozen=True, kw_only=True)
class RWSensorDescription(SensorEntityDescription):
    pid: str


TEMP = dict(
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
)

SENSORS: tuple[RWSensorDescription, ...] = (
    RWSensorDescription(key="wasser", pid=P_WATER, name="Wassertemperatur", icon="mdi:water-thermometer", **TEMP),
    RWSensorDescription(key="puffer", pid=P_PUFFER, name="Puffertemperatur", icon="mdi:storage-tank", **TEMP),
    RWSensorDescription(key="abgas", pid=P_EXHAUST, name="Abgastemperatur", icon="mdi:smoke", **TEMP),
    RWSensorDescription(key="ruecklauf", pid=P_RETURN, name="Rücklauftemperatur", icon="mdi:thermometer-chevron-down", **TEMP),
    RWSensorDescription(key="aussen", pid=P_OUTDOOR, name="Außenfühler", icon="mdi:thermometer", **TEMP),
    RWSensorDescription(
        key="luftstrom",
        pid=P_AIRFLOW,
        name="Luftstrom",
        icon="mdi:weather-windy",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RWSensorDescription(
        key="unterdruck",
        pid=P_DEPRESSION,
        name="Abgasunterdruck",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RWSensorDescription(
        key="leistung_max",
        pid=P_POWER_MAX,
        name="Leistungsstufen (Anzahl)",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RWSensorDescription(
        key="leistung_holz",
        pid=P_POWER_WOOD,
        name="Leistung Holz (Rohwert)",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)

KNOWN = {d.pid for d in SENSORS} | {P_STATUS, P_ERROR, P_POWER_SET}


async def async_setup_entry(
    hass: HomeAssistant, entry: RobinWoodConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coord = entry.runtime_data
    entities: list[SensorEntity] = [RWSensor(coord, d) for d in SENSORS]
    entities += [RWStatusSensor(coord), RWErrorSensor(coord), RWPowerSensor(coord)]
    # Alle weiteren Werte, die das Modul liefert, als (deaktivierte) Rohwert-Sensoren
    if coord.data:
        for pid, reading in sorted(coord.data.readings.items()):
            if pid not in KNOWN:
                entities.append(RWRawSensor(coord, pid, reading.marker))
    async_add_entities(entities)


class RWSensor(RobinWoodEntity, SensorEntity):
    entity_description: RWSensorDescription

    def __init__(self, coordinator, description: RWSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        return super().available and self.value(self.entity_description.pid) is not None

    @property
    def native_value(self):
        return self.value(self.entity_description.pid)


class RWStatusSensor(RobinWoodEntity, SensorEntity):
    _attr_name = "Status"
    _attr_icon = "mdi:fire-circle"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "status")

    @property
    def native_value(self):
        v = self.value(P_STATUS)
        if v is None:
            return None
        return STATUS_TEXT.get(int(v), f"Status {int(v)}")

    @property
    def extra_state_attributes(self):
        return {"code": self.value(P_STATUS)}


class RWErrorSensor(RobinWoodEntity, SensorEntity):
    _attr_name = "Fehler"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "fehler")

    @property
    def native_value(self):
        v = self.value(P_ERROR)
        if v is None:
            return None
        return ERROR_TEXT.get(int(v), f"Fehler {int(v)}")

    @property
    def extra_state_attributes(self):
        return {"code": self.value(P_ERROR)}


class RWPowerSensor(RobinWoodEntity, SensorEntity):
    _attr_name = "Leistungsstufe eingestellt"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "leistung_eingestellt")

    @property
    def native_value(self):
        v = self.value(P_POWER_SET)
        if v is None:
            return None
        v = int(v)
        if v == 0:
            return "Zündleistung"
        if v == 1:
            return "Standby"
        return f"Stufe {v - POWER_OFFSET}"

    @property
    def extra_state_attributes(self):
        return {"rohwert": self.value(P_POWER_SET)}


class RWRawSensor(RobinWoodEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:numeric"

    def __init__(self, coordinator, pid: str, marker: str) -> None:
        super().__init__(coordinator, f"raw_{pid}")
        self._pid = pid
        self._attr_name = f"Parameter {pid}"
        self._marker = marker

    @property
    def native_value(self):
        return self.value(self._pid)

    @property
    def extra_state_attributes(self):
        return {"parameter": self._pid, "marker": self._marker}
