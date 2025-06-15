# Maya Asset Publishing Tool - Backend Blueprint

## Database Models

### Publish Record Model

```python
import sqlite3
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class PublishRecord:
    """Model for storing publish metadata"""

    id: Optional[int] = None
    show_name: str = ""
    asset_type: str = ""  # "asset" or "shot"
    asset_id: str = ""
    task: str = ""
    version: int = 1
    file_path: str = ""
    file_size: int = 0
    artist: str = ""
    comments: str = ""
    published_at: Optional[datetime] = None
    maya_version: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'show_name': self.show_name,
            'asset_type': self.asset_type,
            'asset_id': self.asset_id,
            'task': self.task,
            'version': self.version,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'artist': self.artist,
            'comments': self.comments,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'maya_version': self.maya_version
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PublishRecord':
        """Create instance from database dictionary"""
        published_at = None
        if data.get('published_at'):
            published_at = datetime.fromisoformat(data['published_at'])

        return cls(
            id=data.get('id'),
            show_name=data.get('show_name', ''),
            asset_type=data.get('asset_type', ''),
            asset_id=data.get('asset_id', ''),
            task=data.get('task', ''),
            version=data.get('version', 1),
            file_path=data.get('file_path', ''),
            file_size=data.get('file_size', 0),
            artist=data.get('artist', ''),
            comments=data.get('comments', ''),
            published_at=published_at,
            maya_version=data.get('maya_version', '')
        )
```

### Environment Context Model

```python
@dataclass
class EnvironmentContext:
    """Model for Maya environment context"""

    show_name: str = ""
    current_scene: str = ""
    detected_asset_id: str = ""
    detected_asset_type: str = ""  # "asset" or "shot"
    detected_task: str = ""
    user_name: str = ""
    maya_version: str = ""
    scene_modified: bool = False

    @classmethod
    def from_maya_environment(cls) -> 'EnvironmentContext':
        """Extract context from current Maya environment"""
        import maya.cmds as cmds
        import os

        context = cls()
        context.show_name = os.environ.get('SHOW_NAME', '')
        context.current_scene = cmds.file(query=True, sceneName=True)
        context.user_name = os.environ.get('USER', os.environ.get('USERNAME', ''))
        context.maya_version = cmds.about(version=True)
        context.scene_modified = cmds.file(query=True, modified=True)

        # Auto-detect asset/shot from scene name or path
        if context.current_scene:
            context._parse_scene_context()

        return context

    def _parse_scene_context(self):
        """Parse asset/shot context from scene path"""
        # Implementation for smart scene name parsing
        import os
        scene_name = os.path.basename(self.current_scene)
        scene_dir = os.path.dirname(self.current_scene)

        # Simple parsing logic - can be enhanced
        if '/assets/' in scene_dir:
            self.detected_asset_type = 'asset'
        elif '/shots/' in scene_dir:
            self.detected_asset_type = 'shot'

        # Extract asset/shot ID from path or filename
        # This would need to be customized based on naming conventions
        pass
```

## Database Repository

### Publish Database Manager

