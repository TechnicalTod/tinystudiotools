"""Publish target fields and action buttons."""

from __future__ import annotations

from typing import List, Optional

from ...core.schema import AssetPublishSchema
from ..qt import QtWidgets, Signal


class PublishForm(QtWidgets.QWidget):
    """Asset name, variant, asset type, and publish actions."""

    publish_requested = Signal()
    load_requested = Signal()
    open_requested = Signal()
    refresh_requested = Signal()
    target_changed = Signal()

    def __init__(
        self,
        schema: AssetPublishSchema,
        default_variant: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._schema = schema
        self._category: Optional[str] = None

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        layout.addWidget(QtWidgets.QLabel("Asset name:"), 0, 0)
        self.asset_combo = QtWidgets.QComboBox()
        self.asset_combo.setEditable(True)
        self.asset_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.asset_combo.lineEdit().setPlaceholderText("Prop02")
        layout.addWidget(self.asset_combo, 0, 1)

        layout.addWidget(QtWidgets.QLabel("Variant:"), 0, 2)
        self.variant_edit = QtWidgets.QLineEdit(default_variant)
        self.variant_edit.setPlaceholderText("main")
        layout.addWidget(self.variant_edit, 0, 3)

        layout.addWidget(QtWidgets.QLabel("Asset type:"), 1, 0)
        self.type_combo = QtWidgets.QComboBox()
        for key in schema.publish_type_keys():
            spec = schema.get_publish_type(key)
            self.type_combo.addItem(spec.label, key)
        layout.addWidget(self.type_combo, 1, 1, 1, 3)

        self.publish_button = QtWidgets.QPushButton("Publish")
        self.publish_button.setDefault(True)
        self.load_button = QtWidgets.QPushButton("Load")
        self.load_button.setToolTip("Reference the selected publish into the current scene.")
        self.open_button = QtWidgets.QPushButton("Open")
        self.open_button.setToolTip("Open the selected publish as the current Maya scene.")
        self.refresh_button = QtWidgets.QPushButton("Refresh")

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.load_button)
        button_row.addWidget(self.open_button)
        button_row.addWidget(self.publish_button)
        layout.addLayout(button_row, 2, 0, 1, 4)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 0)

        self.publish_button.clicked.connect(self.publish_requested)
        self.load_button.clicked.connect(self.load_requested)
        self.open_button.clicked.connect(self.open_requested)
        self.refresh_button.clicked.connect(self.refresh_requested)

        self.asset_combo.currentTextChanged.connect(self._emit_target_changed)
        self.variant_edit.textChanged.connect(self._emit_target_changed)
        self.type_combo.currentIndexChanged.connect(self._emit_target_changed)

        self.set_load_enabled(False)
        self.set_open_enabled(False)

    def _emit_target_changed(self, *_args) -> None:
        self.target_changed.emit()

    def set_category(self, category: Optional[str], asset_names: List[str]) -> None:
        """Update the asset-name combo for the selected category."""
        self._category = category
        current = self.asset_combo.currentText()
        self.asset_combo.blockSignals(True)
        self.asset_combo.clear()
        self.asset_combo.addItems(asset_names)
        self.asset_combo.blockSignals(False)
        if current and current not in asset_names:
            self.asset_combo.setEditText(current)

    def set_asset_name(self, name: str) -> None:
        self.asset_combo.blockSignals(True)
        self.asset_combo.setEditText(name)
        self.asset_combo.blockSignals(False)

    def category(self) -> Optional[str]:
        return self._category

    def asset_name(self) -> str:
        return self.asset_combo.currentText().strip()

    def variant(self) -> str:
        return self.variant_edit.text()

    def publish_type(self) -> str:
        return str(self.type_combo.currentData())

    def set_publish_enabled(self, enabled: bool) -> None:
        self.publish_button.setEnabled(enabled)

    def set_load_enabled(self, enabled: bool) -> None:
        self.load_button.setEnabled(enabled)

    def set_open_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)
