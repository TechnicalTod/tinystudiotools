# TinyStudioLauncher - Backend Blueprint

## Architecture Overview

The TinyStudioLauncher uses a modular architecture with clear separation of concerns between environment management, application launching, and UI presentation.

## Core Components

### Environment Manager

```python
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import json
import os
import logging

logger = logging.getLogger(__name__)

class EnvironmentManager:
    """Manages UV virtual environments for different applications"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.environments_dir = base_path / "environments"
        self.requirements_dir = base_path / "requirements"
        self.environments_dir.mkdir(exist_ok=True)
        self.requirements_dir.mkdir(exist_ok=True)

    def create_environment(self, app_name: str, python_version: str) -> bool:
        """Create a new UV environment for an application"""
        env_path = self.environments_dir / app_name

        try:
            # Use uv to create virtual environment with specific Python version
            cmd = [
                "uv", "venv",
                str(env_path),
                "--python", python_version
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to create environment: {result.stderr}")
                return False

            logger.info(f"Created environment for {app_name} with Python {python_version}")
            return True

        except Exception as e:
            logger.error(f"Error creating environment: {e}")
            return False

    def sync_environment(self, app_name: str) -> bool:
        """Sync packages from requirements file"""
        env_path = self.environments_dir / app_name
        req_file = self.requirements_dir / f"{app_name}.txt"

        if not req_file.exists():
            logger.warning(f"No requirements file found for {app_name}")
            return True

        try:
            # Use uv pip to install requirements
            cmd = [
                "uv", "pip", "sync",
                "--python", str(env_path / "Scripts" / "python.exe"),
                str(req_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to sync packages: {result.stderr}")
                return False

            logger.info(f"Synced packages for {app_name}")
            return True

        except Exception as e:
            logger.error(f"Error syncing packages: {e}")
            return False

    def get_environment_info(self, app_name: str) -> Dict:
        """Get information about an environment"""
        env_path = self.environments_dir / app_name

        if not env_path.exists():
            return {"exists": False}

        info = {
            "exists": True,
            "path": str(env_path),
            "python_executable": str(env_path / "Scripts" / "python.exe"),
            "packages": []
        }

        # Get installed packages
        try:
            cmd = [
                str(env_path / "Scripts" / "python.exe"),
                "-m", "pip", "list", "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info["packages"] = json.loads(result.stdout)
        except Exception as e:
            logger.warning(f"Could not get package list: {e}")

        return info
```

### Launch Controller

