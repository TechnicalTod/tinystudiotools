# TunnelUI Asset Browser - Backend Blueprint

## Architecture Overview

The refactored TunnelUI will follow a layered architecture pattern with clear separation of concerns:

- **Presentation Layer**: Qt-based UI components and dialogs
- **Service Layer**: Business logic for asset management and search
- **Data Access Layer**: Repositories for metadata and file system operations
- **Configuration Layer**: Settings management and environment detection
- **Infrastructure Layer**: Logging, error handling, and utility functions

## Configuration System

### Configuration Model

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json
import os

@dataclass
class AssetLibraryConfig:
    """Configuration for asset library paths and settings"""

    # Core paths
    metadata_path: str = r"L:\megaScansMetadata"
    assets_path: str = r"M:\Zips"

    # UI settings
    thumbnail_size: int = 150
    grid_spacing: int = 10
    window_width: int = 900
    window_height: int = 800

    # Performance settings
    max_concurrent_loads: int = 10
    cache_size: int = 100

    # Maya integration
    maya_mode: bool = True
    stylesheet_path: Optional[str] = None

    # Advanced settings
    debug_mode: bool = False
    log_level: str = "INFO"

@dataclass
class AppEnvironment:
    """Runtime environment detection and configuration"""

    is_maya: bool = field(default=False)
    maya_version: Optional[str] = field(default=None)
    app_root: Path = field(default_factory=lambda: Path(__file__).parent)
    config_path: Path = field(default=None)

    def __post_init__(self):
        if self.config_path is None:
            self.config_path = self.app_root / "config" / "tunnel_config.json"
```

### Configuration Manager

```python
class ConfigurationManager:
    """Manages application configuration with fallbacks and validation"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[AssetLibraryConfig] = None
        self._environment: Optional[AppEnvironment] = None

    def load_config(self) -> AssetLibraryConfig:
        """Load configuration with fallbacks to defaults"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                self._config = AssetLibraryConfig(**data)
            else:
                self._config = AssetLibraryConfig()
                self.save_config()  # Create default config file
        except Exception as e:
            logging.warning(f"Failed to load config: {e}. Using defaults.")
            self._config = AssetLibraryConfig()

        return self._config

    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config.__dict__, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False

    def get_environment(self) -> AppEnvironment:
        """Detect and return current runtime environment"""
        if self._environment is None:
            self._environment = self._detect_environment()
        return self._environment

    def _detect_environment(self) -> AppEnvironment:
        """Detect Maya vs standalone environment"""
        try:
            import maya.cmds as cmds
            maya_version = cmds.about(version=True)
            return AppEnvironment(is_maya=True, maya_version=maya_version)
        except ImportError:
            return AppEnvironment(is_maya=False)

    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        # Try to find config relative to script location
        script_dir = Path(__file__).parent
        return script_dir / "config" / "tunnel_config.json"
```

## Data Access Layer

### Asset Metadata Repository

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
import json
import os
from pathlib import Path

class AssetMetadataRepository(ABC):
    """Abstract base class for asset metadata access"""

    @abstractmethod
    def load_inverted_index(self) -> Dict[str, Dict[str, str]]:
        """Load the inverted index for asset search"""
        pass

    @abstractmethod
    def load_asset_groupings(self) -> Dict[str, List[str]]:
        """Load asset groupings by category"""
        pass

    @abstractmethod
    def load_zip_index(self) -> Dict[str, str]:
        """Load zip file index for asset importing"""
        pass

    @abstractmethod
    def get_asset_image_path(self, asset_id: str, category: str, thumbnail: bool = True) -> Optional[Path]:
        """Get path to asset image file"""
        pass

class FileSystemMetadataRepository(AssetMetadataRepository):
    """File system based implementation of asset metadata repository"""

    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        self._inverted_index: Optional[Dict] = None
        self._asset_groupings: Optional[Dict] = None
        self._zip_index: Optional[Dict] = None

    def load_inverted_index(self) -> Dict[str, Dict[str, str]]:
        """Load inverted index from JSON file"""
        if self._inverted_index is None:
            try:
                index_path = self.metadata_path / "inverted_index_combined.json"
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._inverted_index = data.get("index", {})
            except Exception as e:
                logging.error(f"Failed to load inverted index: {e}")
                self._inverted_index = {}

        return self._inverted_index

    def load_asset_groupings(self) -> Dict[str, List[str]]:
        """Load asset groupings from JSON file"""
        if self._asset_groupings is None:
            try:
                index_path = self.metadata_path / "inverted_index_combined.json"
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._asset_groupings = data.get("AssetGrouping", {})
            except Exception as e:
                logging.error(f"Failed to load asset groupings: {e}")
                self._asset_groupings = {}

        return self._asset_groupings

    def load_zip_index(self) -> Dict[str, str]:
        """Load zip index from JSON file"""
        if self._zip_index is None:
            try:
                zip_index_path = self.metadata_path / "zip_index.json"
                with open(zip_index_path, 'r') as f:
                    self._zip_index = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load zip index: {e}")
                self._zip_index = {}

        return self._zip_index

    def get_asset_image_path(self, asset_id: str, category: str, thumbnail: bool = True) -> Optional[Path]:
        """Get path to asset image file"""
        suffix = "_thumbnail" if thumbnail else ""
        filename = f"{asset_id}_Preview{suffix}.png"
        image_path = self.metadata_path / category / filename

        return image_path if image_path.exists() else None

    def refresh_cache(self):
        """Clear cached data to force reload"""
        self._inverted_index = None
        self._asset_groupings = None
        self._zip_index = None
```

