# Switch for Home Assistant Scenes

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Helper to wrap home assistant scenes with a switch that tracks and controls the scene state

If you, like me, want to be able to link the state of Home Assitant Scenes to a button control panel, then you quickly run into the issue that Scenes in Home Assistant don't have a state that describes when they are active.
While you can cobble together some scripts to try and track the most recent scene activation, this falls flat when the state of entities in the scene are changed externally. E.g.:

* if someone turns on the lights with Alexa instead of by activating the scene.
* if multiple scenes overlap entities (e.g. an "All off" scene)
* if an automation temporarily makes one light brighter before restoring it to the normal level.

In these cases, I want my control panels to show whether the scene is currently active or not, even if the scene was established without actually activating the scene in HA.


## What it does

The integration adds a Helper, which allows you to wrap any Home Assistant Scene (_not_ scenes provided by other integrations like Lutron). When the state of the entities in the scene matches the scene state, the switch is enabled. When the entities don't match the scene state, the switch is disabled.

Turning the switch "On" activates the scene. There is no way to turn a scene "Off", so turning the switch Off also re-activates the scene.


# How to use it

In the Helpers page, choose Add New Helper, and select "Scene Switch" from the list.

Choose the Home Assistant Scebe you want to wrap with the switch. You can optionally choose to exclude some of the scene's entity types from the state comparison. Currently the switch only tracks the state of Lights, Switches and Covers. You can change these settings with the Options dialog.

This creates a switch entity named after the scene, which you can use on your dashboards, etc.


## How it works

The scene switch entity tracks all of the HA Scene's entities, and compares the state of the entity with the scene's definition whenever they change. This looks into the internals of the built-in HA Scene integration, but this has been working fine for me for years.

When the scene switch is asked to turn on or off, it activates the associated scene.
