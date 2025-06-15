# Maya Shelf Button System - Technical Blueprint

## Auto-Discovery Module

### SagaToolDiscovery Class

```python
class SagaToolDiscovery:
    """Auto-discover Maya tools from script directories"""

    def __init__(self, scripts_path: str):
        self.scripts_path = Path(scripts_path)
        self.discovered_tools = {}
        self.categories = {}

    def discover_all_tools(self):
        """Scan all tool directories and discover tools"""
        print("🔍 Discovering SAGA tools...")

        # Look for directories ending with 'Tools'
        for dir_path in self.scripts_path.iterdir():
            if (dir_path.is_dir() and
                dir_path.name.endswith('Tools') and
                not dir_path.name.startswith('_')):

                category = dir_path.name
                print(f"📁 Scanning {category}...")
                self._scan_category(category, dir_path)

        # Also scan genTools (special case)
        gen_tools_path = self.scripts_path / 'genTools'
        if gen_tools_path.exists():
            print(f"📁 Scanning genTools...")
            self._scan_category('genTools', gen_tools_path)

        print(f"✅ Discovered {len(self.discovered_tools)} tools across {len(self.categories)} categories")
        return self.discovered_tools

    def _scan_category(self, category: str, dir_path: Path):
        """Scan a single category directory"""
        if category not in self.categories:
            self.categories[category] = []

        for py_file in dir_path.glob('*.py'):
            if py_file.name.startswith('_'):
                continue

            try:
                self._scan_python_file(category, py_file)
            except Exception as e:
                print(f"⚠️  Error scanning {py_file}: {e}")

    def _scan_python_file(self, category: str, py_file: Path):
        """Scan a Python file for tool configurations"""
        module_name = f"{category}.{py_file.stem}"

        try:
            # Read the file content to look for SAGA_TOOL_CONFIG
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for SAGA_TOOL_CONFIG in docstrings
            configs = self._extract_tool_configs(content)

            if configs:
                # Import the module to get actual functions
                module = importlib.import_module(module_name)

                for config in configs:
                    entry_point = config.get('entry_point', 'launch')

                    if hasattr(module, entry_point):
                        func = getattr(module, entry_point)
                        tool_id = f"{category}.{py_file.stem}.{entry_point}"

                        self.discovered_tools[tool_id] = {
                            'function': func,
                            'module_name': module_name,
                            'file_path': str(py_file),
                            'category': category,
                            'config': config
                        }

                        self.categories[category].append(tool_id)
                        print(f"  ✓ Found: {config.get('label', tool_id)}")

        except ImportError as e:
            print(f"⚠️  Could not import {module_name}: {e}")
        except Exception as e:
            print(f"⚠️  Error processing {py_file}: {e}")

    def _extract_tool_configs(self, file_content: str) -> List[Dict]:
        """Extract SAGA_TOOL_CONFIG from file content"""
        configs = []

        # Look for SAGA_TOOL_CONFIG: followed by JSON
        pattern = r'SAGA_TOOL_CONFIG:\s*(\{[^}]*\})'
        matches = re.findall(pattern, file_content, re.DOTALL)

        for match in matches:
            try:
                # Clean up the JSON (remove comments, fix quotes)
                cleaned_json = self._clean_json_string(match)
                config = json.loads(cleaned_json)
                configs.append(config)
            except json.JSONDecodeError as e:
                print(f"⚠️  Invalid JSON in SAGA_TOOL_CONFIG: {e}")

        return configs

    def _clean_json_string(self, json_str: str) -> str:
        """Clean up JSON string for parsing"""
        # Remove Python-style comments
        lines = json_str.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove comments after //
            if '//' in line:
                line = line[:line.index('//')]
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def get_tools_by_category(self, category: str) -> List[str]:
        """Get all tool IDs for a category"""
        return self.categories.get(category, [])

    def get_shelf_tools(self) -> List[Dict]:
        """Get tools that should appear on the shelf"""
        shelf_tools = []

        for tool_id, tool_data in self.discovered_tools.items():
            config = tool_data['config']
            if config.get('shelf_button', True):  # Default to True
                shelf_tools.append({
                    'id': tool_id,
                    'function': tool_data['function'],
                    'config': config,
                    'category': tool_data['category']
                })

        return shelf_tools
```

## Shelf Builder Module

### Main Shelf Builder Function

