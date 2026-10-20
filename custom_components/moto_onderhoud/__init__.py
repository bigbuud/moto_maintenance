"""Moto Onderhoud: onderhoudsplanner voor je motor."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, PLATFORMS, STORAGE_VERSION
from .manager import MotoManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet een motor op."""
    manager = MotoManager(hass, entry)
    await manager.async_load()
    entry.runtime_data = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    manager.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ontlaad een motor."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        manager: MotoManager = entry.runtime_data
        manager.async_stop()
        await manager.async_flush()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Verwijder opgeslagen gegevens."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()
