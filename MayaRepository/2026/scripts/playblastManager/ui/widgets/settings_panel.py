"""Playblast settings (frame range, HUD, display, quality)."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..qt import Qt, QtWidgets
from ...core.schema import PlayblastSchema


class SettingsPanel(QtWidgets.QGroupBox):
    def __init__(self, schema: PlayblastSchema, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Settings", parent)
        layout = QtWidgets.QFormLayout(self)

        self._scene_range_radio = QtWidgets.QRadioButton("Scene playback range")
        self._custom_range_radio = QtWidgets.QRadioButton("Custom range")
        range_box = QtWidgets.QWidget()
        range_layout = QtWidgets.QVBoxLayout(range_box)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.addWidget(self._scene_range_radio)
        range_layout.addWidget(self._custom_range_radio)
        layout.addRow("Frame range:", range_box)

        frame_row = QtWidgets.QHBoxLayout()
        self._start_spin = QtWidgets.QDoubleSpinBox()
        self._end_spin = QtWidgets.QDoubleSpinBox()
        for spin in (self._start_spin, self._end_spin):
            spin.setDecimals(3)
            spin.setRange(-100000.0, 100000.0)
            spin.setSingleStep(1.0)
        frame_row.addWidget(QtWidgets.QLabel("Start"))
        frame_row.addWidget(self._start_spin)
        frame_row.addWidget(QtWidgets.QLabel("End"))
        frame_row.addWidget(self._end_spin)
        layout.addRow("", frame_row)

        self._hud_check = QtWidgets.QCheckBox("Show HUD / ornaments")
        self._hud_check.setObjectName("ShowOrnamentsCheck")
        # Global dark.qss defines the base indicator but no checked-state style
        # for QCheckBox, which makes checked/unchecked look identical.
        self._hud_check.setStyleSheet(
            """
            QCheckBox#ShowOrnamentsCheck::indicator:checked {
                background-color: #ffaa00;
                border: 1px solid #ffaa00;
            }
            """
        )
        self._hud_check.setChecked(schema.default_show_ornaments)
        layout.addRow(self._hud_check)

        self._display_combo = QtWidgets.QComboBox()
        self._display_combo.addItems(schema.display_modes)
        idx = self._display_combo.findText(schema.default_display_mode)
        if idx >= 0:
            self._display_combo.setCurrentIndex(idx)
        layout.addRow("Display mode:", self._display_combo)

        self._quality_spin = QtWidgets.QSpinBox()
        self._quality_spin.setRange(1, 100)
        self._quality_spin.setValue(schema.default_quality)
        layout.addRow("Quality:", self._quality_spin)

        res_lbl = QtWidgets.QLabel("From camera")
        res_lbl.setStyleSheet("color: #a8a8a8; background: transparent; border: none;")
        layout.addRow("Resolution:", res_lbl)

        fmt_lbl = QtWidgets.QLabel("PNG sequence")
        fmt_lbl.setStyleSheet("color: #a8a8a8; background: transparent; border: none;")
        layout.addRow("Format:", fmt_lbl)

        if schema.default_frame_source == "scene":
            self._scene_range_radio.setChecked(True)
        else:
            self._custom_range_radio.setChecked(True)

        self._scene_range_radio.toggled.connect(self._update_range_enabled)
        self._custom_range_radio.toggled.connect(self._update_range_enabled)
        self._update_range_enabled()

    def _update_range_enabled(self) -> None:
        custom = self._custom_range_radio.isChecked()
        self._start_spin.setEnabled(custom)
        self._end_spin.setEnabled(custom)

    def set_playback_range(self, start: float, end: float) -> None:
        self._start_spin.setValue(start)
        self._end_spin.setValue(end)

    def frame_range(self, scene_start: float, scene_end: float) -> Tuple[float, float]:
        if self._scene_range_radio.isChecked():
            return scene_start, scene_end
        return self._start_spin.value(), self._end_spin.value()

    def show_ornaments(self) -> bool:
        return self._hud_check.isChecked()

    def display_mode(self) -> str:
        return self._display_combo.currentText()

    def quality(self) -> int:
        return self._quality_spin.value()
