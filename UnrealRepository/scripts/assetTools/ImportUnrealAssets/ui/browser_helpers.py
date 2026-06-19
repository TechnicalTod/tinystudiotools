"""Table and browser helper utilities for the Import Unreal Assets UI."""

from __future__ import annotations

import os

from PySide6 import QtCore, QtWidgets

from genTools.uiUtils import load_qss

from assetTools.setdec_paths import normalize_disk_path

from ..publish_layout import (
    DEFAULT_VARIANT_NAME,
    asset_display_name,
    asset_manager_asset_root,
    asset_manager_publish_variants,
    list_subdirs,
    publish_layout_for_path,
    rig_unreal_versions,
    setdec_variants,
    version_sort_key,
)
from .styles import TABLE_COMBO_QSS, TABLE_ROW_HEIGHT

__all__ = [
    "DEFAULT_VARIANT_NAME",
    "apply_table_combo_style",
    "asset_display_name",
    "asset_manager_asset_root",
    "asset_manager_publish_variants",
    "cell_combo",
    "fill_version_combo",
    "fit_table_row",
    "list_subdirs",
    "make_table_combo",
    "path_from_table_item",
    "publish_layout_for_path",
    "rig_unreal_versions",
    "set_table_combo_cell",
    "setdec_variants",
    "version_sort_key",
]


def apply_table_combo_style(
    combo: QtWidgets.QComboBox,
    *,
    multi_variant: bool = False,
) -> None:
    if multi_variant:
        combo.setStyleSheet(TABLE_COMBO_QSS + load_qss("qComboBoxMultiItemYellow.qss"))
    else:
        combo.setStyleSheet(TABLE_COMBO_QSS)
    combo.setSizeAdjustPolicy(
        QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
    )
    combo.setMinimumContentsLength(10)


def make_table_combo(*, multi_variant: bool = False) -> QtWidgets.QComboBox:
    combo = QtWidgets.QComboBox()
    apply_table_combo_style(combo, multi_variant=multi_variant)
    return combo


def set_table_combo_cell(
    table: QtWidgets.QTableWidget,
    row: int,
    column: int,
    combo: QtWidgets.QComboBox,
) -> None:
    table.setCellWidget(row, column, combo)


def fit_table_row(table: QtWidgets.QTableWidget, row: int) -> None:
    table.setRowHeight(row, TABLE_ROW_HEIGHT)


def path_from_table_item(item: QtWidgets.QTableWidgetItem | None) -> str:
    if item is None:
        return ""
    stored = item.data(QtCore.Qt.ItemDataRole.UserRole)
    return normalize_disk_path(str(stored or item.text()))


def cell_combo(table: QtWidgets.QTableWidget, row: int, column: int) -> QtWidgets.QComboBox | None:
    widget = table.cellWidget(row, column)
    if isinstance(widget, QtWidgets.QComboBox):
        return widget
    return None


def fill_version_combo(
    version_combo: QtWidgets.QComboBox,
    *,
    path: str,
    variant: str,
    layout: str,
) -> None:
    version_combo.blockSignals(True)
    version_combo.clear()
    if layout == "rig_unreal":
        versions = rig_unreal_versions(path)
    elif layout == "asset_manager_model":
        variants = asset_manager_publish_variants(path)
        versions = variants.get(variant, [])
    else:
        versions = sorted(
            list_subdirs(os.path.join(path, variant)),
            key=version_sort_key,
        )
    version_combo.addItems(versions or ["v001"])
    if versions:
        version_combo.setCurrentIndex(len(versions) - 1)
    version_combo.blockSignals(False)
