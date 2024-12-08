"""Scene switch to wrap home assistant scene entities."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    CoverEntityFeature,
)
from homeassistant.components.homeassistant.scene import entities_in_scene
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_XY_COLOR,
    ColorMode,
)
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, SERVICE_TURN_ON
from homeassistant.core import (
    _LOGGER,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import SceneSwitchConfig, SceneSwitchConfigEntry

SCENE_DATA_PLATFORM = "homeassistant_scene"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SceneSwitchConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize scene switch config entry."""
    registry = er.async_get(hass)
    config = config_entry.runtime_data
    wrapped_scene = registry.async_get(config.scene_entity_id)
    if wrapped_scene is None:
        return

    async_add_entities(
        [
            SceneStateSwitch(
                config_entry.title,
                config,
                config_entry.entry_id,
                wrapped_scene.icon,
            )
        ]
    )


def _hs_compare(ch: int, cs: int, sh: int, ss: int) -> bool:
    return abs(ch - sh) < 5 and abs(cs - ss) < 2


def _xy_compare(cx: int, cy: int, sx: int, sy: int) -> bool:
    return abs(cx - sx) < 0.05 and abs(cy - sy) < 0.05


def _rgb_compare(cr: int, cg: int, cb: int, sr: int, sg: int, sb: int) -> bool:
    return abs(cr - sr) < 3 and abs(cg - sg) < 3 and abs(cb - sb) < 3


def _rgbw_compare(
    cr: int, cg: int, cb: int, cw: int, sr: int, sg: int, sb: int, sw: int
) -> bool:
    return (
        abs(cr - sr) < 3 and abs(cg - sg) < 3 and abs(cb - sb) < 3 and abs(cw - sw) < 3
    )


def _rgbww_compare(
    cr: int,
    cg: int,
    cb: int,
    cw: int,
    cww: int,
    sr: int,
    sg: int,
    sb: int,
    sw: int,
    sww: int,
) -> bool:
    return (
        abs(cr - sr) < 3
        and abs(cg - sg) < 3
        and abs(cb - sb) < 3
        and abs(cw - sw) < 3
        and abs(cww - sww) < 3
    )


simple_brightness_comparer = (
    ATTR_BRIGHTNESS,
    lambda curr, scene: abs(curr - scene) < 3.0,
)

mode_comparers = {
    ColorMode.BRIGHTNESS: [simple_brightness_comparer],
    ColorMode.COLOR_TEMP: [
        simple_brightness_comparer,
        (ATTR_COLOR_TEMP_KELVIN, lambda curr, scene: abs(curr - scene) < 50),
    ],
    ColorMode.HS: [
        simple_brightness_comparer,
        (ATTR_HS_COLOR, lambda curr, scene: _hs_compare(*curr, *scene)),
    ],
    ColorMode.XY: [
        simple_brightness_comparer,
        (ATTR_XY_COLOR, lambda curr, scene: _xy_compare(*curr, *scene)),
    ],
    ColorMode.RGB: [
        (ATTR_RGB_COLOR, lambda curr, scene: _rgb_compare(*curr, *scene)),
    ],
    ColorMode.RGBW: [
        (ATTR_RGBW_COLOR, lambda curr, scene: _rgbw_compare(*curr, *scene)),
    ],
    ColorMode.RGBWW: [
        (ATTR_RGBWW_COLOR, lambda curr, scene: _rgbww_compare(*curr, *scene)),
    ],
}


