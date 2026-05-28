"""Multi-select camera table."""

from __future__ import annotations

from typing import List, Optional

from ..qt import Qt, QtWidgets, Signal
from ...host import CameraInfo


class CameraListWidget(QtWidgets.QGroupBox):
    selection_changed = Signal()
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Cameras", parent)
        layout = QtWidgets.QVBoxLayout(self)

        self._table = QtWidgets.QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Render", "Camera", "Resolution"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setColumnWidth(0, 56)
        layout.addWidget(self._table)
        self._table.itemChanged.connect(lambda *_: self.selection_changed.emit())

    def set_cameras(self, cameras: List[CameraInfo]) -> None:
        previously_checked = {cam.shape for cam in self.selected_cameras()}
        self._table.blockSignals(True)
        self._table.setRowCount(len(cameras))
        for row, cam in enumerate(cameras):
            check = QtWidgets.QTableWidgetItem()
            check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            should_check = cam.shape in previously_checked or (
                not previously_checked and cam.renderable
            )
            check.setCheckState(Qt.Checked if should_check else Qt.Unchecked)
            self._table.setItem(row, 0, check)

            name_item = QtWidgets.QTableWidgetItem(cam.shape)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            name_item.setData(Qt.UserRole, cam)
            self._table.setItem(row, 1, name_item)

            res_item = QtWidgets.QTableWidgetItem(f"{cam.width} × {cam.height}")
            res_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._table.setItem(row, 2, res_item)

        self._table.resizeRowsToContents()
        self._table.blockSignals(False)
        self.selection_changed.emit()

    def selected_cameras(self) -> List[CameraInfo]:
        selected: list[CameraInfo] = []
        for row in range(self._table.rowCount()):
            check = self._table.item(row, 0)
            if check is None or check.checkState() != Qt.Checked:
                continue
            name_item = self._table.item(row, 1)
            if name_item is None:
                continue
            cam = name_item.data(Qt.UserRole)
            if cam is not None:
                selected.append(cam)
        return selected