```python
class PublishDatabase:
    """SQLite database manager for publish records"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS publishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    show_name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    artist TEXT NOT NULL,
                    comments TEXT DEFAULT '',
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    maya_version TEXT DEFAULT '',
                    UNIQUE(show_name, asset_type, asset_id, task, version)
                )
            ''')

            # Create indexes for faster queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_show_asset
                ON publishes(show_name, asset_type, asset_id)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_published_at
                ON publishes(published_at DESC)
            ''')

    def create_publish(self, record: PublishRecord) -> PublishRecord:
        """Create a new publish record"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO publishes
                (show_name, asset_type, asset_id, task, version, file_path,
                 file_size, artist, comments, published_at, maya_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.show_name, record.asset_type, record.asset_id,
                record.task, record.version, record.file_path,
                record.file_size, record.artist, record.comments,
                record.published_at or datetime.now(), record.maya_version
            ))

            record.id = cursor.lastrowid
            return record

    def get_publishes_by_show(self, show_name: str) -> List[PublishRecord]:
        """Get all publishes for a show"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM publishes
                WHERE show_name = ?
                ORDER BY asset_type, asset_id, task, version
            ''', (show_name,))

            return [PublishRecord.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_asset_versions(self, show_name: str, asset_type: str, asset_id: str, task: str) -> List[PublishRecord]:
        """Get all versions for a specific asset/task"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM publishes
                WHERE show_name = ? AND asset_type = ? AND asset_id = ? AND task = ?
                ORDER BY version DESC
            ''', (show_name, asset_type, asset_id, task))

            return [PublishRecord.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_next_version(self, show_name: str, asset_type: str, asset_id: str, task: str) -> int:
        """Get the next available version number"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT MAX(version) FROM publishes
                WHERE show_name = ? AND asset_type = ? AND asset_id = ? AND task = ?
            ''', (show_name, asset_type, asset_id, task))

            result = cursor.fetchone()
            return (result[0] or 0) + 1

    def get_recent_publishes(self, limit: int = 20) -> List[PublishRecord]:
        """Get recent publishes across all shows"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM publishes
                ORDER BY published_at DESC
                LIMIT ?
            ''', (limit,))

            return [PublishRecord.from_dict(dict(row)) for row in cursor.fetchall()]
```

## File System Manager

### Network Drive Publisher

```python
import os
import shutil
from pathlib import Path
from typing import Tuple

class NetworkDrivePublisher:
    """Handles file operations for network drive publishing"""

    def __init__(self, base_path: str = "S:/"):
        self.base_path = Path(base_path)

    def generate_publish_path(self, record: PublishRecord) -> Path:
        """Generate the full network path for a publish"""
        path = self.base_path / record.show_name

        if record.asset_type == "asset":
            path = path / "assets"
        elif record.asset_type == "shot":
            path = path / "shots"

        path = path / record.asset_id / record.task / f"v{record.version:03d}"

        # Generate filename
        filename = f"{record.asset_id}_{record.task}_v{record.version:03d}.ma"
        return path / filename

    def ensure_directory(self, file_path: Path) -> bool:
        """Ensure the directory structure exists"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create directory {file_path.parent}: {e}")
            return False

    def publish_file(self, source_path: str, target_path: Path) -> Tuple[bool, str]:
        """Copy/save Maya file to network location"""
        try:
            # Ensure target directory exists
            if not self.ensure_directory(target_path):
                return False, f"Failed to create directory: {target_path.parent}"

            # Save Maya file to target location
            import maya.cmds as cmds
            cmds.file(rename=str(target_path))
            cmds.file(save=True, type='mayaAscii')

            # Verify file was created
            if target_path.exists():
                return True, f"Successfully published to: {target_path}"
            else:
                return False, "File was not created at target location"

        except Exception as e:
            return False, f"Publish failed: {str(e)}"

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except:
            return 0

    def validate_network_access(self) -> Tuple[bool, str]:
        """Check if network drive is accessible"""
        try:
            if not self.base_path.exists():
                return False, f"Network path not accessible: {self.base_path}"

            # Try to create a test file
            test_file = self.base_path / ".maya_publish_test"
            test_file.touch()
            test_file.unlink()

            return True, "Network access verified"
        except Exception as e:
            return False, f"Network access failed: {str(e)}"
```

## Configuration Manager

### Show Configuration Handler

