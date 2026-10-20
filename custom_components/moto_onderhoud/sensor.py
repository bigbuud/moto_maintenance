"""Statussensoren per onderhoudstaak."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import STATUSES
from .entity import MotoEntity
from .manager import MotoManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MotoManager = entry.runtime_data
    async_add_entities(TaskSensor(manager, key) for key in manager.tasks)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "register_maintenance",
        {
            vol.Optional("km"): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional("date"): cv.date,
            vol.Optional("note"): cv.string,
        },
        "async_register_maintenance",
    )


class TaskSensor(MotoEntity, SensorEntity):
    """Status van één onderhoudstaak."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES

    def __init__(self, manager: MotoManager, key: str) -> None:
        super().__init__(manager, key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}_status"
        self._attr_name = self.task.name
        self._attr_icon = self.task.icon

    @property
    def native_value(self) -> str:
        return self.manager.state(self.task).status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        task = self.task
        st = self.manager.state(task)
        return {
            "km_remaining": None if st.km_remaining is None else round(st.km_remaining),
            "days_remaining": st.days_remaining,
            "last_km": round(task.last_km),
            "last_date": task.last_date,
            "interval_km": task.interval_km,
            "interval_months": task.interval_months,
            "note": task.note,
        }

    async def async_register_maintenance(
        self, km: float | None = None, date=None, note: str | None = None
    ) -> None:
        """Service: registreer uitgevoerd onderhoud."""
        self.manager.register(self.key, km, date, note)
