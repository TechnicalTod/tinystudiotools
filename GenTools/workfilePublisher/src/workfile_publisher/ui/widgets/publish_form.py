"""Variant, workfile type, top-level name, and action button row."""

from __future__ import annotations

from typing import List, Optional

from ...core import path_schema as ps
from ..qt import QtWidgets, Signal


def _task_label(task: str) -> str:
    return task.replace("_", " ").title()


class PublishForm(QtWidgets.QWidget):
    """Top-level name, workfile type, variant editor, and Publish / Open / Refresh."""

    publish_requested = Signal(str)  # variant
    open_requested = Signal()
    refresh_requested = Signal()
    target_changed = Signal()

    def __init__(
        self,
        schema: ps.PathSchema,
        dcc: str,
        default_variant: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._schema = schema
        self._dcc = dcc
        self._context_kind: Optional[str] = None

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        self._name_label = QtWidgets.QLabel("Asset name:")
        layout.addWidget(self._name_label, 0, 0)
        self.name_combo = QtWidgets.QComboBox()
        self.name_combo.setEditable(True)
        self.name_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.name_combo.setEnabled(False)
        self.name_combo.lineEdit().setPlaceholderText("Prop02")
        layout.addWidget(self.name_combo, 0, 1)

        layout.addWidget(QtWidgets.QLabel("Variant:"), 0, 2)
        self.variant_edit = QtWidgets.QLineEdit(default_variant)
        self.variant_edit.setPlaceholderText("main")
        self.variant_edit.setToolTip(
            "Filename variant tag. Use lowercase letters, digits, "
            "underscores and dashes. Each variant has its own version stream."
        )
        layout.addWidget(self.variant_edit, 0, 3)

        layout.addWidget(QtWidgets.QLabel("Workfile type:"), 1, 0)
        self.task_combo = QtWidgets.QComboBox()
        self.task_combo.setEnabled(False)
        layout.addWidget(self.task_combo, 1, 1, 1, 3)

        self.publish_button = QtWidgets.QPushButton("Publish")
        self.publish_button.setDefault(True)
        self.open_button = QtWidgets.QPushButton("Open Selected")
        self.refresh_button = QtWidgets.QPushButton("Refresh")

        layout.addWidget(self.refresh_button, 2, 2)
        layout.addWidget(self.open_button, 2, 3)
        layout.addWidget(self.publish_button, 2, 4)
        layout.setColumnStretch(1, 1)

        self.publish_button.clicked.connect(self._emit_publish)
        self.open_button.clicked.connect(self.open_requested)
        self.refresh_button.clicked.connect(self.refresh_requested)

        self.name_combo.currentTextChanged.connect(self._emit_target_changed)
        self.task_combo.currentIndexChanged.connect(self._emit_target_changed)
        self.variant_edit.textChanged.connect(self._emit_target_changed)

    def _emit_target_changed(self, *_args) -> None:
        self.target_changed.emit()

    def set_context(self, kind: Optional[str]) -> None:
        """Republish the task combo for ``"asset"``, ``"shot"``, or clear."""
        self._context_kind = kind
        self.task_combo.blockSignals(True)
        self.task_combo.clear()
        if kind is None:
            self.task_combo.setEnabled(False)
            self.task_combo.blockSignals(False)
            return

        dcc_spec = self._schema.get_dcc(self._dcc)
        for task in dcc_spec.tasks_for(kind):
            self.task_combo.addItem(_task_label(task), task)
        self.task_combo.setEnabled(True)
        self.task_combo.blockSignals(False)

    def set_name_context(self, kind: Optional[str], names: List[str]) -> None:
        """Update the top-level name combo for the selected tree parent."""
        current = self.name_combo.currentText()
        self.name_combo.blockSignals(True)
        self.name_combo.clear()
        if kind == "asset":
            self._name_label.setText("Asset name:")
            self.name_combo.lineEdit().setPlaceholderText("Prop02")
            self.name_combo.addItems(names)
            self.name_combo.setEnabled(True)
        elif kind == "shot":
            self._name_label.setText("Shot name:")
            self.name_combo.lineEdit().setPlaceholderText("Set by production")
            self.name_combo.setEditText("")
            self.name_combo.setEnabled(False)
        else:
            self.name_combo.setEditText("")
            self.name_combo.setEnabled(False)
        self.name_combo.blockSignals(False)
        if kind == "asset" and current and current not in names:
            self.name_combo.setEditText(current)

    def set_top_level_name(self, name: str) -> None:
        self.name_combo.blockSignals(True)
        self.name_combo.setEditText(name)
        self.name_combo.blockSignals(False)

    def top_level_name(self) -> str:
        return self.name_combo.currentText().strip()

    def set_task(self, task: str) -> None:
        index = self.task_combo.findData(task)
        if index < 0:
            return
        self.task_combo.blockSignals(True)
        self.task_combo.setCurrentIndex(index)
        self.task_combo.blockSignals(False)

    def task(self) -> str:
        data = self.task_combo.currentData()
        return str(data) if data else ""

    def variant(self) -> str:
        return self.variant_edit.text()

    def set_publish_enabled(self, enabled: bool) -> None:
        self.publish_button.setEnabled(enabled)

    def set_open_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)

    def _emit_publish(self) -> None:
        self.publish_requested.emit(self.variant())
