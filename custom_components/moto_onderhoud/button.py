"""Knop 'uitgevoerd' per onderhoudstaak."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import MotoEntity
from .manager import MotoManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MotoManager = entry.runtime_data
    async_add_entities(DoneButton(manager, key) for key in manager.tasks)


class DoneButton(MotoEntity, ButtonEntity):
    """Registreert de taak als uitgevoerd op de huidige kilometerstand, vandaag."""

    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, manager: MotoManager, key: str) -> None:
        super().__init__(manager, key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}_done"
        self._attr_name = f"{self.task.name} uitgevoerd"

    async def async_press(self) -> None:
        self.manager.register(self.key)
