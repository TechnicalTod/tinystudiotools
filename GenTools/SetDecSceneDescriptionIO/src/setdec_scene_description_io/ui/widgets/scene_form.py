"""Environment, variant, and import/export action row."""

from __future__ import annotations

from typing import List, Optional

from ...core.paths import SceneSchema
from ..qt import QtWidgets, Signal


class SceneForm(QtWidgets.QWidget):
    """Environment name, variant editor, and Import / Export / Refresh actions."""

    export_requested = Signal()
    import_requested = Signal()
    refresh_requested = Signal()
    target_changed = Signal()

    def __init__(
        self,
        schema: SceneSchema,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._schema = schema

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        layout.addWidget(QtWidgets.QLabel("Environment:"), 0, 0)
        self.env_combo = QtWidgets.QComboBox()
        self.env_combo.setEditable(True)
        self.env_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.env_combo.lineEdit().setPlaceholderText("BigPissDungeon")
        layout.addWidget(self.env_combo, 0, 1)

        layout.addWidget(QtWidgets.QLabel("Variant:"), 0, 2)
        self.variant_edit = QtWidgets.QLineEdit(schema.default_variant)
        self.variant_edit.setPlaceholderText(schema.default_variant)
        layout.addWidget(self.variant_edit, 0, 3)

        layout.addWidget(QtWidgets.QLabel("Next version:"), 1, 0)
        self.next_version_label = QtWidgets.QLabel("v001")
        layout.addWidget(self.next_version_label, 1, 1)

        self.export_button = QtWidgets.QPushButton("Export Scene")
        self.export_button.setDefault(True)
        self.import_button = QtWidgets.QPushButton("Import Selected")
        self.import_button.setToolTip("Rebuild the scene from the selected published description.")
        self.refresh_button = QtWidgets.QPushButton("Refresh")

        layout.addWidget(self.refresh_button, 2, 2)
        layout.addWidget(self.import_button, 2, 3)
        layout.addWidget(self.export_button, 2, 4)
        layout.setColumnStretch(1, 1)

        self.export_button.clicked.connect(self.export_requested)
        self.import_button.clicked.connect(self.import_requested)
        self.refresh_button.clicked.connect(self.refresh_requested)

        self.env_combo.currentTextChanged.connect(self._emit_target_changed)
        self.variant_edit.textChanged.connect(self._emit_target_changed)

        self.set_import_enabled(False)

    def _emit_target_changed(self, *_args) -> None:
        self.target_changed.emit()

    def set_environments(self, names: List[str]) -> None:
        current = self.env_combo.currentText()
        self.env_combo.blockSignals(True)
        self.env_combo.clear()
        self.env_combo.addItems(names)
        self.env_combo.blockSignals(False)
        if current:
            self.env_combo.setEditText(current)

    def set_environment(self, name: str) -> None:
        self.env_combo.setEditText(name)

    def set_variant(self, variant: str) -> None:
        self.variant_edit.setText(variant)

    def environment(self) -> str:
        return self.env_combo.currentText().strip()

    def variant(self) -> str:
        return self.variant_edit.text().strip()

    def set_next_version(self, label: str) -> None:
        self.next_version_label.setText(label)

    def set_import_enabled(self, enabled: bool) -> None:
        self.import_button.setEnabled(enabled)

    def set_export_enabled(self, enabled: bool) -> None:
        self.export_button.setEnabled(enabled)