### Asset Import Repository

```python
class AssetImportRepository:
    """Handles asset import operations"""

    def __init__(self, assets_path: str):
        self.assets_path = Path(assets_path)

    def get_asset_zip_path(self, asset_id: str, zip_filename: str) -> Optional[Path]:
        """Get full path to asset zip file"""
        zip_path = self.assets_path / zip_filename
        return zip_path if zip_path.exists() else None

    def validate_asset_exists(self, asset_id: str, zip_filename: str) -> bool:
        """Check if asset zip file exists"""
        return self.get_asset_zip_path(asset_id, zip_filename) is not None

    def get_asset_info(self, asset_id: str, zip_filename: str) -> Dict[str, Any]:
        """Get asset information for import"""
        zip_path = self.get_asset_zip_path(asset_id, zip_filename)
        if not zip_path:
            return {}

        return {
            "asset_id": asset_id,
            "zip_filename": zip_filename,
            "zip_path": str(zip_path),
            "file_size": zip_path.stat().st_size if zip_path.exists() else 0,
            "exists": zip_path.exists()
        }
```

## Service Layer

### Asset Search Service

```python
class AssetSearchService:
    """Business logic for asset searching and filtering"""

    def __init__(self, metadata_repo: AssetMetadataRepository):
        self.metadata_repo = metadata_repo
        self._search_cache: Dict[str, List[str]] = {}

    def search_assets(self, query: str, category: Optional[str] = None) -> List[str]:
        """Search assets by query string with optional category filter"""
        if not query.strip():
            return self.get_all_assets_in_category(category) if category else []

        # Check cache first
        cache_key = f"{query.lower()}:{category or 'all'}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        # Perform search
        inverted_index = self.metadata_repo.load_inverted_index()
        search_terms = query.lower().split()
        matching_assets = set()

        for term in search_terms:
            for index_key, assets_dict in inverted_index.items():
                if term in index_key.lower():
                    matching_assets.update(assets_dict.keys())

        # Filter by category if specified
        if category:
            category_assets = set(self.get_all_assets_in_category(category))
            matching_assets = matching_assets.intersection(category_assets)

        # Sort by asset name
        result = sorted(matching_assets, key=lambda aid: self._get_asset_name(aid, inverted_index))

        # Cache result
        self._search_cache[cache_key] = result
        return result

    def get_all_assets_in_category(self, category: str) -> List[str]:
        """Get all assets in a specific category"""
        asset_groupings = self.metadata_repo.load_asset_groupings()
        return sorted(asset_groupings.get(category, []))

    def get_asset_name(self, asset_id: str) -> str:
        """Get display name for an asset"""
        inverted_index = self.metadata_repo.load_inverted_index()
        return self._get_asset_name(asset_id, inverted_index)

    def _get_asset_name(self, asset_id: str, inverted_index: Dict) -> str:
        """Helper to get asset name from inverted index"""
        for assets_dict in inverted_index.values():
            if asset_id in assets_dict:
                return assets_dict[asset_id]
        return asset_id

    def clear_cache(self):
        """Clear search cache"""
        self._search_cache.clear()
```

