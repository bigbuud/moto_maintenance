"""Number-entiteiten: kilometerstand en intervallen."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import MotoEntity
from .manager import MotoManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MotoManager = entry.runtime_data
    entities: list[NumberEntity] = [OdometerNumber(manager)]
    for key in manager.tasks:
        entities.append(IntervalKmNumber(manager, key))
        entities.append(IntervalMonthsNumber(manager, key))
    async_add_entities(entities)


class OdometerNumber(MotoEntity, NumberEntity):
    """Huidige kilometerstand."""

    _attr_name = "Kilometerstand"
    _attr_icon = "mdi:counter"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 1_000_000
    _attr_native_step = 1
    _attr_device_class = NumberDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, manager: MotoManager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_odometer"

    @property
    def native_value(self) -> float:
        return self.manager.odometer

    async def async_set_native_value(self, value: float) -> None:
        self.manager.set_odometer(value)


class IntervalKmNumber(MotoEntity, NumberEntity):
    """Interval in km (0 = niet op km)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 100_000
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, manager: MotoManager, key: str) -> None:
        super().__init__(manager, key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}_interval_km"
        self._attr_name = f"{self.task.name} interval (km)"
        self._attr_icon = "mdi:ruler"

    @property
    def native_value(self) -> float:
        return self.task.interval_km

    async def async_set_native_value(self, value: float) -> None:
        self.manager.set_interval_km(self.key, value)


class IntervalMonthsNumber(MotoEntity, NumberEntity):
    """Interval in maanden (0 = niet op tijd)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MONTHS

    def __init__(self, manager: MotoManager, key: str) -> None:
        super().__init__(manager, key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}_interval_months"
        self._attr_name = f"{self.task.name} interval (maanden)"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self) -> float:
        return self.task.interval_months

    async def async_set_native_value(self, value: float) -> None:
        self.manager.set_interval_months(self.key, value)
