"""Config flow for scene_switch integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
    wrapped_entity_config_entry_title,
)

from . import SceneSwitchConfig
from .const import DOMAIN, INCLUDE_COVERS, INCLUDE_LIGHTS, INCLUDE_SWITCHES

SCENE_DATA_PLATFORM = "homeassistant_scene"


def applicable_scene_entity_selector(
    hass: HomeAssistant,
) -> selector.EntitySelector:
    """Return an entity selector which allows selection of un-wrapped home assistant scenes."""

    # Excludes scenes that have already been wrapped
    entity_registry = er.async_get(hass)
    exclude_entities = [
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.domain == Platform.SWITCH
        and entity.platform == DOMAIN
        and entity.config_entry_id is not None
        and (entry := hass.config_entries.async_get_entry(entity.config_entry_id))
        and isinstance(entry.runtime_data, SceneSwitchConfig)
        and entry.runtime_data.scene_entity_id == entity.entity_id
    ]

    entity_selector_config = selector.EntitySelectorConfig(
        domain=Platform.SCENE, exclude_entities=exclude_entities
    )

    return selector.EntitySelector(entity_selector_config)


async def generate_config_schema(handler: SchemaCommonFlowHandler) -> vol.Schema:
    """Generate config schema."""
    return vol.Schema(
        {
            vol.Required(CONF_ENTITY_ID): applicable_scene_entity_selector(
                handler.parent_handler.hass,
            ),
            vol.Required(INCLUDE_LIGHTS, default=True): selector.BooleanSelector(
                selector.BooleanSelectorConfig(),
            ),
            vol.Required(INCLUDE_SWITCHES, default=True): selector.BooleanSelector(
                selector.BooleanSelectorConfig(),
            ),
            vol.Required(INCLUDE_COVERS, default=True): selector.BooleanSelector(
                selector.BooleanSelectorConfig(),
            ),
        }
    )


async def generate_options_schema(handler: SchemaCommonFlowHandler) -> vol.Schema:
    """Generate options schema."""
    return vol.Schema(
        {
            vol.Required(INCLUDE_LIGHTS, default=True): selector.BooleanSelector(
                selector.BooleanSelectorConfig(),
            ),
            vol.Required(INCLUDE_SWITCHES, default=True): selector.BooleanSelector(
                selector.BooleanSelectorConfig(),
            ),
            vol.Required(INCLUDE_COVERS, default=True): selector.BooleanSelector(
                selector.BooleanSelectorConfig(),
            ),
        }
    )


CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(generate_config_schema)
}

OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(generate_options_schema)
}


class GammaLightConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config flow for scene_switch."""

    VERSION = 2
    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return wrapped_entity_config_entry_title(self.hass, options[CONF_ENTITY_ID])
