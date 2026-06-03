"""Screenshot preview and pickers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..qt import Qt, QtCore, QtGui, QtWidgets, Signal

_PREVIEW_WIDTH = 330
_PREVIEW_HEIGHT = 240


class ScreenshotPanel(QtWidgets.QGroupBox):
    screenshot_changed = Signal(object)  # Path | None

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Screenshot", parent)
        self._path: Optional[Path] = None
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Maximum,
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self._preview = QtWidgets.QLabel("No image")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setFixedSize(_PREVIEW_WIDTH, _PREVIEW_HEIGHT)
        self._preview.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._preview.setStyleSheet(
            "background: #2b2b2b; color: #b0b0b0; border: 1px solid #555555;"
        )
        self._preview.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed,
        )
        layout.addWidget(self._preview, 0, Qt.AlignHCenter)
        layout.addSpacing(4)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)
        self.capture_btn = QtWidgets.QPushButton("Capture")
        self.clear_btn = QtWidgets.QPushButton("Clear")
        row.addStretch(1)
        row.addWidget(self.capture_btn)
        row.addWidget(self.clear_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.clear_btn.clicked.connect(self.clear)

    def screenshot_path(self) -> Optional[Path]:
        """Path attached to the next publish (viewport capture)."""
        return self._path

    def set_image_path(self, path: Optional[Path]) -> None:
        """Set preview and the image used on the next publish."""
        self._path = path
        self._apply_preview(path)
        self.screenshot_changed.emit(self._path)

    def display_image(self, path: Optional[Path]) -> None:
        """Show a preview only (e.g. from a selected publish); does not change publish attachment."""
        self._apply_preview(path)

    def _apply_preview(self, path: Optional[Path]) -> None:
        if path and path.is_file():
            pix = QtGui.QPixmap(str(path))
            if not pix.isNull():
                self._preview.setText("")
                self._preview.setPixmap(self._scaled_pixmap(pix))
                return
        self._preview.setPixmap(QtGui.QPixmap())
        self._preview.setText("No image" if path is None else "Invalid image")

    @staticmethod
    def _scaled_pixmap(source: QtGui.QPixmap) -> QtGui.QPixmap:
        """Scale to the fixed preview area without changing the label size."""
        return source.scaled(
            _PREVIEW_WIDTH,
            _PREVIEW_HEIGHT,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )

    def clear(self) -> None:
        self.set_image_path(None)
