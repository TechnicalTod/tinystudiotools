"""Published version folder table."""

from __future__ import annotations

from typing import List, Optional

from ...core.versioning import PublishEntry
from ..qt import Qt, QtCore, QtWidgets, Signal

_HEADERS = ("Variant", "Version", "Summary", "Modified")


class PublishTable(QtWidgets.QTableWidget):
    selection_changed = Signal(object)
    open_requested = Signal(object)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(0, len(_HEADERS), parent)
        self.setHorizontalHeaderLabels(_HEADERS)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.doubleClicked.connect(self._on_double_clicked)
        self._entries: List[PublishEntry] = []

    def set_entries(self, entries: List[PublishEntry]) -> None:
        self._entries = list(entries)
        was_sorting = self.isSortingEnabled()
        self.setSortingEnabled(False)
        self.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            variant_item = QtWidgets.QTableWidgetItem(entry.variant)
            variant_item.setData(Qt.UserRole, row)
            version_item = QtWidgets.QTableWidgetItem(f"v{entry.version:03d}")
            version_item.setData(Qt.UserRole, entry.version)
            summary_item = QtWidgets.QTableWidgetItem(entry.summary)
            summary_item.setToolTip(str(entry.path))
            modified_item = QtWidgets.QTableWidgetItem(entry.modified)
            self.setItem(row, 0, variant_item)
            self.setItem(row, 1, version_item)
            self.setItem(row, 2, summary_item)
            self.setItem(row, 3, modified_item)
        self.setSortingEnabled(was_sorting)
        if self._entries:
            self.selectRow(0)
        else:
            self.selection_changed.emit(None)

    def current_entry(self) -> Optional[PublishEntry]:
        rows = self.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.item(rows[0].row(), 0)
        if item is None:
            return None
        idx = item.data(Qt.UserRole)
        if idx is None or idx >= len(self._entries):
            return None
        return self._entries[idx]

    def _on_selection_changed(self) -> None:
        self.selection_changed.emit(self.current_entry())

    def _on_double_clicked(self, _index: QtCore.QModelIndex) -> None:
        entry = self.current_entry()
        if entry is not None:
            self.open_requested.emit(entry)
