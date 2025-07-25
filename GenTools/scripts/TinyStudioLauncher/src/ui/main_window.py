"""
Main window implementation for TinyStudioLauncher UI
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QComboBox,
        QPushButton,
        QTextEdit,
        QApplication,
        QSplitter,
        QFrame,
        QGridLayout,
    )
    from PySide6.QtCore import Qt, QSize, Signal, Slot, QThread, QTimer
    from PySide6.QtGui import QIcon, QFont, QColor, QTextCursor
except ImportError:
    # Fallback to PySide2 for Maya compatibility
    from PySide2.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QComboBox,
        QPushButton,
        QTextEdit,
        QApplication,
        QSplitter,
        QFrame,
        QGridLayout,
    )
    from PySide2.QtCore import Qt, QSize, Signal, Slot, QThread, QTimer
    from PySide2.QtGui import QIcon, QFont, QColor, QTextCursor

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.append(str(PARENT_DIR))

from src.environment_manager import EnvironmentManager
from src.launch_controller import LaunchController


class EnhancedConsole(QTextEdit):
    """Text console with rich formatting and color support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self.setMinimumHeight(100)
        self.setStyleSheet(
            "background-color: #1e1e1e; color: #ffffff; font-family: 'Consolas', monospace; font-size: 10pt;"
        )

    def append_message(self, message, level="INFO"):
        """Add a message with timestamp and color based on level"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Define colors for different message levels
        colors = {
            "DEBUG": "#569cd6",  # Blue
            "INFO": "#ffffff",  # White
            "SUCCESS": "#6a9955",  # Green
            "WARNING": "#dcdcaa",  # Yellow
            "ERROR": "#f14c4c",  # Red
        }
        color = colors.get(level, "#ffffff")

        # Format message with HTML
        formatted_message = f'<span style="color: {color}">[{timestamp}] {message}</span>'

        # Append to console and scroll to bottom
        self.append(formatted_message)
        self.moveCursor(QTextCursor.End)


class AppButton(QPushButton):
    """Enhanced button with app icon and status indicator"""

    def __init__(self, app_name, icon_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.status = "ready"  # ready, launching, running, error

        # Set size and style
        self.setMinimumSize(120, 100)
        self.setMaximumSize(120, 100)
        self.setIconSize(QSize(80, 80))
        self.setStyleSheet(
            ".AppButton { min-width: 120px; max-width: 120px; min-height: 100px; max-height: 100px; }"
        )
        self.setObjectName("AppButton")  # For styling

        # Set icon if provided
        if icon_path and os.path.exists(str(icon_path)):
            self.setIcon(QIcon(str(icon_path)))
        else:
            # Use app name as text if no icon
            self.setText(app_name.title())

        # Set default style
        self.update_status("ready")

    def update_status(self, status):
        """Update button appearance based on status"""
        self.status = status

        # Define styles for different states
        styles = {
            "ready": """
                QPushButton {
                    border: 2px solid #007acc;
                    border-radius: 5px;
                    background-color: #2d2d2d;
                    padding: 5px;
                    min-width: 120px;
                    max-width: 120px;
                    min-height: 100px;
                    max-height: 100px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
            """,
            "launching": """
                QPushButton {
                    border: 2px solid #dcdcaa;
                    border-radius: 5px;
                    background-color: #3d3d3d;
                    padding: 5px;
                    min-width: 120px;
                    max-width: 120px;
                    min-height: 100px;
                    max-height: 100px;
                }
            """,
            "running": """
                QPushButton {
                    border: 2px solid #6a9955;
                    border-radius: 5px;
                    background-color: #2d2d2d;
                    padding: 5px;
                    min-width: 120px;
                    max-width: 120px;
                    min-height: 100px;
                    max-height: 100px;
                }
            """,
            "error": """
                QPushButton {
                    border: 2px solid #f14c4c;
                    border-radius: 5px;
                    background-color: #2d2d2d;
                    padding: 5px;
                    min-width: 120px;
                    max-width: 120px;
                    min-height: 100px;
                    max-height: 100px;
                }
            """,
        }

        self.setStyleSheet(styles.get(status, styles["ready"]))


class TinyLauncherWindow(QMainWindow):
    """Main window for TinyStudioLauncher"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_dir = PARENT_DIR
        self.env_manager = EnvironmentManager(self.base_dir)
        self.launch_controller = LaunchController(self.base_dir / "configs", self.env_manager)

        # Configure window
        self.setWindowTitle("Tiny Studio Launcher")
        self.setMinimumSize(800, 600)

        # Set window icon
        icon_path = self.base_dir / "resources" / "icons" / "SagaIcon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Load UI style
        style_path = self.base_dir / "resources" / "styles" / "dark.qss"
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

        # Create logger for UI class
        self.logger = logging.getLogger("TinyLauncher.UI")

        # Set up the UI layout
        self.setup_ui()

        # Load shows and app configs
        self.load_shows()
        self.load_app_configs()

        # Set up process monitoring with reduced frequency to prevent interference
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.update_processes)
        self.process_timer.start(5000)  # Update every 5 seconds instead of every second

        # Track recently launched apps to avoid excessive polling
        self.recently_launched = {}

    def setup_ui(self):
        """Set up the UI layout"""
        # Create central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create show selection area
        show_layout = QHBoxLayout()
        show_label = QLabel("Select Show:")
        self.show_combo = QComboBox()
        self.show_combo.setMinimumWidth(200)
        show_layout.addWidget(show_label)
        show_layout.addWidget(self.show_combo)
        show_layout.addStretch()
        main_layout.addLayout(show_layout)

        # Create app button grid
        app_frame = QFrame()
        app_layout = QGridLayout(app_frame)
        app_layout.setSpacing(10)
        self.app_buttons = {}
        self.versions_combo = {}
        main_layout.addWidget(app_frame)

        # This will be populated once we load configs
        self.app_frame = app_frame
        self.app_layout = app_layout

        # Create console output
        console_label = QLabel("Console Output:")
        self.console = EnhancedConsole()
        main_layout.addWidget(console_label)
        main_layout.addWidget(self.console)

        # Status bar
        self.statusBar().showMessage("Ready")

    def load_shows(self):
        """Load show directories"""
        # Clear current items
        self.show_combo.clear()

        # Add test show
        self.show_combo.addItem("001_SHOWTEST")

        # Try to find shows from base directory
        shows_dir = Path("S:/")
        if shows_dir.exists():
            try:
                shows = [d.name for d in shows_dir.iterdir() if d.is_dir()]
                shows.sort()
                for show in shows:
                    if show not in ["001_SHOWTEST"]:
                        self.show_combo.addItem(show)
            except Exception as e:
                self.console.append_message(f"Error loading shows: {str(e)}", "ERROR")

        # Log
        self.console.append_message(f"Loaded {self.show_combo.count()} shows", "INFO")

    def load_app_configs(self):
        """Load application configurations"""
        try:
            config_dir = self.base_dir / "configs"
            if not config_dir.exists():
                self.console.append_message("Config directory not found", "ERROR")
                return

            # Find all config files
            config_files = list(config_dir.glob("*.json"))
            if not config_files:
                self.console.append_message("No config files found", "WARNING")
                return

            # Group configs by app type
            app_configs = {}
            for config_file in config_files:
                # Parse app_name and version from filename
                name_parts = config_file.stem.split("_")
                if len(name_parts) == 2:
                    app_name, version = name_parts
                    if app_name not in app_configs:
                        app_configs[app_name] = []
                    app_configs[app_name].append(version)

            # Create app buttons with version dropdowns
            row, col = 0, 0
            max_cols = 3

            for app_name, versions in app_configs.items():
                # Check for icon file using the app name with "Icon" suffix (case insensitive)
                icon_found = False
                for icon_file in os.listdir(str(self.base_dir / "resources" / "icons")):
                    if icon_file.lower().startswith(
                        app_name.lower()
                    ) and icon_file.lower().endswith("icon.png"):
                        icon_path = self.base_dir / "resources" / "icons" / icon_file
                        icon_found = True
                        break

                if not icon_found:
                    # Fallback to regular app name
                    icon_path = self.base_dir / "resources" / "icons" / f"{app_name}.png"
                    if not icon_path.exists():
                        # Use a text label instead if icon doesn't exist
                        button = AppButton(app_name)
                    else:
                        button = AppButton(app_name, str(icon_path))
                else:
                    button = AppButton(app_name, str(icon_path))

                # Create version combo
                version_combo = QComboBox()
                for version in sorted(versions):
                    version_combo.addItem(version)

                # Match the width of the combobox to the button
                version_combo.setFixedWidth(120)

                # Store references
                self.app_buttons[app_name] = button
                self.versions_combo[app_name] = version_combo

                # Connect button click
                button.clicked.connect(lambda checked, app=app_name: self.launch_app(app))

                # Create a container widget for each app
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.setContentsMargins(5, 5, 5, 5)
                container_layout.setSpacing(5)
                container_layout.setAlignment(Qt.AlignCenter)

                # Add button and combobox to container layout
                container_layout.addWidget(button, alignment=Qt.AlignCenter)
                container_layout.addWidget(version_combo, alignment=Qt.AlignCenter)

                # Add container to grid
                self.app_layout.addWidget(container, row, col)

                # Update grid position
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            self.console.append_message(f"Loaded {len(app_configs)} applications", "SUCCESS")

        except Exception as e:
            self.console.append_message(f"Error loading configs: {str(e)}", "ERROR")
            import traceback

            traceback.print_exc()

    def launch_app(self, app_name):
        """Launch the selected application"""
        try:
            # Get selected show and version
            show = self.show_combo.currentText()
            version = self.versions_combo[app_name].currentText()

            # Update button status
            self.app_buttons[app_name].update_status("launching")
            self.console.append_message(f"Launching {app_name} {version} for {show}...", "INFO")

            # Prepare launch config
            try:
                config = self.launch_controller.prepare_launch_config(app_name, version, show)
                self.console.append_message(f"Configuration prepared", "INFO")

                # Launch the application
                process = self.launch_controller.launch_application(config)
                self.console.append_message(
                    f"{app_name} {version} launched successfully (PID: {process.pid})", "SUCCESS"
                )

                # Mark as recently launched to reduce monitoring
                self.recently_launched[app_name] = {"timestamp": datetime.now(), "pid": process.pid}

                # Update button status after short delay
                QTimer.singleShot(1000, lambda: self.app_buttons[app_name].update_status("running"))

                # Minimize the launcher window to reduce interference
                self.showMinimized()

            except Exception as e:
                self.console.append_message(f"Error launching {app_name}: {str(e)}", "ERROR")
                self.app_buttons[app_name].update_status("error")

        except Exception as e:
            self.console.append_message(f"Error in launch_app: {str(e)}", "ERROR")

    def update_processes(self):
        """Update status of running processes with reduced frequency"""
        try:
            # Clean up old entries in recently_launched
            current_time = datetime.now()
            to_remove = []
            for app_name, data in self.recently_launched.items():
                # Remove entries older than 2 minutes
                if (current_time - data["timestamp"]).total_seconds() > 120:
                    to_remove.append(app_name)

            for app_name in to_remove:
                del self.recently_launched[app_name]

            # Only update active processes if we're not in the critical startup period
            if not self.recently_launched:
                active_processes = self.launch_controller.get_active_processes()

                # Update buttons based on active processes
                for key, info in active_processes.items():
                    app_name = info.get("config").app_name
                    if app_name in self.app_buttons:
                        self.app_buttons[app_name].update_status("running")

        except Exception as e:
            # Don't log this to avoid spamming console
            pass
