"""
Validation Widget - Scene validation interface
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


class ValidationWidget(QWidget):
    """Widget for scene validation"""

    # Signals
    validation_requested = Signal(dict)  # Emit validation request

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        self.validation_results = []

    def setup_ui(self):
        """Setup the validation interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header section
        self.header_section = self.create_header_section()
        layout.addWidget(self.header_section)

        # Validation rules section
        self.rules_section = self.create_rules_section()
        layout.addWidget(self.rules_section)

        # Results section
        self.results_section = self.create_results_section()
        layout.addWidget(self.results_section)

    def create_header_section(self):
        """Create the header section"""
        group = QGroupBox("Scene Validation")
        layout = QVBoxLayout(group)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.validate_btn = QPushButton("🔍 Run Validation")
        self.validate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #1565C0; }
            QPushButton:disabled { background-color: #666; color: #999; }
        """
        )

        self.reset_btn = QPushButton("🔄 Reset")
        self.export_btn = QPushButton("📄 Export Report")
        self.export_btn.setEnabled(False)

        controls_layout.addWidget(self.validate_btn)
        controls_layout.addWidget(self.reset_btn)
        controls_layout.addWidget(self.export_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Status display
        status_layout = QHBoxLayout()

        self.overall_status_label = QLabel("Status: Ready to validate")
        self.overall_status_label.setStyleSheet("QLabel { font-weight: bold; color: #999; }")

        self.scene_info_label = QLabel("Scene: Loading...")
        self.scene_info_label.setStyleSheet("QLabel { color: #999; }")

        status_layout.addWidget(self.overall_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.scene_info_label)

        layout.addLayout(status_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return group

    def create_rules_section(self):
        """Create the validation rules section"""
        group = QGroupBox("Validation Rules")
        layout = QVBoxLayout(group)

        # Rules list
        self.rules_tree = QTreeWidget()
        self.rules_tree.setHeaderLabels(["Rule", "Status", "Description"])
        self.rules_tree.setAlternatingRowColors(True)
        self.rules_tree.setRootIsDecorated(False)

        # Populate with default rules
        self.populate_validation_rules()

        layout.addWidget(self.rules_tree)

        # Rule controls
        controls_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_none_btn = QPushButton("Select None")

        controls_layout.addWidget(self.select_all_btn)
        controls_layout.addWidget(self.select_none_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        return group

    def create_results_section(self):
        """Create the results section"""
        group = QGroupBox("Validation Results")
        layout = QVBoxLayout(group)

        # Summary
        summary_layout = QHBoxLayout()

        self.errors_label = QLabel("Errors: 0")
        self.errors_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")

        self.warnings_label = QLabel("Warnings: 0")
        self.warnings_label.setStyleSheet("QLabel { color: #ff9800; font-weight: bold; }")

        self.passed_label = QLabel("Passed: 0")
        self.passed_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")

        summary_layout.addWidget(self.errors_label)
        summary_layout.addWidget(self.warnings_label)
        summary_layout.addWidget(self.passed_label)
        summary_layout.addStretch()

        layout.addLayout(summary_layout)

        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Validation results will appear here...")

        layout.addWidget(self.results_text)

        return group

    def setup_connections(self):
        """Setup signal connections"""
        self.validate_btn.clicked.connect(self.run_validation)
        self.reset_btn.clicked.connect(self.reset_validation)
        self.export_btn.clicked.connect(self.export_report)
        self.select_all_btn.clicked.connect(self.select_all_rules)
        self.select_none_btn.clicked.connect(self.select_no_rules)

    def populate_validation_rules(self):
        """Populate the validation rules tree"""
        default_rules = [
            ("naming_convention", "Naming Convention", "Check scene and asset naming standards"),
            ("scene_cleanup", "Scene Cleanup", "Check for unused nodes and cleanup issues"),
            ("file_paths", "File Paths", "Check for missing files and broken references"),
            ("geometry", "Geometry", "Check geometry for common issues"),
            ("materials", "Materials", "Check material and shader setup"),
            ("references", "References", "Check reference files and paths"),
        ]

        for rule_id, rule_name, description in default_rules:
            item = QTreeWidgetItem(self.rules_tree)
            item.setText(0, rule_name)
            item.setText(1, "Not run")
            item.setText(2, description)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setData(0, Qt.UserRole, rule_id)

    def run_validation(self):
        """Run validation on selected rules"""
        # Get selected rules
        selected_rules = []
        for i in range(self.rules_tree.topLevelItemCount()):
            item = self.rules_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                rule_id = item.data(0, Qt.UserRole)
                selected_rules.append(rule_id)

        if not selected_rules:
            QMessageBox.warning(
                self, "No Rules Selected", "Please select at least one validation rule."
            )
            return

        # Update UI
        self.validate_btn.setEnabled(False)
        self.validate_btn.setText("Validating...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Create validation context
        validation_context = {"selected_rules": selected_rules, "scene_info": self.get_scene_info()}

        # Emit validation request
        self.validation_requested.emit(validation_context)

    def update_validation_results(self, results):
        """Update the validation results display"""
        self.validation_results = results

        # Update progress
        self.progress_bar.setVisible(False)
        self.validate_btn.setEnabled(True)
        self.validate_btn.setText("🔍 Run Validation")

        # Count results
        errors = 0
        warnings = 0
        passed = 0

        results_text = "Validation Results:\n" + "=" * 50 + "\n\n"

        # Update tree items and collect stats
        for i in range(self.rules_tree.topLevelItemCount()):
            item = self.rules_tree.topLevelItem(i)
            rule_id = item.data(0, Qt.UserRole)

            # Find result for this rule
            result = next(
                (
                    r
                    for r in results
                    if hasattr(r, "rule_name") and r.rule_name.lower().replace(" ", "_") == rule_id
                ),
                None,
            )

            if result:
                if result.passed:
                    item.setText(1, "✅ Passed")
                    item.setBackground(1, QColor(200, 255, 200))
                    passed += 1
                else:
                    if getattr(result, "errors", []):
                        item.setText(1, "❌ Failed")
                        item.setBackground(1, QColor(255, 200, 200))
                        errors += 1
                    else:
                        item.setText(1, "⚠️ Warning")
                        item.setBackground(1, QColor(255, 255, 200))
                        warnings += 1

                # Add to results text
                status = "PASSED" if result.passed else "FAILED"
                results_text += f"{result.rule_name}: {status}\n"

                if hasattr(result, "errors"):
                    for error in result.errors:
                        results_text += f"  ❌ ERROR: {error}\n"
                if hasattr(result, "warnings"):
                    for warning in result.warnings:
                        results_text += f"  ⚠️ WARNING: {warning}\n"

                results_text += "\n"

        # Update summary
        self.errors_label.setText(f"Errors: {errors}")
        self.warnings_label.setText(f"Warnings: {warnings}")
        self.passed_label.setText(f"Passed: {passed}")

        # Update overall status
        if errors > 0:
            self.overall_status_label.setText("Status: ❌ FAILED")
            self.overall_status_label.setStyleSheet("QLabel { font-weight: bold; color: #f44336; }")
        elif warnings > 0:
            self.overall_status_label.setText("Status: ⚠️ WARNINGS")
            self.overall_status_label.setStyleSheet("QLabel { font-weight: bold; color: #ff9800; }")
        else:
            self.overall_status_label.setText("Status: ✅ PASSED")
            self.overall_status_label.setStyleSheet("QLabel { font-weight: bold; color: #4CAF50; }")

        # Update results text
        self.results_text.setText(results_text)

        # Enable export button
        self.export_btn.setEnabled(True)

    def get_scene_info(self):
        """Get current scene information"""
        try:
            import maya.cmds as cmds

            scene_file = cmds.file(query=True, sceneName=True) or "Untitled"
            return {"scene_name": scene_file, "maya_available": True}
        except ImportError:
            return {"scene_name": "No scene (Maya not available)", "maya_available": False}

    def update_scene_info(self):
        """Update the scene info display"""
        scene_info = self.get_scene_info()
        scene_name = scene_info["scene_name"]
        if scene_name:
            import os

            scene_name = os.path.basename(scene_name)
        else:
            scene_name = "No scene loaded"

        self.scene_info_label.setText(f"Scene: {scene_name}")

    def select_all_rules(self):
        """Select all validation rules"""
        for i in range(self.rules_tree.topLevelItemCount()):
            item = self.rules_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def select_no_rules(self):
        """Deselect all validation rules"""
        for i in range(self.rules_tree.topLevelItemCount()):
            item = self.rules_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)

    def reset_validation(self):
        """Reset validation state"""
        self.validation_results = []
        self.results_text.clear()

        # Reset tree items
        for i in range(self.rules_tree.topLevelItemCount()):
            item = self.rules_tree.topLevelItem(i)
            item.setText(1, "Not run")
            item.setBackground(1, QColor())

        # Reset summary
        self.errors_label.setText("Errors: 0")
        self.warnings_label.setText("Warnings: 0")
        self.passed_label.setText("Passed: 0")

        # Reset status
        self.overall_status_label.setText("Status: Ready to validate")
        self.overall_status_label.setStyleSheet("QLabel { font-weight: bold; color: #999; }")

        # Disable export button
        self.export_btn.setEnabled(False)

    def export_report(self):
        """Export validation report"""
        if not self.validation_results:
            QMessageBox.warning(self, "No Results", "No validation results to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Validation Report",
            "validation_report.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.results_text.toPlainText())
                QMessageBox.information(
                    self, "Export Successful", f"Report exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{str(e)}")