```python
import json
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class ShowConfig:
    """Configuration for a specific show"""

    show_name: str
    asset_tasks: List[str]
    shot_tasks: List[str]
    validation_rules: Dict[str, bool]
    naming_convention: Dict[str, str]
    network_path: str = "S:/"

    @classmethod
    def from_json(cls, json_path: Path) -> 'ShowConfig':
        """Load configuration from JSON file"""
        with open(json_path, 'r') as f:
            data = json.load(f)

        return cls(
            show_name=data.get('show_name', ''),
            asset_tasks=data.get('asset_tasks', []),
            shot_tasks=data.get('shot_tasks', []),
            validation_rules=data.get('validation_rules', {}),
            naming_convention=data.get('naming_convention', {}),
            network_path=data.get('network_path', 'S:/')
        )

    def to_json(self, json_path: Path):
        """Save configuration to JSON file"""
        data = {
            'show_name': self.show_name,
            'asset_tasks': self.asset_tasks,
            'shot_tasks': self.shot_tasks,
            'validation_rules': self.validation_rules,
            'naming_convention': self.naming_convention,
            'network_path': self.network_path
        }

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

class ConfigurationManager:
    """Manages show configurations"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def get_show_config(self, show_name: str) -> Optional[ShowConfig]:
        """Load configuration for a specific show"""
        config_file = self.config_dir / f"{show_name}.json"

        if config_file.exists():
            return ShowConfig.from_json(config_file)
        else:
            # Create default configuration
            return self.create_default_config(show_name)

    def create_default_config(self, show_name: str) -> ShowConfig:
        """Create default configuration for a new show"""
        config = ShowConfig(
            show_name=show_name,
            asset_tasks=["model", "texture", "shading", "rig"],
            shot_tasks=["previs", "layout", "anim", "lighting"],
            validation_rules={
                "naming_convention": True,
                "scene_cleanup": True,
                "required_comments": False
            },
            naming_convention={
                "asset_prefix": "AST_",
                "shot_prefix": "SHT_",
                "version_format": "v{version:03d}"
            }
        )

        # Save default configuration
        config_file = self.config_dir / f"{show_name}.json"
        config.to_json(config_file)

        return config

    def list_shows(self) -> List[str]:
        """List all configured shows"""
        config_files = self.config_dir.glob("*.json")
        return [f.stem for f in config_files]
```

## Maya Integration Layer

### Maya Scene Handler

```python
import maya.cmds as cmds
import maya.mel as mel
from typing import Dict, List, Tuple

class MayaSceneHandler:
    """Handles Maya-specific operations"""

    @staticmethod
    def get_scene_info() -> Dict[str, any]:
        """Get current Maya scene information"""
        return {
            'scene_name': cmds.file(query=True, sceneName=True),
            'scene_modified': cmds.file(query=True, modified=True),
            'maya_version': cmds.about(version=True),
            'current_unit': cmds.currentUnit(query=True, linear=True),
            'frame_range': [
                cmds.playbackOptions(query=True, minTime=True),
                cmds.playbackOptions(query=True, maxTime=True)
            ]
        }

    @staticmethod
    def prepare_scene_for_publish() -> List[str]:
        """Prepare scene for publishing and return any warnings"""
        warnings = []

        # Save current selection
        selection = cmds.ls(selection=True)

        try:
            # Clear selection
            cmds.select(clear=True)

            # Basic scene cleanup
            if cmds.ls(type='unknown'):
                warnings.append("Unknown nodes found in scene")

            # Check for empty groups
            empty_groups = [node for node in cmds.ls(type='transform')
                          if not cmds.listRelatives(node, children=True)]
            if empty_groups:
                warnings.append(f"Empty groups found: {len(empty_groups)}")

            # Check for unused shading nodes
            unused_shaders = mel.eval('MLdeleteUnused;')
            if unused_shaders:
                warnings.append("Unused shading nodes removed")

        finally:
            # Restore selection
            if selection:
                cmds.select(selection)

        return warnings

    @staticmethod
    def validate_scene() -> Tuple[bool, List[str], List[str]]:
        """Validate current scene and return errors/warnings"""
        errors = []
        warnings = []

        # Check if scene is saved
        if not cmds.file(query=True, sceneName=True):
            errors.append("Scene must be saved before publishing")

        # Check for references
        references = cmds.file(query=True, reference=True) or []
        if references:
            warnings.append(f"Scene contains {len(references)} references")

        # Check for missing textures
        file_nodes = cmds.ls(type='file')
        missing_textures = []
        for node in file_nodes:
            texture_path = cmds.getAttr(f"{node}.fileTextureName")
            if texture_path and not os.path.exists(texture_path):
                missing_textures.append(texture_path)

        if missing_textures:
            warnings.append(f"Missing textures: {len(missing_textures)}")

        # Check polygon count (configurable threshold)
        poly_count = len(cmds.ls(type='mesh'))
        if poly_count > 10000:  # Example threshold
            warnings.append(f"High polygon count: {poly_count}")

        return len(errors) == 0, errors, warnings
```