### Asset Management Service

```python
class AssetManagementService:
    """High-level asset management operations"""

    def __init__(self, metadata_repo: AssetMetadataRepository, import_repo: AssetImportRepository):
        self.metadata_repo = metadata_repo
        self.import_repo = import_repo
        self.search_service = AssetSearchService(metadata_repo)

    def get_categories(self) -> List[str]:
        """Get list of available asset categories"""
        asset_groupings = self.metadata_repo.load_asset_groupings()
        return list(asset_groupings.keys())

    def get_category_display_name(self, category: str) -> str:
        """Get display name for category"""
        display_names = {
            "3d": "3D Assets",
            "3dplant": "Plants",
            "atlas": "Atlas",
            "decals": "Decals",
            "brush": "Brushes",
            "surface": "Surfaces"
        }
        return display_names.get(category, category.title())

    def get_asset_image_path(self, asset_id: str, category: str, thumbnail: bool = True) -> Optional[Path]:
        """Get path to asset image"""
        return self.metadata_repo.get_asset_image_path(asset_id, category, thumbnail)

    def prepare_asset_import(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Prepare asset for import"""
        zip_index = self.metadata_repo.load_zip_index()
        zip_filename = zip_index.get(asset_id)

        if not zip_filename:
            return None

        return self.import_repo.get_asset_info(asset_id, zip_filename)

    def refresh_library(self):
        """Refresh asset library data"""
        self.metadata_repo.refresh_cache()
        self.search_service.clear_cache()
```

## UI Layer Abstraction

### Image Loading Service

```python
from PySide6.QtCore import QObject, QThread, pyqtSignal, QThreadPool, QRunnable
from PySide6.QtGui import QPixmap

class ImageLoadRequest(QRunnable):
    """Runnable for loading images in background threads"""

    def __init__(self, asset_id: str, image_path: Path, callback):
        super().__init__()
        self.asset_id = asset_id
        self.image_path = image_path
        self.callback = callback

    def run(self):
        """Load image and signal completion"""
        try:
            pixmap = QPixmap(str(self.image_path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = self._create_placeholder()

            self.callback.image_loaded.emit(self.asset_id, pixmap)
        except Exception as e:
            logging.error(f"Failed to load image {self.image_path}: {e}")
            self.callback.image_loaded.emit(self.asset_id, self._create_placeholder())

    def _create_placeholder(self) -> QPixmap:
        """Create placeholder pixmap for failed loads"""
        pixmap = QPixmap(150, 150)
        pixmap.fill(Qt.gray)
        return pixmap

class ImageLoadingService(QObject):
    """Service for managing asynchronous image loading"""

    image_loaded = pyqtSignal(str, QPixmap)  # asset_id, pixmap

    def __init__(self, max_threads: int = 10):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(max_threads)
        self._loading_cache: Set[str] = set()

    def load_image(self, asset_id: str, image_path: Path):
        """Queue image for loading"""
        if asset_id in self._loading_cache:
            return  # Already loading

        self._loading_cache.add(asset_id)
        request = ImageLoadRequest(asset_id, image_path, self)
        self.thread_pool.start(request)

    def clear_cache(self):
        """Clear loading cache"""
        self._loading_cache.clear()
```

### Settings Dialog

