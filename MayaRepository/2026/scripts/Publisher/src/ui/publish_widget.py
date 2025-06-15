"""
Publish Widget - Main publishing interface
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


class PublishWidget(QWidget):
    """Widget for the publish tab interface"""

    # Signals
    validation_requested = Signal()
    publish_requested = Signal(dict)  # Emit publish data
    version_update_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the publish interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Publish form
        self.publish_form = self.create_publish_form()
        layout.addWidget(self.publish_form)

        # Validation section
        self.validation_section = self.create_validation_section()
        layout.addWidget(self.validation_section)

        layout.addStretch()

    def create_publish_form(self):
        """Create the publish form section"""
        group = QGroupBox("Publish Information")
        group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                color: #4A90E2;
                border: 1px solid #666666;
                border-radius: 5px;
                margin: 5px 0px;
                padding-top: 15px;
                background-color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #4A90E2;
            }
        """
        )

        layout = QFormLayout(group)
        layout.setSpacing(10)

        # Show dropdown
        self.show_combo = QComboBox()
        self.show_combo.setEditable(True)
        self.show_combo.setToolTip("Select or enter the show name")

        # Asset type
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(["asset", "shot"])
        self.asset_type_combo.setToolTip("Select asset or shot type")

        # Asset ID
        self.asset_id_edit = QLineEdit()
        self.asset_id_edit.setPlaceholderText("Enter asset/shot ID...")
        self.asset_id_edit.setToolTip("Unique identifier for the asset or shot")

        # Task dropdown
        self.task_combo = QComboBox()
        self.task_combo.setEditable(True)
        self.task_combo.setToolTip("Select the task (model, texture, rig, etc.)")

        # Version (auto-generated, read-only)
        self.version_label = QLabel("v001")
        self.version_label.setStyleSheet(
            """
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #4A90E2;
                font-weight: bold;
                font-family: monospace;
            }
        """
        )
        self.version_label.setToolTip("Auto-generated version number")

        # Comments
        self.comments_edit = QTextEdit()
        self.comments_edit.setMaximumHeight(80)
        self.comments_edit.setPlaceholderText("Optional publish comments...")
        self.comments_edit.setToolTip("Describe changes or notes for this publish")

        # Artist (read-only)
        self.artist_label = QLabel("Unknown")
        self.artist_label.setStyleSheet(
            """
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #cccccc;
            }
        """
        )

        # Add to layout
        layout.addRow("Show:", self.show_combo)
        layout.addRow("Type:", self.asset_type_combo)
        layout.addRow("Asset/Shot ID:", self.asset_id_edit)
        layout.addRow("Task:", self.task_combo)
        layout.addRow("Version:", self.version_label)
        layout.addRow("Artist:", self.artist_label)
        layout.addRow("Comments:", self.comments_edit)

        return group

    def create_validation_section(self):
        """Create the validation section"""
        group = QGroupBox("Scene Validation")
        group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                color: #FF9800;
                border: 1px solid #666666;
                border-radius: 5px;
                margin: 5px 0px;
                padding-top: 15px;
                background-color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #FF9800;
            }
        """
        )

        layout = QVBoxLayout(group)

        # Validation controls
        controls_layout = QHBoxLayout()

        self.validate_btn = QPushButton("🔍 Run Validation")
        self.validate_btn.setToolTip("Run scene validation checks")
        self.validate_btn.clicked.connect(self.validation_requested.emit)

        self.validation_status = QLabel("Not validated")
        self.validation_status.setStyleSheet("QLabel { color: #cccccc; }")

        controls_layout.addWidget(self.validate_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.validation_status)

        # Validation results
        self.validation_results = QTextEdit()
        self.validation_results.setMaximumHeight(150)
        self.validation_results.setReadOnly(True)
        self.validation_results.setPlaceholderText("Validation results will appear here...")

        layout.addLayout(controls_layout)
        layout.addWidget(self.validation_results)

        return group

    def setup_connections(self):
        """Setup signal connections"""
        self.show_combo.currentTextChanged.connect(self.on_form_changed)
        self.asset_type_combo.currentTextChanged.connect(self.on_form_changed)
        self.asset_id_edit.textChanged.connect(self.on_form_changed)
        self.task_combo.currentTextChanged.connect(self.on_form_changed)

    def on_form_changed(self):
        """Handle form field changes"""
        self.version_update_requested.emit()

    def get_publish_data(self):
        """Get current publish data from form"""
        return {
            "show_name": self.show_combo.currentText(),
            "asset_type": self.asset_type_combo.currentText(),
            "asset_id": self.asset_id_edit.text(),
            "task": self.task_combo.currentText(),
            "version": self.version_label.text(),
            "comments": self.comments_edit.toPlainText(),
            "artist": self.artist_label.text(),
        }

    def set_publish_data(self, data):
        """Set form data"""
        if "show_name" in data and data["show_name"]:
            self.show_combo.setCurrentText(data["show_name"])

        if "asset_type" in data and data["asset_type"]:
            self.asset_type_combo.setCurrentText(data["asset_type"])

        if "asset_id" in data and data["asset_id"]:
            self.asset_id_edit.setText(data["asset_id"])

        if "task" in data and data["task"]:
            self.task_combo.setCurrentText(data["task"])

        if "version" in data:
            self.version_label.setText(data["version"])

        if "artist" in data:
            self.artist_label.setText(data["artist"])

    def update_show_list(self, shows):
        """Update the show dropdown"""
        current_text = self.show_combo.currentText()
        self.show_combo.clear()
        self.show_combo.addItems(shows)
        if current_text:
            self.show_combo.setCurrentText(current_text)

    def update_task_list(self, tasks):
        """Update the task dropdown"""
        current_text = self.task_combo.currentText()
        self.task_combo.clear()
        self.task_combo.addItems(tasks)
        if current_text:
            self.task_combo.setCurrentText(current_text)

    def update_version_display(self, version):
        """Update version display"""
        if isinstance(version, int):
            self.version_label.setText(f"v{version:03d}")
        else:
            self.version_label.setText(str(version))

    def set_validation_status(self, passed, errors=0, warnings=0):
        """Update validation status"""
        if passed:
            self.validation_status.setText("✅ PASSED")
            self.validation_status.setStyleSheet(
                """
                QLabel { 
                    color: #4CAF50; 
                    font-weight: bold; 
                }
            """
            )
        else:
            self.validation_status.setText("❌ FAILED")
            self.validation_status.setStyleSheet(
                """
                QLabel { 
                    color: #f44336; 
                    font-weight: bold; 
                }
            """
            )

    def set_validation_results(self, results_text):
        """Set validation results text"""
        self.validation_results.setText(results_text)

    def set_validation_running(self, running=True):
        """Set validation running state"""
        if running:
            self.validate_btn.setEnabled(False)
            self.validate_btn.setText("Validating...")
        else:
            self.validate_btn.setEnabled(True)
            self.validate_btn.setText("🔍 Run Validation")

    def is_form_valid(self):
        """Check if form has valid data for publishing"""
        return all(
            [
                self.show_combo.currentText().strip(),
                self.asset_id_edit.text().strip(),
                self.task_combo.currentText().strip(),
            ]
        )
