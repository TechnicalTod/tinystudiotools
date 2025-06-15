"""
Settings Widget - Configuration interface
"""

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError:
    try:
        from PySide2.QtWidgets import *
        from PySide2.QtCore import *
        from PySide2.QtGui import *
    except ImportError:
        raise ImportError("Neither PySide6 nor PySide2 is available")

import os
from pathlib import Path


class SettingsWidget(QWidget):
    """Widget for application settings"""

    # Signals
    settings_changed = Signal(dict)  # Emit changed settings
    network_test_requested = Signal(str)  # Emit network path to test

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the settings interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Network settings
        self.network_section = self.create_network_section()
        layout.addWidget(self.network_section)

        # Database settings
        self.database_section = self.create_database_section()
        layout.addWidget(self.database_section)

        # Validation settings
        self.validation_section = self.create_validation_section()
        layout.addWidget(self.validation_section)

        # UI settings
        self.ui_section = self.create_ui_section()
        layout.addWidget(self.ui_section)

        layout.addStretch()

        # Action buttons
        self.buttons_section = self.create_buttons_section()
        layout.addWidget(self.buttons_section)

    def create_network_section(self):
        """Create network settings section"""
        group = QGroupBox("Network Settings")
        layout = QFormLayout(group)

        # Network path
        self.network_path_edit = QLineEdit("S:/")
        self.network_path_edit.setToolTip("Base path for published files")

        network_browse_btn = QPushButton("Browse...")
        network_browse_btn.clicked.connect(self.browse_network_path)

        network_path_layout = QHBoxLayout()
        network_path_layout.addWidget(self.network_path_edit)
        network_path_layout.addWidget(network_browse_btn)

        # Test connection button
        self.test_network_btn = QPushButton("🔗 Test Connection")
        self.test_network_btn.setToolTip("Test network path accessibility")

        # Connection status
        self.network_status_label = QLabel("Not tested")
        self.network_status_label.setStyleSheet("QLabel { color: #999; }")

        # Create widgets for layouts
        network_path_widget = QWidget()
        network_path_widget.setLayout(network_path_layout)

        # Add to layout
        layout.addRow("Network Path:", network_path_widget)
        layout.addRow("Test:", self.test_network_btn)
        layout.addRow("Status:", self.network_status_label)

        return group

    def create_database_section(self):
        """Create database settings section"""
        group = QGroupBox("Database Settings")
        layout = QFormLayout(group)

        # Database path
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setToolTip("Path to SQLite database file")

        db_browse_btn = QPushButton("Browse...")
        db_browse_btn.clicked.connect(self.browse_database_path)

        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(db_browse_btn)

        # Auto-backup
        self.auto_backup_check = QCheckBox("Enable automatic backups")
        self.auto_backup_check.setToolTip("Automatically backup database")

        # Backup location
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setEnabled(False)

        backup_browse_btn = QPushButton("Browse...")
        backup_browse_btn.clicked.connect(self.browse_backup_path)
        backup_browse_btn.setEnabled(False)

        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_path_edit)
        backup_path_layout.addWidget(backup_browse_btn)

        # Connect auto-backup checkbox
        self.auto_backup_check.toggled.connect(self.backup_path_edit.setEnabled)
        self.auto_backup_check.toggled.connect(backup_browse_btn.setEnabled)

        # Create widgets for layouts
        db_path_widget = QWidget()
        db_path_widget.setLayout(db_path_layout)

        backup_path_widget = QWidget()
        backup_path_widget.setLayout(backup_path_layout)

        # Add to layout
        layout.addRow("Database Path:", db_path_widget)
        layout.addRow("", self.auto_backup_check)
        layout.addRow("Backup Path:", backup_path_widget)

        return group

    def create_validation_section(self):
        """Create validation settings section"""
        group = QGroupBox("Validation Rules")
        layout = QVBoxLayout(group)

        # Create checkboxes for validation rules
        self.validation_checks = {}

        rules = [
            ("naming_convention", "Naming Convention", "Check scene and asset naming standards"),
            ("scene_cleanup", "Scene Cleanup", "Check for unused nodes and cleanup issues"),
            ("file_paths", "File Paths", "Check for missing files and broken references"),
            ("geometry", "Geometry", "Check geometry for common issues"),
            ("required_comments", "Required Comments", "Require comments for publishing"),
        ]

        for rule_id, rule_name, rule_desc in rules:
            check = QCheckBox(rule_name)
            check.setToolTip(rule_desc)
            check.setChecked(True)  # Default enabled

            self.validation_checks[rule_id] = check
            layout.addWidget(check)

        return group

    def create_ui_section(self):
        """Create UI settings section"""
        group = QGroupBox("User Interface")
        layout = QFormLayout(group)

        # Theme selection (placeholder for future)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Maya)", "Light", "System"])
        self.theme_combo.setCurrentText("Dark (Maya)")
        self.theme_combo.setEnabled(False)  # Disabled since we use custom stylesheet

        # Window size
        self.window_size_combo = QComboBox()
        self.window_size_combo.addItems(["800x600", "1000x700", "1200x800", "Custom"])
        self.window_size_combo.setCurrentText("1000x700")

        # Auto-refresh
        self.auto_refresh_check = QCheckBox("Auto-refresh context on scene change")
        self.auto_refresh_check.setChecked(True)

        # Show tooltips
        self.show_tooltips_check = QCheckBox("Show tooltips")
        self.show_tooltips_check.setChecked(True)

        # Add to layout
        layout.addRow("Theme:", self.theme_combo)
        layout.addRow("Window Size:", self.window_size_combo)
        layout.addRow("", self.auto_refresh_check)
        layout.addRow("", self.show_tooltips_check)

        return group

    def create_buttons_section(self):
        """Create action buttons section"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Reset to defaults
        self.reset_btn = QPushButton("🔄 Reset to Defaults")
        self.reset_btn.setToolTip("Reset all settings to default values")

        # Import/Export buttons
        self.import_btn = QPushButton("📁 Import Settings")
        self.export_btn = QPushButton("💾 Export Settings")

        layout.addWidget(self.reset_btn)
        layout.addStretch()
        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)

        return widget

    def setup_connections(self):
        """Setup signal connections"""
        self.test_network_btn.clicked.connect(self.test_network_connection)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.import_btn.clicked.connect(self.import_settings)
        self.export_btn.clicked.connect(self.export_settings)

        # Connect settings change signals
        self.network_path_edit.textChanged.connect(self.on_settings_changed)
        self.db_path_edit.textChanged.connect(self.on_settings_changed)
        self.auto_backup_check.toggled.connect(self.on_settings_changed)
        self.backup_path_edit.textChanged.connect(self.on_settings_changed)

        for check in self.validation_checks.values():
            check.toggled.connect(self.on_settings_changed)

        self.window_size_combo.currentTextChanged.connect(self.on_settings_changed)
        self.auto_refresh_check.toggled.connect(self.on_settings_changed)
        self.show_tooltips_check.toggled.connect(self.on_settings_changed)

    def on_settings_changed(self):
        """Handle settings change"""
        settings = self.get_settings()
        self.settings_changed.emit(settings)

    def test_network_connection(self):
        """Test network connection"""
        network_path = self.network_path_edit.text()
        if not network_path:
            self.update_network_status(False, "No path specified")
            return

        try:
            path = Path(network_path)
            if path.exists() and path.is_dir():
                # Try to create a test file
                test_file = path / ".maya_publisher_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    self.update_network_status(True, "Connection successful")
                except:
                    self.update_network_status(False, "No write access")
            else:
                self.update_network_status(False, "Path does not exist")
        except Exception as e:
            self.update_network_status(False, f"Error: {str(e)}")

        # Also emit signal for external handling
        self.network_test_requested.emit(network_path)

    def update_network_status(self, success, message):
        """Update network status display"""
        if success:
            self.network_status_label.setText(f"✅ {message}")
            self.network_status_label.setStyleSheet("QLabel { color: #4CAF50; }")
        else:
            self.network_status_label.setText(f"❌ {message}")
            self.network_status_label.setStyleSheet("QLabel { color: #f44336; }")

    def browse_network_path(self):
        """Browse for network path"""
        current_path = self.network_path_edit.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Network Path", current_path)
        if folder:
            self.network_path_edit.setText(folder)

    def browse_database_path(self):
        """Browse for database path"""
        current_path = self.db_path_edit.text()
        if not current_path:
            current_path = str(Path.home())

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Database File", current_path, "SQLite Database (*.db);;All Files (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)

    def browse_backup_path(self):
        """Browse for backup path"""
        current_path = self.backup_path_edit.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Path", current_path)
        if folder:
            self.backup_path_edit.setText(folder)

    def get_settings(self):
        """Get current settings as dictionary"""
        return {
            "network_path": self.network_path_edit.text(),
            "database_path": self.db_path_edit.text(),
            "auto_backup": self.auto_backup_check.isChecked(),
            "backup_path": self.backup_path_edit.text(),
            "validation_rules": {
                rule_id: check.isChecked() for rule_id, check in self.validation_checks.items()
            },
            "window_size": self.window_size_combo.currentText(),
            "auto_refresh": self.auto_refresh_check.isChecked(),
            "show_tooltips": self.show_tooltips_check.isChecked(),
        }

    def set_settings(self, settings):
        """Set settings from dictionary"""
        if "network_path" in settings:
            self.network_path_edit.setText(settings["network_path"])

        if "database_path" in settings:
            self.db_path_edit.setText(settings["database_path"])

        if "auto_backup" in settings:
            self.auto_backup_check.setChecked(settings["auto_backup"])

        if "backup_path" in settings:
            self.backup_path_edit.setText(settings["backup_path"])

        if "validation_rules" in settings:
            for rule_id, enabled in settings["validation_rules"].items():
                if rule_id in self.validation_checks:
                    self.validation_checks[rule_id].setChecked(enabled)

        if "window_size" in settings:
            index = self.window_size_combo.findText(settings["window_size"])
            if index >= 0:
                self.window_size_combo.setCurrentIndex(index)

        if "auto_refresh" in settings:
            self.auto_refresh_check.setChecked(settings["auto_refresh"])

        if "show_tooltips" in settings:
            self.show_tooltips_check.setChecked(settings["show_tooltips"])

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Reset to defaults
            default_settings = {
                "network_path": "S:/",
                "database_path": "",
                "auto_backup": False,
                "backup_path": "",
                "validation_rules": {rule_id: True for rule_id in self.validation_checks.keys()},
                "window_size": "1000x700",
                "auto_refresh": True,
                "show_tooltips": True,
            }

            self.set_settings(default_settings)
            self.update_network_status(False, "Not tested")

            QMessageBox.information(self, "Reset Complete", "Settings have been reset to defaults.")

    def import_settings(self):
        """Import settings from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                import json

                with open(file_path, "r") as f:
                    settings = json.load(f)

                self.set_settings(settings)
                QMessageBox.information(
                    self, "Import Successful", f"Settings imported from:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Failed to import settings:\n{str(e)}")

    def export_settings(self):
        """Export settings to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "maya_publisher_settings.json",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            try:
                import json

                settings = self.get_settings()

                with open(file_path, "w") as f:
                    json.dump(settings, f, indent=2)

                QMessageBox.information(
                    self, "Export Successful", f"Settings exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export settings:\n{str(e)}")