```python
def makeShelfAndButtons():
    """Build shelf automatically from discovered tools"""

    # Discover all tools
    discovery = SagaToolDiscovery(mayaFilePaths.mayaScriptsPath)
    discovery.discover_all_tools()

    # Create shelf
    iconPath = mayaFilePaths.mayaShelfIconPath
    shelf = shelfCreate.ShelfTool('SAGA_SHELF', iconPath)
    shelf.createShelf()

    # Get tools that should appear on shelf
    shelf_tools = discovery.get_shelf_tools()

    # Group tools by category
    categorized_tools = {}
    for tool in shelf_tools:
        category = tool['category']
        if category not in categorized_tools:
            categorized_tools[category] = []
        categorized_tools[category].append(tool)

    # Add spacer
    safe_create_button(shelf, lambda: shelf.addShelfSpacer(iconImage='spacer.png'))

    # Create buttons for each category
    for category, tools in categorized_tools.items():
        if len(tools) == 1:
            # Single tool - create simple button
            tool = tools[0]
            config = tool['config']
            button = safe_create_button(shelf, lambda t=tool: shelf.shelfButton(
                t['function'],
                config.get('icon', 'default.png'),
                config.get('tooltip', config.get('label', 'Tool'))
            ))

        else:
            # Multiple tools - create group button with menu
            category_config = get_category_config(category)
            primary_tool = get_primary_tool(tools)

            button = safe_create_button(shelf, lambda: shelf.shelfButton(
                primary_tool['function'] if primary_tool else lambda: None,
                category_config.get('icon', f'{category.lower()}.png'),
                category_config.get('tooltip', f'{category} Tools')
            ))

            if button:
                # Add menu items for each tool
                for tool in tools:
                    config = tool['config']
                    shelf.addMenu(button, config.get('label', 'Tool'), tool['function'])

    print("🎉 Saga shelf built successfully!")
```

### Helper Functions

```python
def safe_create_button(shelf, create_func):
    """Safely create shelf button with error handling"""
    try:
        return create_func()
    except Exception as e:
        print(f"⚠️  Failed to create shelf button: {e}")
        return None

def get_category_config(category: str) -> dict:
    """Get configuration for a tool category"""
    configs = {
        'assetTools': {'icon': 'asset.png', 'tooltip': 'Asset Tools'},
        'modellingTools': {'icon': 'modelling.png', 'tooltip': 'Modelling Tools'},
        'riggingTools': {'icon': 'rigging.png', 'tooltip': 'Rigging Tools'},
        'shadingTools': {'icon': 'shaderTools.png', 'tooltip': 'Shading Tools'},
        'textureTools': {'icon': 'textureTools.png', 'tooltip': 'Texture Tools'},
        'unrealTools': {'icon': 'unrealTools.png', 'tooltip': 'Unreal Tools'},
        'techvisTools': {'icon': 'techvis.png', 'tooltip': 'Techvis Tools'},
        'genTools': {'icon': 'genTools.png', 'tooltip': 'General Tools'},
        'cameraTools': {'icon': 'cameraTools.png', 'tooltip': 'Camera Tools'}
    }
    return configs.get(category, {'icon': 'default.png', 'tooltip': f'{category} Tools'})

def get_primary_tool(tools: list) -> dict:
    """Get the primary tool for a category (first one marked as primary or first tool)"""
    for tool in tools:
        if tool['config'].get('primary', False):
            return tool
    return tools[0] if tools else None
```

## Tool Metadata Format

### Example Tool with Metadata

```python
"""
SAGA_TOOL_CONFIG:
{
    "label": "Cubinate",
    "tooltip": "Convert selected objects to cubes",
    "icon": "cubinate.png",
    "category": "modelling",
    "entry_point": "cubinate",
    "shelf_button": true,
    "menu_group": "Tools"
}
"""
import maya.cmds as mc

def cubinate(objects=None, doTransfer=True, deleteSourceMesh=False, keepHistory=True, smoothCube=0, preScale=0, subdivisionsX=3, subdivisionsY=3, subdivisionsZ=3):
    """
    Convert selected objects to cube representations

    SAGA_TOOL_CONFIG:
    {
        "label": "Cubinate Selected",
        "tooltip": "Convert selected objects to cubes for optimization"
    }
    """
    # Implementation code here
```

### Example Asset Tool with Metadata

