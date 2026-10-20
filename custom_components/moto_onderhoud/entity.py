"""Basisentiteit voor Moto Onderhoud."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .manager import MotoManager, Task


class MotoEntity(Entity):
    """Entiteit die meeluistert met de manager."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: MotoManager, key: str | None = None) -> None:
        self.manager = manager
        self.key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)},
            name=manager.entry.title,
            manufacturer="Moto Onderhoud",
            model="Onderhoudsplanner",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def task(self) -> Task:
        assert self.key is not None
        return self.manager.tasks[self.key]

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.manager.signal, self.async_write_ha_state
            )
        )
