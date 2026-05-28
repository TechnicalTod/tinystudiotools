"""Variant + action button row."""

from __future__ import annotations

from typing import Optional

from ..qt import QtWidgets, Signal


class PublishForm(QtWidgets.QWidget):
    """Variant editor and Publish / Open / Refresh buttons."""

    publish_requested = Signal(str)   # variant
    open_requested = Signal()
    refresh_requested = Signal()

    def __init__(
        self,
        default_variant: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setHorizontalSpacing(8)

        variant_label = QtWidgets.QLabel("Variant:")
        self.variant_edit = QtWidgets.QLineEdit(default_variant)
        self.variant_edit.setPlaceholderText("main")
        self.variant_edit.setToolTip(
            "Filename variant tag. Use lowercase letters, digits, "
            "underscores and dashes. Each variant has its own version stream."
        )

        self.publish_button = QtWidgets.QPushButton("Publish")
        self.publish_button.setDefault(True)
        self.open_button = QtWidgets.QPushButton("Open Selected")
        self.refresh_button = QtWidgets.QPushButton("Refresh")

        layout.addWidget(variant_label, 0, 0)
        layout.addWidget(self.variant_edit, 0, 1)
        layout.addWidget(self.refresh_button, 0, 2)
        layout.addWidget(self.open_button, 0, 3)
        layout.addWidget(self.publish_button, 0, 4)
        layout.setColumnStretch(1, 1)

        self.publish_button.clicked.connect(self._emit_publish)
        self.open_button.clicked.connect(self.open_requested)
        self.refresh_button.clicked.connect(self.refresh_requested)

    def variant(self) -> str:
        return self.variant_edit.text()

    def set_publish_enabled(self, enabled: bool) -> None:
        self.publish_button.setEnabled(enabled)

    def set_open_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)

    def _emit_publish(self) -> None:
        self.publish_requested.emit(self.variant())