```python
import subprocess
import os
from pathlib import Path
from typing import Dict, Optional, Any
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LaunchConfig:
    """Configuration for launching an application"""
    app_name: str
    version: str
    show: str
    executable_path: str
    environment_path: str
    env_vars: Dict[str, str]
    python_paths: List[str]
    script_paths: List[str]

class LaunchController:
    """Controls the launching of applications with proper environment setup"""

    def __init__(self, config_dir: Path, env_manager: EnvironmentManager):
        self.config_dir = config_dir
        self.env_manager = env_manager
        self.active_processes = {}

    def load_config(self, app_name: str, version: str) -> Dict:
        """Load configuration for an application/version"""
        config_file = self.config_dir / f"{app_name}_{version}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration not found: {config_file}")

        with open(config_file, 'r') as f:
            return json.load(f)

    def prepare_launch_config(self, app_name: str, version: str, show: str) -> LaunchConfig:
        """Prepare launch configuration with all necessary paths and variables"""
        config = self.load_config(app_name, version)
        env_info = self.env_manager.get_environment_info(f"{app_name}-{version}")

        if not env_info["exists"]:
            raise RuntimeError(f"Environment not found for {app_name}-{version}")

        # Build environment variables
        env_vars = os.environ.copy()

        # Clear any existing Python paths
        env_vars.pop('PYTHONPATH', None)
        env_vars.pop('MAYA_SCRIPT_PATH', None)

        # Set base paths
        base_paths = {
            "SAGA_BASE_SHOW_DIR": "S:/",
            "SAGA_LIB_DIR": "L:/",
            "SCRIPT_DIR": "L:/SagaTools/",
            "SHOW_NAME": show,
            "CURRENT_SHOW": show
        }
        env_vars.update(base_paths)

        # Build repository paths
        repo_base = Path(base_paths["SCRIPT_DIR"]) / config["repository"] / version

        # Collect Python paths
        python_paths = [
            str(repo_base / "scripts"),
            str(repo_base / "shared"),
            str(repo_base / "tools"),
        ]

        # Add show-specific paths if they exist
        show_scripts = Path(base_paths["SAGA_BASE_SHOW_DIR"]) / show / "scripts" / app_name
        if show_scripts.exists():
            python_paths.insert(0, str(show_scripts))

        # Add additional paths from config
        for path in config.get("additional_paths", []):
            python_paths.append(path.format(**env_vars))

        # Set Python path
        env_vars["PYTHONPATH"] = os.pathsep.join(python_paths)

        # Set application-specific variables
        if app_name == "maya":
            env_vars["MAYA_SCRIPT_PATH"] = env_vars["PYTHONPATH"]
            env_vars["QT_PLUGIN_PATH"] = config["qt_plugin_path"].format(version=version)

        # Add custom environment variables from config
        for key, value in config.get("env_vars", {}).items():
            env_vars[key] = value.format(**env_vars)

        return LaunchConfig(
            app_name=app_name,
            version=version,
            show=show,
            executable_path=config["executable_path"].format(version=version),
            environment_path=env_info["path"],
            env_vars=env_vars,
            python_paths=python_paths,
            script_paths=config.get("script_paths", [])
        )

    def launch_application(self, launch_config: LaunchConfig) -> subprocess.Popen:
        """Launch an application with the prepared configuration"""

        # Verify executable exists
        if not Path(launch_config.executable_path).exists():
            raise FileNotFoundError(f"Executable not found: {launch_config.executable_path}")

        # Activate virtual environment by prepending to PATH
        env_scripts = Path(launch_config.environment_path) / "Scripts"
        launch_config.env_vars["PATH"] = f"{env_scripts};{launch_config.env_vars['PATH']}"

        # Log launch information
        logger.info(f"Launching {launch_config.app_name} {launch_config.version} for {launch_config.show}")
        logger.debug(f"PYTHONPATH: {launch_config.env_vars.get('PYTHONPATH', 'Not set')}")

        # Launch the application
        process = subprocess.Popen(
            [launch_config.executable_path],
            env=launch_config.env_vars,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Track the process
        process_key = f"{launch_config.app_name}_{launch_config.version}_{launch_config.show}_{process.pid}"
        self.active_processes[process_key] = process

        return process

    def get_active_processes(self) -> Dict[str, subprocess.Popen]:
        """Get dictionary of active processes, cleaning up terminated ones"""
        # Clean up terminated processes
        terminated = []
        for key, process in self.active_processes.items():
            if process.poll() is not None:
                terminated.append(key)

        for key in terminated:
            del self.active_processes[key]

        return self.active_processes.copy()
```

### Configuration Files

```json
// configs/maya_2023.json
{
  "name": "Maya 2023",
  "repository": "MayaRepository",
  "python_version": "3.9",
  "executable_path": "C:/Program Files/Autodesk/Maya{version}/bin/maya.exe",
  "qt_plugin_path": "C:/Program Files/Autodesk/Maya{version}/plugins/platforms",
  "additional_paths": [
    "{MAYA_REPO}/scripts/melScripts",
    "{MAYA_REPO}/scripts/Publisher",
    "{MAYA_REPO}/scripts/Publisher/src"
  ],
  "env_vars": {
    "MAYA_APP_DIR": "{SAGA_BASE_SHOW_DIR}{SHOW_NAME}/maya/{version}",
    "MAYA_PROJECT": "{SAGA_BASE_SHOW_DIR}{SHOW_NAME}/maya/projects",
    "MAYA_MODULE_PATH": "{MAYA_REPO}/modules"
  },
  "script_paths": ["scripts", "shared", "tools"],
  "startup_script": "userSetup.py"
}
```

```json
// configs/unreal.json
{
  "name": "Unreal Engine",
  "repository": "UnrealRepository",
  "python_version": "3.10",
  "executable_path": "{UNREAL_PROJECT_DIR}",
  "project_pattern": "{SAGA_BASE_SHOW_DIR}{CURRENT_SHOW}/05_Unreal/SAGA_{CURRENT_SHOW}/SAGA_{CURRENT_SHOW}.uproject",
  "additional_paths": [],
  "env_vars": {
    "UE_PYTHONPATH": "{PYTHONPATH}",
    "UNREAL_PROJECT_BASE_DIR": "{SAGA_BASE_SHOW_DIR}{CURRENT_SHOW}/05_Unreal/SAGA_{CURRENT_SHOW}/"
  },
  "script_paths": ["scripts", "shared", "tools"]
}
```

### UI Components

