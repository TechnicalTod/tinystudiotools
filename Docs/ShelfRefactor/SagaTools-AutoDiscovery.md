# Saga Tools Auto-Discovery System

## Overview

The Saga Tools Auto-Discovery System enables the automatic discovery and registration of Maya tools within your codebase. This eliminates the need for manual registration of tools in the `buildSagaShelf.py` script, making it easier to add new tools or modify existing ones.

## How It Works

The system uses metadata embedded in Python docstrings to discover and register tools. This metadata is in the form of a JSON block marked with the `SAGA_TOOL_CONFIG:` tag.

### Key Components

1. **autoDiscovery.py** - Core module that scans for tools and builds the registry
2. **ToolRegistry** - Class that stores discovered tools and provides access methods
3. **SAGA_TOOL_CONFIG** - JSON metadata format for describing tools

## Adding Metadata to Your Tools

To make your tools discoverable, add `SAGA_TOOL_CONFIG` metadata to both your module and functions:

### Module Metadata

```python
"""
My awesome module description

SAGA_TOOL_CONFIG:
{
    "category": "utility",
    "label": "My Tools",
    "tooltip": "Collection of useful tools"
}
"""

import maya.cmds as mc
# rest of your module
```

### Function Metadata

```python
def my_tool():
    """
    My awesome tool description

    SAGA_TOOL_CONFIG:
    {
        "label": "My Tool",
        "tooltip": "Does something cool",
        "icon": "myTool.png",
        "category": "rigging",
        "entry_point": "my_tool",
        "shelf_button": true,
        "menu_group": "My Tools"
    }
    """
    # tool implementation
```

## Metadata Properties

| Property     | Description               | Required | Default       |
| ------------ | ------------------------- | -------- | ------------- |
| label        | Display name for the tool | Yes      | -             |
| tooltip      | Tooltip text              | Yes      | -             |
| icon         | Icon file name            | No       | -             |
| category     | Tool category             | Yes      | -             |
| entry_point  | Function name to call     | No       | Function name |
| shelf_button | Add to shelf              | No       | false         |
| menu_group   | Menu group name           | No       | -             |

## Helper Tools

We provide two helper scripts to ease the transition:

1. **updateSagaShelf.py** - Updates the existing `buildSagaShelf.py` to use the auto-discovery system
2. **add_tool_metadata.py** - Interactive tool to help add metadata to your scripts

## Examples

### Basic Tool

```python
def centerPivot():
    """
    Center pivot on selected objects

    SAGA_TOOL_CONFIG:
    {
        "label": "Center Pivot",
        "tooltip": "Center pivot on selected objects",
        "icon": "centerPivot.png",
        "category": "transform",
        "shelf_button": true
    }
    """
    mc.CenterPivot()
```

### Tool with UI

```python
def launch():
    """
    Launch the asset directory creation UI

    SAGA_TOOL_CONFIG:
    {
        "label": "Create Asset Directories",
        "tooltip": "Create standard asset directory structure",
        "icon": "createAssetDir.png",
        "category": "asset",
        "shelf_button": true,
        "menu_group": "Utilities"
    }
    """
    global win
    win = MainWindow()
    win.show()
```

## Migration Guide

1. Run `updateSagaShelf.py` to update your buildSagaShelf.py file to use auto-discovery
2. Use `add_tool_metadata.py` to add metadata to your existing tools
3. Test by loading Maya and verifying the shelf loads correctly

## Benefits

- **Decentralized Configuration**: Tool definitions live with the code, not in a central file
- **Self-Documentation**: Metadata provides useful documentation for tools
- **Easier Maintenance**: No need to update buildSagaShelf.py when adding/changing tools
- **Automatic Organization**: Tools are automatically categorized and grouped