## UI Tree Model

### Publish Tree Data Model

```python
from PySide6 import QtCore, QtGui
from typing import Any, List, Optional

class PublishTreeItem:
    """Tree item for publish hierarchy"""

    def __init__(self, data: List[Any], parent: Optional['PublishTreeItem'] = None):
        self.item_data = data
        self.parent_item = parent
        self.child_items: List['PublishTreeItem'] = []
        self.item_type = ""  # "show", "category", "asset", "task", "version"
        self.publish_record: Optional[PublishRecord] = None

    def append_child(self, item: 'PublishTreeItem'):
        """Add a child item"""
        item.parent_item = self
        self.child_items.append(item)

    def child(self, row: int) -> Optional['PublishTreeItem']:
        """Get child at specific row"""
        if 0 <= row < len(self.child_items):
            return self.child_items[row]
        return None

    def child_count(self) -> int:
        """Get number of children"""
        return len(self.child_items)

    def column_count(self) -> int:
        """Get number of columns"""
        return len(self.item_data)

    def data(self, column: int) -> Any:
        """Get data for specific column"""
        if 0 <= column < len(self.item_data):
            return self.item_data[column]
        return None

    def parent(self) -> Optional['PublishTreeItem']:
        """Get parent item"""
        return self.parent_item

    def row(self) -> int:
        """Get row number in parent"""
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

class PublishTreeModel(QtCore.QAbstractItemModel):
    """Tree model for publish browser"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_item = PublishTreeItem(["Name", "Version", "Artist", "Date"])
        self.database = None
        self.current_show = ""

    def set_database(self, database: PublishDatabase):
        """Set database connection"""
        self.database = database

    def load_show_data(self, show_name: str):
        """Load data for a specific show"""
        if not self.database:
            return

        self.beginResetModel()

        # Clear existing data
        self.root_item = PublishTreeItem(["Name", "Version", "Artist", "Date"])
        self.current_show = show_name

        # Load publishes from database
        publishes = self.database.get_publishes_by_show(show_name)

        # Organize data hierarchically
        show_item = PublishTreeItem([show_name, "", "", ""], self.root_item)
        show_item.item_type = "show"
        self.root_item.append_child(show_item)

        # Group by asset type
        assets_item = PublishTreeItem(["Assets", "", "", ""], show_item)
        shots_item = PublishTreeItem(["Shots", "", "", ""], show_item)
        assets_item.item_type = "category"
        shots_item.item_type = "category"
        show_item.append_child(assets_item)
        show_item.append_child(shots_item)

        # Organize publishes by asset/shot
        asset_groups = {}
        for publish in publishes:
            parent_item = assets_item if publish.asset_type == "asset" else shots_item

            # Create asset/shot item if not exists
            asset_key = publish.asset_id
            if asset_key not in asset_groups:
                asset_item = PublishTreeItem([publish.asset_id, "", "", ""], parent_item)
                asset_item.item_type = "asset"
                parent_item.append_child(asset_item)
                asset_groups[asset_key] = {}

                # Create task items
                for task in set(p.task for p in publishes if p.asset_id == asset_key):
                    task_item = PublishTreeItem([task, "", "", ""], asset_item)
                    task_item.item_type = "task"
                    asset_item.append_child(task_item)
                    asset_groups[asset_key][task] = task_item

            # Add version item
            task_item = asset_groups[asset_key][publish.task]
            version_item = PublishTreeItem([
                f"v{publish.version:03d}",
                str(publish.version),
                publish.artist,
                publish.published_at.strftime("%Y-%m-%d %H:%M") if publish.published_at else ""
            ], task_item)
            version_item.item_type = "version"
            version_item.publish_record = publish
            task_item.append_child(version_item)

        self.endResetModel()

    # Standard QAbstractItemModel methods
    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return self.root_item.column_count()

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            return item.data(index.column())
        elif role == QtCore.Qt.UserRole:
            return item.publish_record

        return None

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation,
                   role: int = QtCore.Qt.DisplayRole) -> Any:
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.root_item.data(section)
        return None

    def index(self, row: int, column: int,
              parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_item = parent.internalPointer() if parent.isValid() else self.root_item
        child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)
        return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        parent_item = parent.internalPointer() if parent.isValid() else self.root_item
        return parent_item.child_count()
```