```python
from PySide2.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTextEdit, QLabel,
    QGroupBox, QSplitter
)
from PySide2.QtCore import Qt, QThread, Signal, QSettings
from PySide2.QtGui import QIcon, QPixmap
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ConsoleOutput(QTextEdit):
    """Custom console output widget with formatting"""

    def __init__(self):
        super().__init__()
        self.setMaximumHeight(200)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New';
                font-size: 9pt;
                border: 1px solid #3e3e3e;
            }
        """)

    def add_message(self, message: str, level: str = "INFO"):
        """Add a formatted message to the console"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding based on level
        colors = {
            "INFO": "#ffffff",
            "SUCCESS": "#4ec9b0",
            "WARNING": "#dcdcaa",
            "ERROR": "#f48771"
        }
        color = colors.get(level, "#ffffff")

        formatted_msg = f'<span style="color: #858585">[{timestamp}]</span> '
        formatted_msg += f'<span style="color: {color}">{message}</span>'

        self.append(formatted_msg)
        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ApplicationButton(QPushButton):
    """Custom button for launching applications"""

    def __init__(self, app_name: str, icon_path: str, parent=None):
        super().__init__(parent)
        self.app_name = app_name

        # Set icon
        icon = QIcon(icon_path)
        self.setIcon(icon)
        self.setIconSize(QSize(120, 100))

        # Style
        self.setMinimumSize(140, 120)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 2px solid #3e3e3e;
                border-radius: 8px;
            }
            QPushButton:hover {
                border: 2px solid #02de23;
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
        """)

        # Add status indicator
        self.status_indicator = QLabel(self)
        self.status_indicator.setGeometry(self.width() - 20, 5, 15, 15)
        self.set_status("ready")

    def set_status(self, status: str):
        """Update status indicator"""
        colors = {
            "ready": "#4ec9b0",    # Green
            "launching": "#dcdcaa", # Yellow
            "error": "#f48771",    # Red
            "disabled": "#858585"  # Gray
        }
        color = colors.get(status, "#858585")

        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 7px;
            }}
        """)

class TinyStudioLauncherUI(QMainWindow):
    """Main window for TinyStudioLauncher"""

    launch_requested = Signal(str, str, str)  # app_name, version, show

    def __init__(self, controller: LaunchController):
        super().__init__()
        self.controller = controller
        self.settings = QSettings("SagaTools", "TinyStudioLauncher")
        self.app_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Tiny Studio Launcher")
        self.setMinimumSize(1200, 700)

        # Load stylesheet
        self.load_stylesheet()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Header section
        header_layout = QHBoxLayout()

        # Show selection
        show_group = QGroupBox("Show Selection")
        show_layout = QVBoxLayout(show_group)

        self.show_combo = QComboBox()
        self.show_combo.setMinimumHeight(30)
        self.populate_shows()
        show_layout.addWidget(QLabel("Select Show:"))
        show_layout.addWidget(self.show_combo)

        header_layout.addWidget(show_group)
        header_layout.addStretch()

        # Environment status
        env_group = QGroupBox("Environment Status")
        env_layout = QVBoxLayout(env_group)
        self.env_status_label = QLabel("All environments ready")
        env_layout.addWidget(self.env_status_label)

        header_layout.addWidget(env_group)

        main_layout.addLayout(header_layout)

        # Applications section
        apps_group = QGroupBox("Applications")
        apps_layout = QHBoxLayout(apps_group)
        apps_layout.setSpacing(20)

        # Maya section
        maya_layout = QVBoxLayout()
        maya_layout.addWidget(QLabel("Maya Version:"))

        self.maya_version_combo = QComboBox()
        self.maya_version_combo.addItems(["2023", "2026"])
        maya_layout.addWidget(self.maya_version_combo)

        maya_button = ApplicationButton("maya", "resources/icons/maya.png")
        maya_button.clicked.connect(lambda: self.launch_application("maya"))
        self.app_buttons["maya"] = maya_button
        maya_layout.addWidget(maya_button)

        apps_layout.addLayout(maya_layout)

        # Unreal section
        unreal_layout = QVBoxLayout()
        unreal_layout.addWidget(QLabel("Unreal Engine"))

        unreal_button = ApplicationButton("unreal", "resources/icons/unreal.png")
        unreal_button.clicked.connect(lambda: self.launch_application("unreal"))
        self.app_buttons["unreal"] = unreal_button
        unreal_layout.addWidget(unreal_button)

        apps_layout.addLayout(unreal_layout)

        # After Effects section (disabled for now)
        ae_layout = QVBoxLayout()
        ae_layout.addWidget(QLabel("After Effects"))

        ae_button = ApplicationButton("aftereffects", "resources/icons/ae.png")
        ae_button.setEnabled(False)
        ae_button.set_status("disabled")
        self.app_buttons["aftereffects"] = ae_button
        ae_layout.addWidget(ae_button)

        apps_layout.addLayout(ae_layout)

        main_layout.addWidget(apps_group)

        # Console output
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout(console_group)

        self.console = ConsoleOutput()
        console_layout.addWidget(self.console)

        main_layout.addWidget(console_group)

        # Load settings
        self.load_settings()

        # Initial message
        self.console.add_message("Tiny Studio Launcher initialized", "SUCCESS")

    def launch_application(self, app_name: str):
        """Handle application launch request"""
        show = self.show_combo.currentText()

        if not show:
            self.console.add_message("Please select a show", "WARNING")
            return

        version = ""
        if app_name == "maya":
            version = self.maya_version_combo.currentText()

        self.console.add_message(f"Launching {app_name} {version} for {show}...", "INFO")
        self.app_buttons[app_name].set_status("launching")

        # Emit signal for controller to handle
        self.launch_requested.emit(app_name, version, show)

    def populate_shows(self):
        """Populate show dropdown from S:/ directory"""
        import os
        drive_path = "S:/"

        if os.path.exists(drive_path):
            try:
                directories = [
                    d for d in os.listdir(drive_path)
                    if os.path.isdir(os.path.join(drive_path, d))
                    and d not in ["$RECYCLE.BIN", "System Volume Information"]
                ]
                self.show_combo.addItems(directories)
                self.console.add_message(f"Found {len(directories)} shows", "INFO")
            except Exception as e:
                self.console.add_message(f"Error loading shows: {e}", "ERROR")
        else:
            self.console.add_message("S:/ drive not found", "ERROR")

    def load_settings(self):
        """Load saved settings"""
        last_show = self.settings.value("last_show", "")
        if last_show:
            index = self.show_combo.findText(last_show)
            if index >= 0:
                self.show_combo.setCurrentIndex(index)

        last_maya_version = self.settings.value("last_maya_version", "2023")
        index = self.maya_version_combo.findText(last_maya_version)
        if index >= 0:
            self.maya_version_combo.setCurrentIndex(index)

    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("last_show", self.show_combo.currentText())
        self.settings.setValue("last_maya_version", self.maya_version_combo.currentText())

    def closeEvent(self, event):
        """Save settings on close"""
        self.save_settings()
        super().closeEvent(event)
```