```python
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QSpinBox, QCheckBox,
                               QFileDialog, QMessageBox, QTabWidget, QWidget)

class SettingsDialog(QDialog):
    """Configuration dialog for application settings"""

    def __init__(self, config_manager: ConfigurationManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        self.setWindowTitle("TunnelUI Settings")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        """Setup the settings dialog UI"""
        layout = QVBoxLayout(self)

        # Create tabs
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Paths tab
        paths_tab = self._create_paths_tab()
        tab_widget.addTab(paths_tab, "Paths")

        # Display tab
        display_tab = self._create_display_tab()
        tab_widget.addTab(display_tab, "Display")

        # Advanced tab
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")

        # Buttons
        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.apply_button = QPushButton("Apply")
        self.reset_button = QPushButton("Reset to Defaults")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self._apply_settings)
        self.reset_button.clicked.connect(self._reset_to_defaults)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def _create_paths_tab(self) -> QWidget:
        """Create paths configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Metadata path
        self.metadata_path_edit = QLineEdit()
        metadata_browse = QPushButton("Browse...")
        metadata_browse.clicked.connect(lambda: self._browse_folder(self.metadata_path_edit))

        metadata_layout = QHBoxLayout()
        metadata_layout.addWidget(self.metadata_path_edit)
        metadata_layout.addWidget(metadata_browse)

        layout.addRow("Metadata Folder:", metadata_layout)

        # Assets path
        self.assets_path_edit = QLineEdit()
        assets_browse = QPushButton("Browse...")
        assets_browse.clicked.connect(lambda: self._browse_folder(self.assets_path_edit))

        assets_layout = QHBoxLayout()
        assets_layout.addWidget(self.assets_path_edit)
        assets_layout.addWidget(assets_browse)

        layout.addRow("Assets Folder:", assets_layout)

        return widget

    def _create_display_tab(self) -> QWidget:
        """Create display options tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(50, 300)
        self.thumbnail_size_spin.setSuffix(" px")
        layout.addRow("Thumbnail Size:", self.thumbnail_size_spin)

        self.grid_spacing_spin = QSpinBox()
        self.grid_spacing_spin.setRange(0, 50)
        self.grid_spacing_spin.setSuffix(" px")
        layout.addRow("Grid Spacing:", self.grid_spacing_spin)

        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create advanced options tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 20)
        layout.addRow("Max Concurrent Image Loads:", self.max_threads_spin)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        layout.addRow("Image Cache Size:", self.cache_size_spin)

        self.debug_check = QCheckBox()
        layout.addRow("Debug Mode:", self.debug_check)

        return widget

    def _browse_folder(self, line_edit: QLineEdit):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", line_edit.text())
        if folder:
            line_edit.setText(folder)

    def _load_current_values(self):
        """Load current configuration values into UI"""
        self.metadata_path_edit.setText(self.config.metadata_path)
        self.assets_path_edit.setText(self.config.assets_path)
        self.thumbnail_size_spin.setValue(self.config.thumbnail_size)
        self.grid_spacing_spin.setValue(self.config.grid_spacing)
        self.max_threads_spin.setValue(self.config.max_concurrent_loads)
        self.cache_size_spin.setValue(self.config.cache_size)
        self.debug_check.setChecked(self.config.debug_mode)

    def _apply_settings(self):
        """Apply current settings"""
        self.config.metadata_path = self.metadata_path_edit.text()
        self.config.assets_path = self.assets_path_edit.text()
        self.config.thumbnail_size = self.thumbnail_size_spin.value()
        self.config.grid_spacing = self.grid_spacing_spin.value()
        self.config.max_concurrent_loads = self.max_threads_spin.value()
        self.config.cache_size = self.cache_size_spin.value()
        self.config.debug_mode = self.debug_check.isChecked()

        if self.config_manager.save_config():
            QMessageBox.information(self, "Settings", "Settings saved successfully!")
        else:
            QMessageBox.warning(self, "Settings", "Failed to save settings!")

    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings",
                                   "Reset all settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config = AssetLibraryConfig()
            self._load_current_values()

    def accept(self):
        """Accept dialog and apply settings"""
        self._apply_settings()
        super().accept()
```

## Application Factory

### Application Builder

```python
class TunnelUIApplication:
    """Main application factory and coordinator"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_manager = ConfigurationManager(config_path)
        self.environment = self.config_manager.get_environment()
        self.config = self.config_manager.load_config()

        # Services
        self.metadata_repo: Optional[AssetMetadataRepository] = None
        self.import_repo: Optional[AssetImportRepository] = None
        self.asset_service: Optional[AssetManagementService] = None
        self.image_service: Optional[ImageLoadingService] = None

        self._setup_logging()
        self._initialize_services()

    def _setup_logging(self):
        """Configure application logging"""
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _initialize_services(self):
        """Initialize all application services"""
        try:
            # Data repositories
            self.metadata_repo = FileSystemMetadataRepository(self.config.metadata_path)
            self.import_repo = AssetImportRepository(self.config.assets_path)

            # Business services
            self.asset_service = AssetManagementService(self.metadata_repo, self.import_repo)
            self.image_service = ImageLoadingService(self.config.max_concurrent_loads)

            logging.info("Services initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize services: {e}")
            raise

    def create_main_window(self) -> 'TunnelMainWindow':
        """Create and configure the main application window"""
        from .ui.main_window import TunnelMainWindow

        window = TunnelMainWindow(
            asset_service=self.asset_service,
            image_service=self.image_service,
            config_manager=self.config_manager,
            environment=self.environment
        )

        return window

    def run_standalone(self):
        """Run application in standalone mode"""
        import sys
        from PySide6.QtWidgets import QApplication

        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()

        window = self.create_main_window()
        window.show()

        if not self.environment.is_maya:
            sys.exit(app.exec())

    def run_maya_mode(self):
        """Run application in Maya integration mode"""
        window = self.create_main_window()
        window.show()
        return window

# Backward compatibility entry point
def openWindow():
    """Legacy entry point for Maya shelf integration"""
    try:
        app = TunnelUIApplication()
        if app.environment.is_maya:
            return app.run_maya_mode()
        else:
            return app.run_standalone()
    except Exception as e:
        logging.error(f"Failed to open TunnelUI: {e}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "TunnelUI Error", f"Failed to initialize application:\n{e}")
        return None
```