## Validation Framework

### Scene Validation System

```python
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict

class ValidationRule(ABC):
    """Base class for validation rules"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run validation and return (passed, errors, warnings)"""
        pass

class NamingConventionRule(ValidationRule):
    """Validate scene naming conventions"""

    def __init__(self):
        super().__init__("Naming Convention", "Check asset/shot naming standards")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []

        # Check current scene name
        scene_name = cmds.file(query=True, sceneName=True, shortName=True)
        if not scene_name:
            errors.append("Scene must be saved with a proper name")
            return False, errors, warnings

        # Check naming pattern (customize based on studio standards)
        if not self._check_naming_pattern(scene_name):
            warnings.append(f"Scene name may not follow naming convention: {scene_name}")

        return len(errors) == 0, errors, warnings

    def _check_naming_pattern(self, name: str) -> bool:
        """Check if name follows expected pattern"""
        # Simple example - customize for your studio
        return "_" in name and not name.startswith("untitled")

class SceneCleanupRule(ValidationRule):
    """Validate scene cleanliness"""

    def __init__(self):
        super().__init__("Scene Cleanup", "Check for unused nodes and cleanup issues")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []

        # Check for unknown nodes
        unknown_nodes = cmds.ls(type='unknown')
        if unknown_nodes:
            warnings.append(f"Unknown nodes found: {len(unknown_nodes)}")

        # Check for empty groups
        empty_groups = [node for node in cmds.ls(type='transform')
                       if not cmds.listRelatives(node, children=True)]
        if empty_groups:
            warnings.append(f"Empty groups found: {len(empty_groups)}")

        # Check for unused materials
        all_materials = cmds.ls(materials=True)
        used_materials = set()
        for shape in cmds.ls(type='mesh'):
            shading_engines = cmds.listConnections(shape, type='shadingEngine')
            if shading_engines:
                for sg in shading_engines:
                    materials = cmds.listConnections(f"{sg}.surfaceShader")
                    if materials:
                        used_materials.update(materials)

        unused_materials = [mat for mat in all_materials if mat not in used_materials
                           and not mat.startswith('lambert1')]
        if unused_materials:
            warnings.append(f"Unused materials found: {len(unused_materials)}")

        return True, errors, warnings

class ValidationManager:
    """Manages validation rules and execution"""

    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.setup_default_rules()

    def setup_default_rules(self):
        """Setup default validation rules"""
        self.rules = [
            NamingConventionRule(),
            SceneCleanupRule()
        ]

    def add_rule(self, rule: ValidationRule):
        """Add a custom validation rule"""
        self.rules.append(rule)

    def run_validation(self, enabled_rules: List[str] = None) -> Dict[str, Tuple[bool, List[str], List[str]]]:
        """Run validation rules and return results"""
        results = {}

        for rule in self.rules:
            if not rule.enabled:
                continue

            if enabled_rules and rule.name not in enabled_rules:
                continue

            try:
                passed, errors, warnings = rule.validate()
                results[rule.name] = (passed, errors, warnings)
            except Exception as e:
                results[rule.name] = (False, [f"Validation error: {str(e)}"], [])

        return results

    def get_overall_status(self, results: Dict[str, Tuple[bool, List[str], List[str]]]) -> Tuple[bool, int, int]:
        """Get overall validation status"""
        total_errors = 0
        total_warnings = 0
        all_passed = True

        for passed, errors, warnings in results.values():
            if not passed:
                all_passed = False
            total_errors += len(errors)
            total_warnings += len(warnings)

        return all_passed, total_errors, total_warnings
```
