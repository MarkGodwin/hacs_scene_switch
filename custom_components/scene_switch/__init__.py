"""Component to wrap Home Assistant scene entities with a switch that tracks the scene's state."""

from __future__ import annotations

import logging
from typing import NamedTuple

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from .const import INCLUDE_COVERS, INCLUDE_LIGHTS, INCLUDE_SWITCHES

__all__ = ["SceneSwitch"]

_LOGGER = logging.getLogger(__name__)


class SceneSwitchConfig(NamedTuple):
    """Discovered controller information."""

    scene_entity_id: str
    include_lights: bool
    include_switches: bool
    include_covers: bool


type SceneSwitchConfigEntry = ConfigEntry[SceneSwitchConfig]


async def async_setup_entry(hass: HomeAssistant, entry: SceneSwitchConfigEntry) -> bool:
    """Set up a config entry."""

    registry = er.async_get(hass)
    try:
        entity_id = er.async_validate_entity_id(registry, entry.options[CONF_ENTITY_ID])
    except vol.Invalid:
        # The entity is identified by an unknown entity registry ID
        _LOGGER.error(
            "Failed to setup scene_switch for unknown scene %s",
            entry.options[CONF_ENTITY_ID],
        )
        return False

    config = SceneSwitchConfig(
        scene_entity_id=entity_id,
        include_lights=entry.options[INCLUDE_LIGHTS],
        include_switches=entry.options[INCLUDE_SWITCHES],
        include_covers=entry.options[INCLUDE_COVERS],
    )
    entry.runtime_data = config

    async def async_registry_updated(
        event: Event[er.EventEntityRegistryUpdatedData],
    ) -> None:
        """Handle entity registry update."""
        data = event.data
        if data["action"] == "remove":
            # Remove our switch if the scene is removed
            await hass.config_entries.async_remove(entry.entry_id)

        if data["action"] != "update":
            return

        if "entity_id" in data["changes"]:
            # Entity_id changed, reload the config entry
            await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(
        async_track_entity_registry_updated_event(
            hass, entity_id, async_registry_updated
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, (Platform.SWITCH,))
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))
    return True


async def config_entry_update_listener(
    hass: HomeAssistant, entry: SceneSwitchConfigEntry
) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: SceneSwitchConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, (Platform.SWITCH,))
