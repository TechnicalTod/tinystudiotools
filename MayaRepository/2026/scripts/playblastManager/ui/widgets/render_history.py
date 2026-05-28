"""Render history table with first-frame preview."""

from __future__ import annotations

from typing import List, Optional

from ..qt import Qt, QtGui, QtWidgets, Signal
from ...core.discovery import RenderRecord


class RenderHistoryWidget(QtWidgets.QGroupBox):
    selection_changed = Signal(object)  # Optional[RenderRecord]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Render History", parent)
        outer = QtWidgets.QVBoxLayout(self)

        toolbar = QtWidgets.QHBoxLayout()
        self._refresh_btn = QtWidgets.QPushButton("Refresh")
        toolbar.addWidget(self._refresh_btn)
        toolbar.addStretch(1)
        outer.addLayout(toolbar)

        splitter = QtWidgets.QSplitter(Qt.Horizontal)

        self._table = QtWidgets.QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Camera", "Version", "Frames", "Created"])
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        splitter.addWidget(self._table)

        preview_box = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_box)
        self._preview = QtWidgets.QLabel("Select a render to preview")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setMinimumSize(240, 180)
        self._preview.setStyleSheet(
            "QLabel { background: #2b2b2b; color: #b0b0b0; border: 1px solid #555555; }"
        )
        self._preview.setScaledContents(False)
        preview_layout.addWidget(self._preview, 1)

        self._open_folder_btn = QtWidgets.QPushButton("Open Folder")
        self._open_folder_btn.setEnabled(False)
        preview_layout.addWidget(self._open_folder_btn)

        splitter.addWidget(preview_box)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        self._records: List[RenderRecord] = []
        self._table.itemSelectionChanged.connect(self._on_selection)

    def refresh_button(self) -> QtWidgets.QPushButton:
        return self._refresh_btn

    def open_folder_button(self) -> QtWidgets.QPushButton:
        return self._open_folder_btn

    def set_records(self, records: List[RenderRecord]) -> None:
        self._records = list(records)
        self._table.setRowCount(len(records))
        for row, rec in enumerate(records):
            for col, text in enumerate(
                (
                    rec.camera,
                    f"v{rec.version:03d}",
                    str(rec.frame_count),
                    rec.created_label,
                )
            ):
                item = QtWidgets.QTableWidgetItem(text)
                item.setData(Qt.UserRole, rec)
                self._table.setItem(row, col, item)
        self._table.resizeRowsToContents()
        if records:
            self._table.selectRow(0)
        else:
            self._show_preview(None)

    def current_record(self) -> Optional[RenderRecord]:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._records):
            return None
        return self._records[row]

    def _on_selection(self) -> None:
        rec = self.current_record()
        self._show_preview(rec)
        self.selection_changed.emit(rec)

    def _show_preview(self, record: Optional[RenderRecord]) -> None:
        self._open_folder_btn.setEnabled(record is not None)
        if record is None or record.first_frame is None:
            self._preview.setText("No preview available")
            self._preview.setPixmap(QtGui.QPixmap())
            return

        pixmap = QtGui.QPixmap(str(record.first_frame))
        if pixmap.isNull():
            self._preview.setText("Could not load preview")
            self._preview.setPixmap(QtGui.QPixmap())
            return

        scaled = pixmap.scaled(
            self._preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._preview.setPixmap(scaled)
        self._preview.setText("")

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        rec = self.current_record()
        if rec and rec.first_frame:
            self._show_preview(rec)
