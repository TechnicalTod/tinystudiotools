"""
Settings dialog for TunnelUI Asset Browser.

This module provides a comprehensive settings dialog for configuring the application.
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTabWidget,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QTextEdit,
    QComboBox,
    QSlider,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """Configuration dialog for application settings"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("TunnelUI Settings")
        self.setModal(True)
        self.resize(600, 500)

        # Apply checkbox fix styling
        self._apply_checkbox_fix()

        self._setup_ui()
        self._load_current_values()

    def _apply_checkbox_fix(self):
        """Apply checkbox styling fix for better visibility"""
        checkbox_style = """
        QCheckBox {
            color: #ffffff;
            background-color: transparent;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #666666;
            border-radius: 3px;
            background-color: #2b2b2b;
        }
        
        QCheckBox::indicator:hover {
            border: 2px solid #888888;
            background-color: #3c3c3c;
        }
        
        QCheckBox::indicator:checked {
            border: 2px solid #4CAF50;
            background-color: #4CAF50;
        }
        
        QCheckBox::indicator:checked:hover {
            border: 2px solid #5CBF60;
            background-color: #5CBF60;
        }
        
        QCheckBox::indicator:disabled {
            border: 2px solid #444444;
            background-color: #1a1a1a;
        }
        
        QGroupBox {
            color: #ffffff;
            font-weight: bold;
            border: 2px solid #666666;
            border-radius: 5px;
            margin: 10px 0px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0px 5px 0px 5px;
            color: #4CAF50;
        }
        """

        self.setStyleSheet(checkbox_style)

    def _setup_ui(self):
        """Setup the settings dialog UI"""
        layout = QVBoxLayout(self)

        # Create tabs
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Create tabs
        paths_tab = self._create_paths_tab()
        display_tab = self._create_display_tab()
        performance_tab = self._create_performance_tab()
        advanced_tab = self._create_advanced_tab()

        tab_widget.addTab(paths_tab, "Paths")
        tab_widget.addTab(display_tab, "Display")
        tab_widget.addTab(performance_tab, "Performance")
        tab_widget.addTab(advanced_tab, "Advanced")

        # Add Maya Import tab if Maya is available
        if hasattr(self.config, "maya_settings") and self.config.maya_settings:
            maya_tab = self._create_maya_import_tab()
            tab_widget.addTab(maya_tab, "Maya Import")

        # Buttons
        button_layout = QHBoxLayout()

        self.validate_button = QPushButton("Validate Paths")
        self.reset_button = QPushButton("Reset to Defaults")
        self.cancel_button = QPushButton("Cancel")
        self.apply_button = QPushButton("Apply")
        self.ok_button = QPushButton("OK")

        # Connect buttons
        self.validate_button.clicked.connect(self._validate_paths)
        self.reset_button.clicked.connect(self._reset_to_defaults)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self._apply_settings)
        self.ok_button.clicked.connect(self._ok_clicked)

        button_layout.addWidget(self.validate_button)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def _create_paths_tab(self) -> QGroupBox:
        """Create paths configuration tab"""
        widget = QGroupBox("Asset Library Paths")
        layout = QFormLayout(widget)

        # Metadata path
        self.metadata_path_edit = QLineEdit()
        metadata_browse = QPushButton("Browse...")
        metadata_browse.clicked.connect(
            lambda: self._browse_folder(self.metadata_path_edit, "Select Metadata Folder")
        )

        metadata_layout = QHBoxLayout()
        metadata_layout.addWidget(self.metadata_path_edit)
        metadata_layout.addWidget(metadata_browse)
        layout.addRow("Metadata Folder:", metadata_layout)

        # Assets path
        self.assets_path_edit = QLineEdit()
        assets_browse = QPushButton("Browse...")
        assets_browse.clicked.connect(
            lambda: self._browse_folder(self.assets_path_edit, "Select Assets Folder")
        )

        assets_layout = QHBoxLayout()
        assets_layout.addWidget(self.assets_path_edit)
        assets_layout.addWidget(assets_browse)
        layout.addRow("Assets Folder:", assets_layout)

        return widget

    def _create_display_tab(self) -> QGroupBox:
        """Create display options tab"""
        widget = QGroupBox("Thumbnail Settings")
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

    def _create_performance_tab(self) -> QGroupBox:
        """Create performance options tab"""
        widget = QGroupBox("Image Loading")
        layout = QFormLayout(widget)

        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 20)
        layout.addRow("Max Concurrent Loads:", self.max_threads_spin)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        layout.addRow("Image Cache Size:", self.cache_size_spin)

        return widget

    def _create_advanced_tab(self) -> QGroupBox:
        """Create advanced options tab"""
        widget = QGroupBox("Debug & Logging")
        layout = QFormLayout(widget)

        self.debug_check = QCheckBox()
        layout.addRow("Debug Mode:", self.debug_check)

        # Environment information tab
        env_layout = QVBoxLayout()

        env_info = QTextEdit()
        env_info.setReadOnly(True)
        try:
            # Get configuration and environment info
            config = self.config_manager.get_config()

            # Create environment info text
            env_text = []
            env_text.append("=== TunnelUI Environment Information ===\n")

            # Basic configuration
            env_text.append(f"Configuration Path: {self.config_manager.config_path}")
            env_text.append(f"Target Application: {config.target_application}")
            env_text.append(f"Application Override: {config.application_override or 'None'}")
            env_text.append(f"Maya Mode: {config.maya_mode}")
            env_text.append(f"Debug Mode: {config.debug_mode}\n")

            # Try to get current environment if available
            try:
                from configuration.config_models import AppEnvironment

                env = AppEnvironment()
                available_apps = env.detect_all_applications()

                env_text.append("=== Available Applications ===")
                for app, caps in available_apps.items():
                    env_text.append(f"- {app.value}: {caps.name}")
                    if caps.version:
                        env_text.append(f"  Version: {caps.version}")
                    env_text.append(
                        f"  Python API: {'Available' if caps.python_api_available else 'Not Available'}"
                    )

                active_app = env.get_active_application()
                env_text.append(f"\nActive Application: {active_app.value}")
                env_text.append(f"Import Button Text: {env.get_import_button_text()}")

            except Exception as e:
                env_text.append(f"Environment detection error: {e}")

            env_info.setText("\n".join(env_text))

        except Exception as e:
            env_info.setText(f"Failed to load environment information: {e}")

        env_layout.addWidget(QLabel("Environment Information:"))
        env_layout.addWidget(env_info)

        return widget

    def _create_maya_import_tab(self) -> QGroupBox:
        """Create Maya Import settings tab"""
        widget = QGroupBox("Maya Import Settings")
        layout = QFormLayout(widget)

        # Import Cache Settings
        cache_header = QLabel("<b>Import Cache Settings</b>")
        layout.addRow(cache_header)

        self.maya_use_cache_check = QCheckBox()
        layout.addRow("Enable Import Cache:", self.maya_use_cache_check)

        self.maya_cache_location_edit = QLineEdit()
        cache_browse = QPushButton("Browse...")
        cache_browse.clicked.connect(
            lambda: self._browse_folder(self.maya_cache_location_edit, "Select Cache Directory")
        )
        layout.addRow("Cache Location:", self.maya_cache_location_edit)
        layout.addRow("", cache_browse)

        self.maya_cache_size_spin = QSpinBox()
        self.maya_cache_size_spin.setRange(1, 100)
        self.maya_cache_size_spin.setSuffix(" GB")
        layout.addRow("Max Cache Size:", self.maya_cache_size_spin)

        # Material Settings
        material_header = QLabel("<b>Material Creation</b>")
        layout.addRow(material_header)

        self.maya_create_materials_check = QCheckBox()
        layout.addRow("Create Materials:", self.maya_create_materials_check)

        self.maya_material_type_combo = QComboBox()
        self.maya_material_type_combo.addItems(["USD Preview Surface"])
        layout.addRow("Material Type:", self.maya_material_type_combo)

        # Texture Settings
        texture_header = QLabel("<b>Texture Processing</b>")
        layout.addRow(texture_header)

        self.maya_process_textures_check = QCheckBox()
        layout.addRow("Process Textures:", self.maya_process_textures_check)

        # Individual Texture Type Controls
        texture_types_header = QLabel("<b>Texture Types to Import</b>")
        layout.addRow(texture_types_header)

        # Create checkboxes for each texture type
        self.texture_checkboxes = {}
        texture_types = [
            ("diffuse", "Diffuse (Albedo)"),
            ("normal", "Normal"),
            ("roughness", "Roughness"),
            ("metallic", "Metallic"),
            ("ao", "Ambient Occlusion"),
            ("displacement", "Displacement"),
            ("emissive", "Emissive"),
            ("opacity", "Opacity"),
        ]

        for texture_type, display_name in texture_types:
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Default to all enabled
            self.texture_checkboxes[texture_type] = checkbox
            layout.addRow(f"{display_name}:", checkbox)

        self.maya_texture_format_combo = QComboBox()
        self.maya_texture_format_combo.addItems(["png", "jpg", "exr"])
        layout.addRow("Texture Format:", self.maya_texture_format_combo)

        self.maya_texture_resolution_combo = QComboBox()
        self.maya_texture_resolution_combo.addItems(["1K", "2K", "4K", "original"])
        layout.addRow("Texture Resolution:", self.maya_texture_resolution_combo)

        # Import Behavior
        behavior_header = QLabel("<b>Import Behavior</b>")
        layout.addRow(behavior_header)

        self.maya_organize_groups_check = QCheckBox()
        layout.addRow("Organize in Groups:", self.maya_organize_groups_check)

        return widget

    def _browse_folder(self, line_edit: QLineEdit, title: str):
        """Open folder browser dialog"""
        current_path = line_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, title, current_path)
        if folder:
            line_edit.setText(folder)

    def _browse_file(self, line_edit: QLineEdit, title: str):
        """Open file browser dialog"""
        current_path = line_edit.text() or str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(self, title, current_path, "All Files (*)")
        if file_path:
            line_edit.setText(file_path)

    def _load_current_values(self):
        """Load current configuration values into UI"""
        self.metadata_path_edit.setText(self.config.metadata_path)
        self.assets_path_edit.setText(self.config.assets_path)
        self.thumbnail_size_spin.setValue(self.config.thumbnail_size)
        self.grid_spacing_spin.setValue(self.config.grid_spacing)
        self.max_threads_spin.setValue(self.config.max_concurrent_loads)
        self.cache_size_spin.setValue(self.config.cache_size)
        self.debug_check.setChecked(self.config.debug_mode)

        # Load Maya import settings if available
        if hasattr(self.config, "maya_settings") and self.config.maya_settings:
            maya_settings = self.config.maya_settings
            self.maya_use_cache_check.setChecked(maya_settings.use_import_cache)
            self.maya_cache_location_edit.setText(maya_settings.cache_location)
            self.maya_cache_size_spin.setValue(int(maya_settings.cache_max_size_gb))
            self.maya_create_materials_check.setChecked(maya_settings.create_materials)
            self.maya_material_type_combo.setCurrentText(maya_settings.material_type)
            self.maya_process_textures_check.setChecked(maya_settings.process_textures)
            self.maya_texture_format_combo.setCurrentText(maya_settings.texture_format)
            self.maya_texture_resolution_combo.setCurrentText(maya_settings.texture_resolution)
            self.maya_organize_groups_check.setChecked(maya_settings.organize_in_groups)

            # Load texture type selections
            if hasattr(maya_settings, "enabled_texture_types"):
                for texture_type, checkbox in self.texture_checkboxes.items():
                    enabled = maya_settings.enabled_texture_types.get(texture_type, True)
                    checkbox.setChecked(enabled)

    def _validate_paths(self):
        """Validate the configured paths"""
        try:
            # Update config with current UI values
            self._update_config_from_ui()

            # Basic path validation (fast)
            validation_results = self.config_manager.validate_paths()

            # Update validation status
            status_lines = []
            all_valid = True

            for path_name, is_valid in validation_results.items():
                status = "✅" if is_valid else "❌"
                status_lines.append(f"{status} {path_name}")
                if not is_valid:
                    all_valid = False

            status_text = "\n".join(status_lines)
            self.validation_status_label.setText(status_text)

            if all_valid:
                # Only do full library validation if basic paths are valid
                # This is expensive so we do it here, not on startup
                try:
                    self.logger.info("Running full library validation (this may take a moment)...")

                    # Import asset management service here to avoid circular imports
                    from ..services.asset_management_service import AssetManagementService
                    from ..data import FileSystemMetadataRepository, FileSystemImportRepository

                    # Create temporary services for validation
                    metadata_repo = FileSystemMetadataRepository(self.config)
                    import_repo = FileSystemImportRepository(self.config)
                    asset_service = AssetManagementService(metadata_repo, import_repo)

                    # Run full validation
                    library_validation = asset_service.validate_library_integrity()

                    if library_validation["overall_status"] == "healthy":
                        QMessageBox.information(
                            self, "Validation", "✅ All paths and library files are valid!"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Validation",
                            f"⚠️ Library validation: {library_validation['overall_status']}",
                        )

                except Exception as e:
                    self.logger.warning(f"Library validation failed: {e}")
                    QMessageBox.information(
                        self,
                        "Validation",
                        "✅ Basic paths are valid!\n\n⚠️ Full library validation failed - check logs for details.",
                    )
            else:
                QMessageBox.warning(
                    self, "Validation", "❌ Some paths are invalid. Please check configuration."
                )

        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            QMessageBox.critical(self, "Validation Error", f"Path validation failed:\n{e}")

    def _update_config_from_ui(self):
        """Update config object with current UI values"""
        self.config.metadata_path = self.metadata_path_edit.text()
        self.config.assets_path = self.assets_path_edit.text()
        self.config.thumbnail_size = self.thumbnail_size_spin.value()
        self.config.grid_spacing = self.grid_spacing_spin.value()
        self.config.max_concurrent_loads = self.max_threads_spin.value()
        self.config.cache_size = self.cache_size_spin.value()
        self.config.debug_mode = self.debug_check.isChecked()

        # FIX: Add Maya import settings update (was missing!)
        if hasattr(self.config, "maya_settings") and self.config.maya_settings:
            maya_settings = self.config.maya_settings
            maya_settings.use_import_cache = self.maya_use_cache_check.isChecked()
            maya_settings.cache_location = self.maya_cache_location_edit.text()
            maya_settings.cache_max_size_gb = float(self.maya_cache_size_spin.value())
            maya_settings.create_materials = self.maya_create_materials_check.isChecked()
            maya_settings.material_type = self.maya_material_type_combo.currentText()
            maya_settings.process_textures = self.maya_process_textures_check.isChecked()
            maya_settings.texture_format = self.maya_texture_format_combo.currentText()
            maya_settings.texture_resolution = self.maya_texture_resolution_combo.currentText()
            maya_settings.organize_in_groups = self.maya_organize_groups_check.isChecked()

            # Save texture type selections
            maya_settings.enabled_texture_types = {}
            for texture_type, checkbox in self.texture_checkboxes.items():
                maya_settings.enabled_texture_types[texture_type] = checkbox.isChecked()

    def _apply_settings(self):
        """Apply current settings"""
        try:
            self._update_config_from_ui()

            if self.config_manager.save_config():
                QMessageBox.information(self, "Settings", "Settings saved successfully! ✅")
                self.logger.info("Settings applied successfully")
            else:
                QMessageBox.warning(self, "Settings", "Failed to save settings.")

        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            QMessageBox.critical(self, "Settings Error", f"Failed to apply settings:\n{e}")

    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to defaults?\n\nThis will restore the original configuration.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if self.config_manager.reset_to_defaults():
                    self.config = self.config_manager.get_config()
                    self._load_current_values()
                    QMessageBox.information(
                        self, "Reset", "Settings reset to defaults successfully! ✅"
                    )
                else:
                    QMessageBox.warning(self, "Reset", "Failed to reset settings to defaults.")
            except Exception as e:
                self.logger.error(f"Failed to reset settings: {e}")
                QMessageBox.critical(self, "Reset Error", f"Failed to reset settings:\n{e}")

    def _ok_clicked(self):
        """Handle OK button click"""
        self._apply_settings()
        self.accept()

    def get_updated_config(self):
        """Get the updated configuration"""
        self._update_config_from_ui()
        return self.config
