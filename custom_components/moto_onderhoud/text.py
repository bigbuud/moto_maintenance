"""Notitievelden per onderhoudstaak."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import MotoEntity
from .manager import MotoManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MotoManager = entry.runtime_data
    async_add_entities(NoteText(manager, key) for key in manager.tasks)


class NoteText(MotoEntity, TextEntity):
    """Vrije notitie (type filter, prijs, ...)."""

    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 255
    _attr_icon = "mdi:note-text-outline"

    def __init__(self, manager: MotoManager, key: str) -> None:
        super().__init__(manager, key)
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}_note"
        self._attr_name = f"{self.task.name} notitie"

    @property
    def native_value(self) -> str:
        return self.task.note

    async def async_set_value(self, value: str) -> None:
        self.manager.set_note(self.key, value)