## Error Handling and Logging

### Custom Exceptions

```python
class TunnelUIException(Exception):
    """Base exception for TunnelUI application"""
    pass

class ConfigurationError(TunnelUIException):
    """Configuration related errors"""
    pass

class AssetLibraryError(TunnelUIException):
    """Asset library access errors"""
    pass

class ImageLoadingError(TunnelUIException):
    """Image loading related errors"""
    pass
```

### Error Handler

```python
class ErrorHandler:
    """Centralized error handling and user notification"""

    @staticmethod
    def handle_configuration_error(error: ConfigurationError, parent=None):
        """Handle configuration errors with user dialog"""
        from PySide6.QtWidgets import QMessageBox

        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Configuration Error")
        msg.setText("There was a problem with the application configuration.")
        msg.setDetailedText(str(error))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    @staticmethod
    def handle_asset_library_error(error: AssetLibraryError, parent=None):
        """Handle asset library errors"""
        from PySide6.QtWidgets import QMessageBox

        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Asset Library Error")
        msg.setText("Cannot access the asset library.")
        msg.setInformativeText("Please check your configuration settings.")
        msg.setDetailedText(str(error))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
```

## Testing Framework

### Test Base Classes

```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

class TunnelUITestCase(unittest.TestCase):
    """Base test case with common setup for TunnelUI tests"""

    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "config.json"

        # Create test configuration
        test_config = {
            "metadata_path": str(self.temp_dir / "metadata"),
            "assets_path": str(self.temp_dir / "assets"),
            "thumbnail_size": 150,
            "debug_mode": True
        }

        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)

        # Create test directory structure
        (self.temp_dir / "metadata").mkdir()
        (self.temp_dir / "assets").mkdir()

    def tearDown(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_mock_asset_data(self) -> Dict:
        """Create mock asset data for testing"""
        return {
            "index": {
                "test_keyword": {
                    "test_asset_1": "Test Asset 1",
                    "test_asset_2": "Test Asset 2"
                }
            },
            "AssetGrouping": {
                "3d": ["test_asset_1", "test_asset_2"],
                "surface": ["test_asset_3"]
            }
        }
```

## Integration Points

### Maya Integration Wrapper

```python
class MayaIntegration:
    """Wrapper for Maya-specific functionality"""

    @staticmethod
    def is_maya_available() -> bool:
        """Check if Maya is available"""
        try:
            import maya.cmds
            return True
        except ImportError:
            return False

    @staticmethod
    def get_maya_main_window():
        """Get Maya main window for parenting"""
        if not MayaIntegration.is_maya_available():
            return None

        try:
            import maya.OpenMayaUI as OMUI
            import shiboken6
            from PySide6.QtWidgets import QWidget

            maya_win = OMUI.MQtUtil.mainWindow()
            return shiboken6.wrapInstance(int(maya_win), QWidget)
        except Exception as e:
            logging.warning(f"Failed to get Maya main window: {e}")
            return None

    @staticmethod
    def get_maya_stylesheet_path() -> Optional[str]:
        """Get Maya stylesheet path if available"""
        try:
            import mayaFilePaths
            return f"{mayaFilePaths.styleSheetFilepath}/dark.qss"
        except (ImportError, AttributeError):
            return None
```

This blueprint provides a comprehensive architecture for refactoring TunnelUI while maintaining backward compatibility and enabling the desired improvements. The modular design allows for incremental implementation and testing.