class SceneStateSwitch(SwitchEntity):
    """Representation of a Switch."""

    def __init__(
        self,
        sceneName: str,
        config: SceneSwitchConfig,
        unique_id: str,
        icon: str | None,
    ) -> None:
        """Initialize the switch."""
        self._attr_is_on = False
        self._config = config
        self._sceneName = sceneName
        self._attr_should_poll = False
        self._attr_icon = icon
        self._attr_unique_id = unique_id
        _LOGGER.info(
            "Creating scene state switch for scene %s", self._config.scene_entity_id
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def _async_state_changed_listener(
            event: Event[EventStateChangedData] | None = None,
        ) -> None:
            """Handle child updates."""
            self.async_schedule_update_ha_state(force_refresh=True)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                entities_in_scene(self.hass, self._config.scene_entity_id),
                _async_state_changed_listener,
            )
        )

    @property
    def name(self) -> str:
        """Return the name of the scene switch."""
        return self._sceneName + " Scene Switch"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        # Call the service to activate the attached scene
        self._attr_is_on = True
        await self.hass.services.async_call(
            "scene",
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self._config.scene_entity_id},
            blocking=False,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        # You can't turn a scene off, but we will try to re-apply the scene
        self._attr_is_on = False
        await self.hass.services.async_call(
            "scene",
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self._config.scene_entity_id},
            blocking=True,
        )
        self.async_schedule_update_ha_state(force_refresh=True)

    def _compare_simple_state(self, sceneState) -> bool:
        if sceneState.domain == "switch" and not self._config.include_switches:
            return True

        currentState = self.hass.states.get(sceneState.entity_id)

        return currentState is not None and currentState.state == sceneState.state

    def _compare_light_state(self, scene_state: State) -> bool:
        if not self._config.include_lights:
            return True
        _LOGGER.debug(
            "%s - Comparing light state for %s(%s)",
            self.name,
            scene_state.name,
            scene_state.entity_id,
        )
        current_state = self.hass.states.get(scene_state.entity_id)
        if current_state is None:
            return False
        if current_state.state != scene_state.state:
            _LOGGER.debug(
                "State does not match: %s != %s", current_state.state, scene_state.state
            )
            return False

        if current_state.state == "off":
            # Off is off, regardless of colour
            _LOGGER.debug("State matches off")
            return True

        if current_state.attributes.get(ATTR_COLOR_MODE) != scene_state.attributes.get(
            ATTR_COLOR_MODE
        ):
            return False

        current_mode = ColorMode(
            current_state.attributes.get(ATTR_COLOR_MODE, ColorMode.UNKNOWN)
        )

        comparers = mode_comparers.get(current_mode, [])

        if comparers is not None:
            for attr, comparer in comparers:
                _LOGGER.debug(
                    "Current %s: %d, Scene state: %d",
                    attr,
                    current_state.attributes.get(attr),
                    scene_state.attributes.get(attr),
                )
                if not comparer(
                    current_state.attributes.get(attr), scene_state.attributes.get(attr)
                ):
                    return False

        _LOGGER.debug("All supported colour mode attributes match")
        return True

    def _compare_cover_state(self, sceneState) -> bool:
        if not self._config.include_covers:
            return True
        _LOGGER.debug(
            "%s - Comparing cover state for %s(%s)",
            self.name,
            sceneState.name,
            sceneState.entity_id,
        )
        currentState = self.hass.states.get(sceneState.entity_id)
        if currentState is None:
            return False
        if currentState.state != sceneState.state:
            _LOGGER.debug(
                "Top-level state does not match: %s != %s",
                currentState.state,
                sceneState.state,
            )
            return False

        if currentState.state == "closed":
            # closed is closed, regardless of position
            _LOGGER.debug("State matches closed")
            return True

        # Compare relevant attributes
        supported_features = currentState.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        fuzzyAttrs = {
            CoverEntityFeature.SET_POSITION: ATTR_CURRENT_POSITION,
            CoverEntityFeature.SET_TILT_POSITION: ATTR_CURRENT_TILT_POSITION,
        }

        for key, attr in fuzzyAttrs.items():
            if supported_features & key > 0:
                _LOGGER.debug(
                    "%s Comparing %s for %s", self.name, attr, sceneState.name
                )
                _LOGGER.debug(
                    "Current %s: %d, Scene state: %d",
                    attr,
                    currentState.attributes.get(attr),
                    sceneState.attributes.get(attr),
                )
                if (
                    abs(
                        currentState.attributes.get(attr)
                        - sceneState.attributes.get(attr)
                    )
                    > 3
                ):
                    return False

        _LOGGER.debug("All supported cover position attributes match")
        return True

    def update(self) -> None:
        """Compare the current entity state to the scene state."""
        scenePlatform = self.hass.data[SCENE_DATA_PLATFORM]
        scene = scenePlatform.entities.get(self._config.scene_entity_id)

        comparers = {
            "light": self._compare_light_state,
            "cover": self._compare_cover_state,
        }

        for sceneState in scene.scene_config.states.values():
            comparer = comparers.get(sceneState.domain, self._compare_simple_state)
            if comparer is not None:
                if not comparer(sceneState):
                    self._attr_is_on = False
                    return

        self._attr_is_on = True
