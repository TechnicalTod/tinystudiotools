"""
Main window implementation for TinyStudioLauncher UI
"""

import json
import os
import sys
import logging
import subprocess
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
        QScrollArea,
        QSizePolicy,
        QMenuBar,
        QMenu,
        QDialog,
        QMessageBox,
    )
    from PySide6.QtCore import Qt, QSize, Signal, Slot, QThread, QTimer, QSettings
    from PySide6.QtGui import QIcon, QFont, QColor, QTextCursor, QAction
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
        QScrollArea,
        QSizePolicy,
        QMenuBar,
        QMenu,
        QDialog,
        QMessageBox,
        QAction,
    )
    from PySide2.QtCore import Qt, QSize, Signal, Slot, QThread, QTimer, QSettings
    from PySide2.QtGui import QIcon, QFont, QColor, QTextCursor

# Add parent directory to path for imports
def _resolve_parent_dir() -> Path:
    """
    Resolve runtime base directory for both source and frozen builds.

    In frozen mode, use executable directory so configs/resources/environments
    are read from the packaged app folder.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "configs").exists() and (exe_dir / "resources").exists():
            return exe_dir
    return Path(__file__).resolve().parent.parent.parent


PARENT_DIR = _resolve_parent_dir()
if str(PARENT_DIR) not in sys.path:
    sys.path.append(str(PARENT_DIR))

from src.environment_manager import EnvironmentManager
from src.launch_controller import LaunchController
from src.show_config import ShowVersionMismatchError


def _is_launcher_app_config(config_file: Path) -> bool:
    """True only for DCC launch configs (maya_2026.json), not show/template examples."""
    stem = config_file.stem.lower()
    if stem.startswith("show_config") or stem.startswith("template"):
        return False
    if ".example" in stem:
        return False
    if len(config_file.stem.split("_")) != 2:
        return False
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(data, dict) or "repository" not in data:
        return False
    return bool(data.get("executable_path") or data.get("executable_type") == "project")


class EnhancedConsole(QTextEdit):
    """Text console with rich formatting and color support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
    """Fixed-size tile button for an application. Visuals live in dark.qss."""

    TILE_WIDTH = 132
    TILE_HEIGHT = 118
    ICON_SIZE = 72

    def __init__(self, app_name, icon_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.status = "ready"  # ready, launching, running, error

        self.setObjectName("AppButton")
        self.setFixedSize(self.TILE_WIDTH, self.TILE_HEIGHT)
        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        if icon_path and os.path.exists(str(icon_path)):
            self.setIcon(QIcon(str(icon_path)))
        else:
            self.setText(app_name.title())

        self.update_status("ready")

    def update_status(self, status):
        """Update tile state. QSS reacts to the 'status' dynamic property."""
        self.status = status
        self.setProperty("status", status)
        # Force the style engine to re-evaluate property-based selectors.
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class TinyLauncherWindow(QMainWindow):
    """Main window for TinyStudioLauncher"""

    GRID_COLUMNS = 3
    GRID_H_SPACING = 18
    GRID_V_SPACING = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_dir = PARENT_DIR
        self.env_manager = EnvironmentManager(self.base_dir)
        self.launch_controller = LaunchController(self.base_dir / "configs", self.env_manager)
        self.user_settings = QSettings("TinyStudio", "TinyStudioLauncher")
        self._all_app_versions: dict[str, list[str]] = {}

        self.setWindowTitle("Tiny Studio Launcher")
        # Min width fits the 3-column grid plus margins; min height keeps console usable.
        min_w = (
            AppButton.TILE_WIDTH * self.GRID_COLUMNS
            + self.GRID_H_SPACING * (self.GRID_COLUMNS - 1)
            + 80
        )
        self.setMinimumSize(max(720, min_w), 420)

        # Set window icon
        icon_path = self.base_dir / "resources" / "icons" / "TinyStudioIcon.png"
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
        self._setup_menu_bar()

        # Load shows and app configs
        self.load_shows()
        self._restore_selected_show()
        self.show_combo.currentTextChanged.connect(self._save_selected_show)
        self.show_combo.currentTextChanged.connect(self._apply_show_version_pins)
        self.load_app_configs()
        self._apply_show_version_pins(self.show_combo.currentText())

        # Set up process monitoring with reduced frequency to prevent interference
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.update_processes)
        self.process_timer.start(5000)  # Update every 5 seconds instead of every second

        # Track recently launched apps to avoid excessive polling
        self.recently_launched = {}

    def setup_ui(self):
        """Set up the UI layout"""
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 10)
        root.setSpacing(10)

        root.addWidget(self._build_header(), 0)
        self._apps_panel = self._build_apps_panel()
        root.addWidget(self._apps_panel, 0)
        root.addWidget(self._build_console_panel(), 1)

        self.statusBar().showMessage("Ready")

    def _setup_menu_bar(self) -> None:
        bar = self.menuBar()
        install_menu = bar.addMenu("Install")
        act_ae_panel = QAction("After Effects scripts panel…", self)
        act_ae_panel.triggered.connect(self._open_ae_panel_install_dialog)
        install_menu.addAction(act_ae_panel)

    def _collect_ae_config_years(self) -> list[str]:
        """Version strings from configs/ae_<version>.json (e.g. 2024)."""
        config_dir = self.base_dir / "configs"
        years: list[str] = []
        if config_dir.is_dir():
            for p in sorted(config_dir.glob("ae_*.json")):
                parts = p.stem.split("_", 1)
                if len(parts) == 2 and parts[1]:
                    years.append(parts[1])
        return years if years else ["2024"]

    def _open_ae_panel_install_dialog(self) -> None:
        if sys.platform != "win32":
            QMessageBox.information(
                self,
                "Install",
                "Installing the After Effects ScriptUI panel is only supported on Windows.",
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Install — After Effects")
        layout = QVBoxLayout(dlg)
        info = QLabel(
            "Installs TinyStudioTools.jsx into your Adobe ScriptUI Panels folder "
            "(symlink or copy). Restart After Effects afterward, then use "
            "Window → TinyStudioTools.jsx."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        row = QHBoxLayout()
        row.addWidget(QLabel("After Effects version:"))
        combo = QComboBox()
        for y in self._collect_ae_config_years():
            combo.addItem(y)
        idx = combo.findText("2024")
        if idx >= 0:
            combo.setCurrentIndex(idx)
        row.addWidget(combo, 1)
        layout.addLayout(row)

        install_btn = QPushButton("Install After Effects scripts panel")
        install_btn.setDefault(True)

        def do_install() -> None:
            self._run_ae_panel_install_script(combo.currentText())
            dlg.accept()

        install_btn.clicked.connect(do_install)
        layout.addWidget(install_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.reject)
        layout.addWidget(close_btn)

        dlg.resize(480, dlg.sizeHint().height())
        dlg.exec()

    def _build_header(self) -> QWidget:
        """Single-row show selector strip."""
        header = QFrame()
        header.setObjectName("LauncherHeader")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        label = QLabel("SHOW")
        label.setObjectName("SectionLabel")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.show_combo = QComboBox()
        self.show_combo.setMinimumWidth(240)
        self.show_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        layout.addWidget(label, 0, Qt.AlignVCenter)
        layout.addWidget(self.show_combo, 1)
        return header

    APPS_OUTER_TOP = 12
    APPS_OUTER_BOTTOM = 12
    TILE_INNER_SPACING = 6  # spacing between button and version combo inside a tile

    def _build_apps_panel(self) -> QWidget:
        """Scrollable, centered grid of fixed-size app tiles; hugs its content height."""
        self.app_buttons = {}
        self.versions_combo = {}

        scroll = QScrollArea()
        scroll.setObjectName("AppsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Apps area should not grab any vertical slack — console gets it instead.
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        inner = QWidget()
        inner.setObjectName("AppsArea")
        inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        outer = QVBoxLayout(inner)
        outer.setContentsMargins(8, self.APPS_OUTER_TOP, 8, self.APPS_OUTER_BOTTOM)
        outer.setSpacing(0)

        # Centering row so the grid hugs its natural width regardless of window size.
        center_row = QHBoxLayout()
        center_row.setContentsMargins(0, 0, 0, 0)
        center_row.setSpacing(0)
        center_row.addStretch(1)

        self.app_layout = QGridLayout()
        self.app_layout.setContentsMargins(0, 0, 0, 0)
        self.app_layout.setHorizontalSpacing(self.GRID_H_SPACING)
        self.app_layout.setVerticalSpacing(self.GRID_V_SPACING)
        center_row.addLayout(self.app_layout, 0)
        center_row.addStretch(1)

        outer.addLayout(center_row)

        scroll.setWidget(inner)
        return scroll

    def _fit_apps_panel(self) -> int:
        """Lock the apps panel height to the actual grid content. Returns the height used."""
        if not hasattr(self, "_apps_panel") or self._apps_panel is None:
            return 0

        n = len(self.app_buttons)
        if n == 0:
            self._apps_panel.setFixedHeight(0)
            self._apps_natural_h = 0
            return 0

        rows = (n + self.GRID_COLUMNS - 1) // self.GRID_COLUMNS
        combo_h = 0
        for combo in self.versions_combo.values():
            combo_h = max(combo_h, combo.sizeHint().height())
        if combo_h == 0:
            combo_h = 22

        tile_h = AppButton.TILE_HEIGHT + self.TILE_INNER_SPACING + combo_h
        grid_h = rows * tile_h + max(0, rows - 1) * self.GRID_V_SPACING
        natural_h = self.APPS_OUTER_TOP + grid_h + self.APPS_OUTER_BOTTOM + 2

        self._apps_panel.setFixedHeight(natural_h)
        self._apps_natural_h = natural_h
        return natural_h

    def _build_console_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 6, 2, 0)
        layout.setSpacing(6)

        label = QLabel("CONSOLE")
        label.setObjectName("SectionLabel")
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.console = EnhancedConsole()
        layout.addWidget(label)
        layout.addWidget(self.console, 1)
        return panel

    def load_shows(self):
        """Load show directories from TINYSTUDIO_BASE_SHOW_DIR (default S:/)."""
        self.show_combo.clear()

        shows_dir = Path(self.launch_controller.base_show_dir)
        if not shows_dir.exists():
            self.console.append_message(
                f"Show root not found: {shows_dir}",
                "WARNING",
            )
            return

        excluded_names = {
            "$RECYCLE.BIN",
            "SYSTEM VOLUME INFORMATION",
            "AVG SANDBOX",
        }
        try:
            shows = []
            for directory in shows_dir.iterdir():
                if not directory.is_dir():
                    continue
                show_name = directory.name
                if show_name.upper() in excluded_names:
                    continue
                shows.append(show_name)
            shows.sort()
            for show in shows:
                self.show_combo.addItem(show)
        except Exception as e:
            self.console.append_message(f"Error loading shows: {str(e)}", "ERROR")
            return

        count = self.show_combo.count()
        if count:
            self.console.append_message(f"Loaded {count} shows from {shows_dir}", "INFO")
        else:
            self.console.append_message(f"No show folders found in {shows_dir}", "WARNING")

    def _restore_selected_show(self):
        """Restore saved show selection for the current user."""
        saved_show = self.user_settings.value("ui/selected_show", "", type=str)
        if not saved_show:
            return

        idx = self.show_combo.findText(saved_show)
        if idx >= 0:
            self.show_combo.setCurrentIndex(idx)
            self.console.append_message(f"Restored show selection: {saved_show}", "DEBUG")

    def _save_selected_show(self, show_name: str):
        """Persist selected show for the current user profile."""
        if not show_name:
            return
        self.user_settings.setValue("ui/selected_show", show_name)

    def _set_version_combo_items(self, app_name: str, versions: list[str], locked: bool) -> None:
        combo = self.versions_combo.get(app_name)
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        for version in sorted(versions):
            combo.addItem(version)
        combo.setEnabled(not locked)
        combo.setProperty("locked", locked)
        combo.style().unpolish(combo)
        combo.style().polish(combo)
        combo.update()
        combo.blockSignals(False)

    def _apply_show_version_pins(self, show_name: str) -> None:
        """Restrict version dropdowns to versions pinned in the show's config."""
        if not show_name or not self.versions_combo:
            return

        show_config = self.launch_controller.get_show_config(show_name)
        if show_config is None:
            for app_name, versions in self._all_app_versions.items():
                self._set_version_combo_items(app_name, versions, locked=False)
            self.statusBar().showMessage(f"No version pins for {show_name}")
            return

        pins = []
        for app_name, versions in self._all_app_versions.items():
            required = show_config.required_version(app_name)
            if required:
                available = [v for v in versions if v == required]
                if not available:
                    available = [required]
                self._set_version_combo_items(app_name, available, locked=True)
                pins.append(f"{app_name} {required}")
            else:
                self._set_version_combo_items(app_name, versions, locked=False)

        if pins:
            self.console.append_message(
                f"Show '{show_name}' pins: {', '.join(pins)}",
                "INFO",
            )
            self.statusBar().showMessage(f"Versions locked for {show_name}")
        else:
            self.statusBar().showMessage(f"Show config loaded for {show_name} (no app pins)")

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
                if not _is_launcher_app_config(config_file):
                    continue
                app_name, version = config_file.stem.split("_", 1)
                if app_name not in app_configs:
                    app_configs[app_name] = []
                app_configs[app_name].append(version)

            # Create app buttons with version dropdowns
            row, col = 0, 0
            max_cols = self.GRID_COLUMNS

            preferred_order = ["maya", "unreal", "ae"]
            order_index = {name: idx for idx, name in enumerate(preferred_order)}
            ordered_app_items = sorted(
                app_configs.items(),
                key=lambda item: (order_index.get(item[0].lower(), len(preferred_order)), item[0].lower()),
            )

            self._all_app_versions = {app: list(vers) for app, vers in app_configs.items()}

            for app_name, versions in ordered_app_items:
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

                version_combo = QComboBox()
                version_combo.setObjectName("VersionCombo")
                for version in sorted(versions):
                    version_combo.addItem(version)
                version_combo.setFixedWidth(AppButton.TILE_WIDTH)
                version_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

                self.app_buttons[app_name] = button
                self.versions_combo[app_name] = version_combo

                button.clicked.connect(lambda checked, app=app_name: self.launch_app(app))

                tile = QWidget()
                tile.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                tile_layout = QVBoxLayout(tile)
                tile_layout.setContentsMargins(0, 0, 0, 0)
                tile_layout.setSpacing(6)
                tile_layout.setAlignment(Qt.AlignHCenter)
                tile_layout.addWidget(button, 0, Qt.AlignHCenter)
                tile_layout.addWidget(version_combo, 0, Qt.AlignHCenter)

                self.app_layout.addWidget(tile, row, col, Qt.AlignTop | Qt.AlignHCenter)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            self.console.append_message(f"Loaded {len(app_configs)} applications", "SUCCESS")

            # Now that tiles exist, snap the apps panel height to the grid.
            self._fit_apps_panel()
            self._fit_window_to_contents()

        except Exception as e:
            self.console.append_message(f"Error loading configs: {str(e)}", "ERROR")
            import traceback

            traceback.print_exc()

    def _fit_window_to_contents(self) -> None:
        """Resize the window so apps fit snugly with a reasonable default console."""
        apps_h = getattr(self, "_apps_natural_h", 0)

        header_h = 50  # header strip + spacing
        console_default = 200
        status_h = self.statusBar().sizeHint().height()
        margins_h = 14 + 10 + 10  # root top/bottom margins + inter-widget spacing

        target_h = header_h + apps_h + console_default + status_h + margins_h
        target_w = max(self.width(), self.minimumWidth())
        self.resize(target_w, target_h)

    def _find_ae_panel_install_script(self) -> Path | None:
        """Resolve AERepository install script (walks up from launcher base for dev + frozen layouts)."""
        p = self.base_dir.resolve()
        for _ in range(10):
            candidate = p / "AERepository" / "install" / "install_tinystudio_ae_panel.ps1"
            if candidate.is_file():
                return candidate
            if p.parent == p:
                break
            p = p.parent
        return None

    def _run_ae_panel_install_script(self, ae_version: str) -> None:
        """Symlink or copy TinyStudioTools.jsx into Adobe ScriptUI Panels (Windows)."""
        if sys.platform != "win32":
            return
        script = self._find_ae_panel_install_script()
        if script is None:
            self.console.append_message(
                "AE panel installer not found under any parent of the launcher (skipped).",
                "WARNING",
            )
            return
        raw = str(ae_version).strip()
        try:
            year = int(raw[:4])
        except ValueError:
            year = 2024
            self.console.append_message(
                f"Could not parse AE year from {ae_version!r}; using {year} for panel install.",
                "WARNING",
            )
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        ps_exe = Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        ps_cmd = str(ps_exe) if ps_exe.is_file() else "powershell.exe"
        cmd = [
            ps_cmd,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-AeYear",
            str(year),
        ]
        creationflags = 0
        if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        self.console.append_message(
            f"Running AE ScriptUI panel install ({script.name}, -AeYear {year})...",
            "INFO",
        )
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=creationflags,
            )
        except subprocess.TimeoutExpired:
            self.console.append_message("AE panel install script timed out.", "WARNING")
            return
        except Exception as e:
            self.console.append_message(f"AE panel install script failed to run: {e}", "WARNING")
            return
        if completed.stdout and completed.stdout.strip():
            for line in completed.stdout.strip().splitlines():
                self.console.append_message(line, "INFO")
        if completed.stderr and completed.stderr.strip():
            for line in completed.stderr.strip().splitlines():
                self.console.append_message(line, "WARNING")
        if completed.returncode != 0:
            self.console.append_message(
                f"AE panel install exited with code {completed.returncode}",
                "WARNING",
            )
        else:
            self.console.append_message("AE ScriptUI panel install step finished.", "SUCCESS")

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
                if app_name.lower() == "ae":
                    self._run_ae_panel_install_script(version)

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

            except ShowVersionMismatchError as e:
                self.console.append_message(str(e), "ERROR")
                QMessageBox.warning(
                    self,
                    "Version not allowed for this show",
                    str(e),
                )
                self.app_buttons[app_name].update_status("error")
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