```python
"""
SAGA_TOOL_CONFIG:
{
    "label": "Create Asset Directories",
    "tooltip": "Create standardized asset directory structure",
    "icon": "createAssetDir.png",
    "category": "asset",
    "entry_point": "launch",
    "primary": true
}
"""
import os
import subprocess
from genTools.genUtils import warningPopup
from PySide6 import QtGui, QtWidgets, QtCore
import mayaFilePaths
import maya.OpenMayaUI as OMUI
import shiboken2

class MainWindow(QtWidgets.QWidget):
    # Implementation code here

def launch():
    """
    Launch the Create Asset Directory UI

    SAGA_TOOL_CONFIG:
    {
        "label": "Create Asset Directories",
        "tooltip": "Create standardized asset directory structure",
        "icon": "createAssetDir.png",
        "category": "asset",
        "shelf_button": true
    }
    """
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()
```

## Helper Module Examples

### MEL Command Wrappers

```python
"""
MEL command wrapper utilities for Maya
"""

import maya.mel as mm

def movePivotBA():
    """
    Move pivot from B to A

    SAGA_TOOL_CONFIG:
    {
        "label": "Move Pivot B to A",
        "tooltip": "Move pivot from object B to object A",
        "icon": "movePivotBA.png",
        "category": "transform"
    }
    """
    mm.eval('movePivotBA();')

def movePivotToOrigin():
    """
    Move pivot to origin

    SAGA_TOOL_CONFIG:
    {
        "label": "Move Pivot To Origin",
        "tooltip": "Move pivot to world origin",
        "icon": "movePivotToOrigin.png",
        "category": "transform"
    }
    """
    mm.eval('movePivotToOrigin();')

def selectNthEdge():
    """
    Select every Nth edge in edge ring

    SAGA_TOOL_CONFIG:
    {
        "label": "Select Nth Edge",
        "tooltip": "Select every other edge in an edge ring",
        "icon": "selectNthEdge.png",
        "category": "selection"
    }
    """
    mm.eval('polySelectEdgesEveryN "edgeRing" 2;')
```

### UI Utilities

```python
"""
UI utility functions for Maya
"""

import maya.cmds as mc
import maya.mel as mm

def openUVEditor():
    """
    Open UV Editor panel

    SAGA_TOOL_CONFIG:
    {
        "label": "UV Editor",
        "tooltip": "Open the UV Editor panel",
        "icon": "UVTools.png",
        "category": "uv",
        "primary": true
    }
    """
    for panel in mc.getPanel(sty="polyTexturePlacementPanel") or []:
        mc.scriptedPanel(panel, e=True, to=True)

def toggleSelectByAngle():
    """
    Toggle select faces by angle constraint

    SAGA_TOOL_CONFIG:
    {
        "label": "Select by Angle",
        "tooltip": "Toggle selection by angle constraint",
        "icon": "selectByAngle.png",
        "category": "selection"
    }
    """
    if not mc.polySelectConstraint(query=True, ap=True) is True:
        mc.polySelectConstraint(ap=True, at=38)
    else:
        mc.polySelectConstraint(ap=False, at=0)
```

## Data Flow

### Tool Discovery Process

1. **Initialization**:

   - `SagaToolDiscovery` is initialized with the scripts path
   - The `discover_all_tools()` method is called

2. **Directory Scanning**:

   - All directories ending with "Tools" are identified
   - Each directory is processed as a tool category

3. **File Processing**:

   - Python files in each directory are read
   - Docstrings are parsed for `SAGA_TOOL_CONFIG` blocks
   - JSON is extracted and parsed

4. **Tool Registration**:
   - Tools with valid metadata are imported
   - Function references are stored in the discovery object
   - Tools are organized by category

### Shelf Building Process

1. **Tool Collection**:

   - `get_shelf_tools()` retrieves all tools marked for shelf display
   - Tools are grouped by category

2. **Button Creation**:

   - For single tools, direct buttons are created
   - For multiple tools in a category, a group button with menu is created
   - Primary tools are used as the main action for group buttons

3. **Menu Population**:
   - For group buttons, menu items are created for each tool
   - Menu items use the tool's label and function reference

## Error Handling

### Discovery Errors

- Import errors are caught and logged
- JSON parsing errors are caught and logged
- File reading errors are caught and logged
- Missing entry points are detected and skipped

### Shelf Building Errors

- Button creation errors are caught and logged
- Menu creation errors are caught and logged
- Function execution errors are caught and logged

## Performance Considerations

### Lazy Loading

- Modules are only imported when their tools are discovered
- Functions are only called when buttons are clicked

### Caching

- Discovery results are cached
- Tool functions are stored as references

### Error Prevention

- JSON validation prevents malformed metadata
- Default values are provided for missing fields
- Error handling prevents cascading failures