## Deployment Strategy

### Installation Process

1. **Install UV globally**:

   ```bash
   pip install uv
   # or
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up environments**:

   ```python
   # setup_environments.py
   from pathlib import Path
   from environment_manager import EnvironmentManager

   manager = EnvironmentManager(Path("L:/SagaTools/GenTools/scripts/TinyStudioLauncher"))

   # Create environments
   manager.create_environment("maya-2023", "3.9")
   manager.create_environment("maya-2026", "3.10")
   manager.create_environment("unreal", "3.10")

   # Sync packages
   manager.sync_environment("maya-2023")
   manager.sync_environment("maya-2026")
   manager.sync_environment("unreal")
   ```

3. **Package with PyInstaller**:

   ```python
   # TinyStudioLauncher.spec
   # -*- mode: python ; coding: utf-8 -*-

   block_cipher = None

   added_files = [
       ('resources/icons/*.png', 'resources/icons'),
       ('resources/styles/*.qss', 'resources/styles'),
       ('configs/*.json', 'configs'),
   ]

   a = Analysis(
       ['src/launcher.py'],
       pathex=[],
       binaries=[],
       datas=added_files,
       hiddenimports=['PySide2.QtXml'],
       hookspath=[],
       hooksconfig={},
       runtime_hooks=[],
       excludes=[],
       win_no_prefer_redirects=False,
       win_private_assemblies=False,
       cipher=block_cipher,
       noarchive=False,
   )

   pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

   exe = EXE(
       pyz,
       a.scripts,
       a.binaries,
       a.zipfiles,
       a.datas,
       [],
       name='TinyStudioLauncher',
       debug=False,
       bootloader_ignore_signals=False,
       strip=False,
       upx=True,
       console=False,
       icon='resources/icons/launcher.ico'
   )
   ```

## Error Handling

### Common Issues and Solutions

1. **Environment not found**:

   - Check if UV is installed
   - Verify Python version availability
   - Create environment if missing

2. **Package installation failures**:

   - Check network connectivity
   - Verify package compatibility
   - Use offline wheel files if needed

3. **Application launch failures**:
   - Verify executable paths
   - Check environment activation
   - Log all subprocess output

### Logging Configuration

```python
import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """Configure logging for the application"""
    log_dir = Path.home() / "TinyStudioLauncher" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "launcher.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )

    # Console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

## Performance Optimizations

1. **Parallel environment checks**: Check all environments simultaneously on startup
2. **Lazy loading**: Only activate environments when launching
3. **Process pooling**: Reuse subprocess handles where possible
4. **Caching**: Cache environment information with TTL

## Security Considerations

1. **Path validation**: Sanitize all user inputs
2. **Process isolation**: Each launch gets fresh environment
3. **Credential management**: Never store credentials in configs
4. **Audit logging**: Log all application launches
