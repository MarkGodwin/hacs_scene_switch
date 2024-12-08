# Home Assistant Scene Switch

Helper to wrap home assistant scenes with a switch that tracks and controls the scene state.

# How to use it

In the Helpers page, choose Add New Helper, and select "Scene Switch" from the list.

Choose the Home Assistant Scebe you want to wrap with the switch. You can optionally choose to exclude some of the scene's entity types from the state comparison. Currently the switch only tracks the state of Lights, Switches and Covers. You can change these settings with the Options dialog.

This creates a switch entity named after the scene, which you can use on your dashboards, etc.

