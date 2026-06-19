"""Main window for the Import Unreal Assets tool."""

from __future__ import annotations

import getpass
import os

from PySide6 import QtCore, QtGui, QtWidgets

import genTools.genUnrealUtils as genUnrealUtils
from genTools.uiUtils import center_widget, load_qss

from assetTools.setdec_paths import (
    is_setdec_asset_folder,
    list_setdec_groups,
    normalize_disk_path,
    setdec_group_folder,
    setdec_production_folder,
    show_root_for,
)

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()
from publish_bundle_paths import parse_version_folder_name  # type: ignore[import-not-found]

from ..publish_layout import (
    DEFAULT_VARIANT_NAME,
    asset_manager_asset_root,
    asset_manager_publish_variants,
    asset_display_name,
    is_asset_manager_asset_root,
    is_asset_manager_version_path,
    is_rig_unreal_asset_root,
    list_subdirs,
    publish_layout_for_path,
    rig_unreal_versions,
    setdec_variants,
)
from .browser_helpers import (
    apply_table_combo_style,
    cell_combo,
    fill_version_combo,
    fit_table_row,
    make_table_combo,
    path_from_table_item,
    set_table_combo_cell,
)
from .import_controller import run_import_for_table
from .styles import BROWSER_STYLE, BROWSER_TAB_MODES, TABLE_ROW_HEIGHT, TOOL_DISPLAY_NAME


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setObjectName(TOOL_DISPLAY_NAME)
        self._current_show = self._resolve_current_show()
        self._current_user = self._resolve_current_user()
        self._base_show_dir = self._resolve_base_show_dir()
        self._setdec_root = setdec_production_folder(self._current_show)
        self._assets_root = (show_root_for(self._current_show) / "assets").as_posix()
        self._browser_mode = "setdec"
        self.initUI()

    def initUI(self):
        self.setStyleSheet(load_qss("dark.qss") + BROWSER_STYLE)
        self.setWindowTitle("{} — {}".format(TOOL_DISPLAY_NAME, self._current_show))
        self.setFocus()
        self.center()
        self.setGeometry(100, 100, 1400, 640)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)
        self.setLayout(outer)

        outer.addWidget(self._build_header())

        self.root_label = QtWidgets.QLabel()
        self.root_label.setWordWrap(True)
        self.root_label.setStyleSheet("color: #999999; font-size: 11px;")
        self.root_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        outer.addWidget(self.root_label)

        content = QtWidgets.QHBoxLayout()
        content.setSpacing(12)
        outer.addLayout(content, 1)

        content.addWidget(self._build_browser_panel(), 0)

        table_panel = QtWidgets.QWidget()
        table_layout = QtWidgets.QHBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(10)
        content.addWidget(table_panel, 1)

        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setObjectName("ImportAssetTable")
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tableWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Asset", "Variant", "Version", "Asset Type"]
        )
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.tableWidget.setColumnWidth(1, 156)
        self.tableWidget.setColumnWidth(2, 115)
        self.tableWidget.setColumnWidth(3, 142)
        self.tableWidget.itemSelectionChanged.connect(self._refresh_table_row_styles)

        button_panel = QtWidgets.QWidget()
        button_panel.setFixedWidth(120)
        button_layout = QtWidgets.QVBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        self.addButton = QtWidgets.QPushButton("Add Selected")
        self.addButton.clicked.connect(self.add)
        self.removeButton = QtWidgets.QPushButton("Remove")
        self.removeButton.clicked.connect(self.remove)
        self.clearButton = QtWidgets.QPushButton("Clear")
        self.clearButton.clicked.connect(self.clear)
        self.ImportButton = QtWidgets.QPushButton("Import")
        self.ImportButton.clicked.connect(self.importAsset)
        self.ImportButton.setStyleSheet(
            """
            QPushButton {
                color: #b1b1b1;
                background-color: QLinearGradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #015305, stop: 0.1 #015305,
                    stop: 0.5 #014c1c, stop: 0.9 #014c1c, stop: 1 #014c1c);
                min-height: 28px;
            }
            QPushButton:pressed {
                background-color: QLinearGradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2d2d2d, stop: 0.1 #2b2b2b,
                    stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
            }
            """
        )

        button_layout.addWidget(self.addButton)
        button_layout.addWidget(self.removeButton)
        button_layout.addWidget(self.clearButton)
        button_layout.addStretch(1)
        button_layout.addWidget(self.ImportButton)

        table_layout.addWidget(self.tableWidget, 1)
        table_layout.addWidget(button_panel, 0)

        self._update_root_label()

    def center(self):
        center_widget(self)

    @staticmethod
    def _resolve_current_show():
        current_show = os.environ.get("SHOW_NAME", "").strip()
        if not current_show:
            raise RuntimeError(
                "SHOW_NAME is not set. Launch Unreal through TinyStudioLauncher, "
                "then reopen {}.".format(TOOL_DISPLAY_NAME)
            )
        return current_show

    @staticmethod
    def _resolve_current_user():
        return os.environ.get("USERNAME", "").strip() or getpass.getuser()

    @staticmethod
    def _resolve_base_show_dir():
        return os.environ.get("TINYSTUDIO_BASE_SHOW_DIR", "").strip() or "N/A"

    @staticmethod
    def _section_label(text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setObjectName("BrowserSectionLabel")
        return label

    @staticmethod
    def _make_asset_list() -> QtWidgets.QListWidget:
        widget = QtWidgets.QListWidget()
        widget.setObjectName("ImportAssetList")
        widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        return widget

    def _build_header(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)

        for text in (
            "<b>Show:</b> {}".format(self._current_show),
            "<b>User:</b> {}".format(self._current_user),
            "<b>Drive:</b> {}".format(self._base_show_dir),
        ):
            label = QtWidgets.QLabel(text)
            label.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addWidget(label)
            if text != "<b>Drive:</b> {}".format(self._base_show_dir):
                layout.addStretch(1)
        return frame

    def _build_browser_panel(self):
        panel = QtWidgets.QFrame()
        panel.setObjectName("ImportBrowserPanel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(420)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.browser_tabs = QtWidgets.QTabWidget()
        self.browser_tabs.addTab(self._build_setdec_browser(), "Set Dec")
        self.browser_tabs.addTab(self._build_asset_browser(), "Assets")
        self.browser_tabs.addTab(self._build_rigs_browser(), "Rigs")
        self.browser_tabs.currentChanged.connect(self._on_browser_tab_changed)

        layout.addWidget(self.browser_tabs)
        return panel

    def _on_browser_tab_changed(self, index):
        if 0 <= index < len(BROWSER_TAB_MODES):
            self._browser_mode = BROWSER_TAB_MODES[index]
        else:
            self._browser_mode = "setdec"
        self._update_root_label()

    def _update_root_label(self):
        if self._browser_mode == "assets":
            self.root_label.setText(
                "<b>Assets root:</b> <code>{}</code>".format(self._assets_root)
            )
        elif self._browser_mode == "rigs":
            self.root_label.setText(
                "<b>Rigs root:</b> <code>{}</code> &nbsp;|&nbsp; "
                "Looking for <code>publish/rig/unreal/v###/</code> exports.".format(
                    self._assets_root
                )
            )
        else:
            self.root_label.setText(
                "<b>Set Dec root:</b> <code>{}</code>".format(self._setdec_root)
            )

    def _build_setdec_browser(self):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(8)

        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.currentIndexChanged.connect(self._refresh_setdec_asset_list)

        self.setdec_asset_list = self._make_asset_list()

        self.browser_status = QtWidgets.QLabel()
        self.browser_status.setWordWrap(True)
        self.browser_status.setStyleSheet("color: #888888; font-size: 11px;")

        layout.addWidget(self._section_label("Set Dec Group"))
        layout.addWidget(self.group_combo)
        layout.addWidget(self._section_label("Assets"))
        layout.addWidget(self.setdec_asset_list, 1)
        layout.addWidget(self.browser_status)

        self._refresh_groups()
        return panel

    def _build_asset_browser(self):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(8)

        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems(["chr", "prop", "env", "veh"])
        self.category_combo.currentIndexChanged.connect(self._refresh_asset_manager_list)

        self.manager_asset_list = self._make_asset_list()

        self.asset_browser_status = QtWidgets.QLabel(
            "Select asset folders, then click Add Selected. Latest publish version is picked automatically."
        )
        self.asset_browser_status.setWordWrap(True)
        self.asset_browser_status.setStyleSheet("color: #888888; font-size: 11px;")

        layout.addWidget(self._section_label("Category"))
        layout.addWidget(self.category_combo)
        layout.addWidget(self._section_label("Assets"))
        layout.addWidget(self.manager_asset_list, 1)
        layout.addWidget(self.asset_browser_status)

        self._refresh_asset_manager_list()
        return panel

    def _build_rigs_browser(self):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(8)

        self.rigs_category_combo = QtWidgets.QComboBox()
        self.rigs_category_combo.addItems(["chr", "prop", "veh"])
        self.rigs_category_combo.currentIndexChanged.connect(self._refresh_rigs_asset_list)

        self.rigs_asset_list = self._make_asset_list()

        self.rigs_browser_status = QtWidgets.QLabel(
            "Select character or prop folders with rig exports under publish/rig/unreal/."
        )
        self.rigs_browser_status.setWordWrap(True)
        self.rigs_browser_status.setStyleSheet("color: #888888; font-size: 11px;")

        layout.addWidget(self._section_label("Category"))
        layout.addWidget(self.rigs_category_combo)
        layout.addWidget(self._section_label("Assets"))
        layout.addWidget(self.rigs_asset_list, 1)
        layout.addWidget(self.rigs_browser_status)

        self._refresh_rigs_asset_list()
        return panel

    def _refresh_groups(self):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()

        if not os.path.isdir(self._setdec_root):
            self.group_combo.addItem("(setdec folder not found)")
            self.group_combo.setEnabled(False)
            self.setdec_asset_list.setEnabled(False)
            self.browser_status.setText(
                "Expected folder does not exist: {}".format(self._setdec_root)
            )
        else:
            groups = list_setdec_groups(self._current_show)
            if groups:
                self.group_combo.addItems(groups)
                self.group_combo.setEnabled(True)
                self.setdec_asset_list.setEnabled(True)
                self.browser_status.setText(
                    "Select one or more assets, then click Add Selected."
                )
            else:
                self.group_combo.addItem("(no groups in setdec)")
                self.group_combo.setEnabled(False)
                self.setdec_asset_list.setEnabled(False)
                self.browser_status.setText(
                    "No Set Dec groups under {}.".format(self._setdec_root)
                )

        self.group_combo.blockSignals(False)
        self._refresh_setdec_asset_list()

    def _refresh_setdec_asset_list(self):
        self.setdec_asset_list.clear()
        if not self.group_combo.isEnabled():
            return

        group = self.group_combo.currentText()
        group_path = setdec_group_folder(self._current_show, group)
        if not os.path.isdir(group_path):
            return

        for asset_name in list_subdirs(group_path):
            asset_path = normalize_disk_path(os.path.join(group_path, asset_name))
            if is_setdec_asset_folder(self._setdec_root, asset_path):
                self.setdec_asset_list.addItem(asset_name)

    def _refresh_asset_manager_list(self):
        self.manager_asset_list.clear()
        category = self.category_combo.currentText()
        category_path = os.path.join(self._assets_root, category).replace("\\", "/")
        if not os.path.isdir(category_path):
            self.manager_asset_list.setEnabled(False)
            self.asset_browser_status.setText(
                "Category folder not found: {}".format(category_path)
            )
            return

        self.manager_asset_list.setEnabled(True)
        count = 0
        for asset_name in list_subdirs(category_path):
            asset_path = normalize_disk_path(os.path.join(category_path, asset_name))
            if is_asset_manager_asset_root(asset_path):
                self.manager_asset_list.addItem(asset_name)
                count += 1

        self.asset_browser_status.setText(
            "{} assets with model publishes. Select folders, then Add Selected.".format(count)
        )

    def _refresh_rigs_asset_list(self):
        self.rigs_asset_list.clear()
        category = self.rigs_category_combo.currentText()
        category_path = os.path.join(self._assets_root, category).replace("\\", "/")
        if not os.path.isdir(category_path):
            self.rigs_asset_list.setEnabled(False)
            self.rigs_browser_status.setText(
                "Category folder not found: {}".format(category_path)
            )
            return

        self.rigs_asset_list.setEnabled(True)
        count = 0
        for asset_name in list_subdirs(category_path):
            asset_path = normalize_disk_path(os.path.join(category_path, asset_name))
            if is_rig_unreal_asset_root(asset_path):
                self.rigs_asset_list.addItem(asset_name)
                count += 1

        self.rigs_browser_status.setText(
            "{} assets with rig exports under publish/rig/unreal/. "
            "Select folders, then Add Selected.".format(count)
        )

    def _paths_from_browser_selection(self):
        if self._browser_mode == "rigs":
            category = self.rigs_category_combo.currentText()
            category_path = os.path.join(self._assets_root, category).replace("\\", "/")
            paths = []
            for item in self.rigs_asset_list.selectedItems():
                asset_path = normalize_disk_path(os.path.join(category_path, item.text()))
                if asset_path not in paths:
                    paths.append(asset_path)
            return paths

        if self._browser_mode == "assets":
            category = self.category_combo.currentText()
            category_path = os.path.join(self._assets_root, category).replace("\\", "/")
            paths = []
            for item in self.manager_asset_list.selectedItems():
                asset_path = normalize_disk_path(os.path.join(category_path, item.text()))
                if asset_path not in paths:
                    paths.append(asset_path)
            return paths

        group = self.group_combo.currentText()
        group_path = setdec_group_folder(self._current_show, group)
        paths = []
        for item in self.setdec_asset_list.selectedItems():
            asset_path = normalize_disk_path(os.path.join(group_path, item.text()))
            if asset_path not in paths:
                paths.append(asset_path)
        return paths

    def _populate_variant_version_combos(
        self,
        row: int,
        path: str,
        *,
        asset_type_default: str = "Static Mesh",
        layout: str | None = None,
    ):
        variant_combo = make_table_combo()
        version_combo = make_table_combo()
        asset_type_combo = make_table_combo()
        asset_type_combo.addItems(["Static Mesh", "Skeletal Mesh"])
        asset_type_combo.setCurrentText(asset_type_default)

        resolved_layout = publish_layout_for_path(path, layout_hint=layout)

        if resolved_layout == "rig_unreal":
            variant_combo.addItems([DEFAULT_VARIANT_NAME])
            fill_version_combo(
                version_combo,
                path=path,
                variant=DEFAULT_VARIANT_NAME,
                layout="rig_unreal",
            )
            asset_type_combo.setCurrentText("Skeletal Mesh")
        elif resolved_layout == "asset_manager_model":
            asset_root = asset_manager_asset_root(path)
            variants = asset_manager_publish_variants(asset_root)
            variant_names = sorted(variants.keys())
            variant_combo.addItems(variant_names or ["main"])

            if is_asset_manager_version_path(path):
                parsed = parse_version_folder_name(os.path.basename(path.rstrip("/\\")))
                if parsed:
                    _asset, _publish_type, default_variant, default_version = parsed
                    variant_index = variant_combo.findText(default_variant)
                    if variant_index >= 0:
                        variant_combo.setCurrentIndex(variant_index)
            elif len(variant_names) > 1:
                variant_combo.setProperty("multi_variant", True)
                apply_table_combo_style(variant_combo, multi_variant=True)

            fill_version_combo(
                version_combo,
                path=asset_root,
                variant=variant_combo.currentText(),
                layout="asset_manager_model",
            )
            asset_type_combo.setCurrentText("Static Mesh")
        else:
            variants = setdec_variants(path)
            variant_names = sorted(variants.keys()) if variants else list_subdirs(path)
            variant_combo.addItems(variant_names or [DEFAULT_VARIANT_NAME])
            if len(variant_names) > 1:
                variant_combo.setProperty("multi_variant", True)
                apply_table_combo_style(variant_combo, multi_variant=True)

            fill_version_combo(
                version_combo,
                path=path,
                variant=variant_combo.currentText(),
                layout="setdec",
            )

            parent_folder = path.replace("\\", "/").split("/")[-4] if path else ""
            if parent_folder.upper() in ("CHR", "PROP", "CRE", "VEH"):
                index = asset_type_combo.findText(
                    "Skeletal Mesh", QtCore.Qt.MatchFlag.MatchFixedString
                )
                if index >= 0:
                    asset_type_combo.setCurrentIndex(index)

        variant_combo.currentIndexChanged.connect(
            lambda _index, row=row: self._on_variant_changed(row)
        )

        set_table_combo_cell(self.tableWidget, row, 1, variant_combo)
        set_table_combo_cell(self.tableWidget, row, 2, version_combo)
        set_table_combo_cell(self.tableWidget, row, 3, asset_type_combo)
        fit_table_row(self.tableWidget, row)
        self._refresh_table_row_styles()

    def _layout_hint_for_browser(self) -> str | None:
        if self._browser_mode == "rigs":
            return "rig_unreal"
        if self._browser_mode == "assets":
            return "asset_manager_model"
        return "setdec"

    def _row_publish_layout(self, row: int) -> str:
        item = self.tableWidget.item(row, 0)
        if item is None:
            return "setdec"
        stored = item.data(QtCore.Qt.ItemDataRole.UserRole + 1)
        if stored:
            return str(stored)
        return publish_layout_for_path(path_from_table_item(item))

    def _populate_row_from_path(self, row: int, path: str, *, layout: str | None = None):
        path = normalize_disk_path(path.replace("\\", "/"))
        resolved_layout = layout or publish_layout_for_path(
            path,
            layout_hint=self._layout_hint_for_browser(),
        )
        if is_asset_manager_version_path(path):
            path = asset_manager_asset_root(path)
        item = QtWidgets.QTableWidgetItem(asset_display_name(path))
        item.setToolTip(path)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
        item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, resolved_layout)
        self.tableWidget.setItem(row, 0, item)
        self._populate_variant_version_combos(
            row,
            path,
            layout=resolved_layout,
            asset_type_default=(
                "Skeletal Mesh" if resolved_layout == "rig_unreal" else "Static Mesh"
            ),
        )

    def add(self, pathList=None):
        paths = pathList or self._paths_from_browser_selection()
        if not paths:
            genUnrealUtils.warningPopup(
                "Select one or more asset folders in the browser first."
            )
            return

        existing = {
            path_from_table_item(self.tableWidget.item(row, 0))
            for row in range(self.tableWidget.rowCount())
            if self.tableWidget.item(row, 0) is not None
        }

        added = 0
        for path in paths:
            normalized = normalize_disk_path(path)
            if normalized in existing:
                continue
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self._populate_row_from_path(
                row,
                normalized,
                layout=self._layout_hint_for_browser(),
            )
            existing.add(normalized)
            added += 1

        if added == 0 and paths:
            genUnrealUtils.warningPopup("Selected assets are already in the import list.")
        self._refresh_table_row_styles()

    def remove(self):
        rows = sorted(
            {index.row() for index in self.tableWidget.selectedIndexes()},
            reverse=True,
        )
        if not rows:
            genUnrealUtils.warningPopup("Select one or more rows in the import list to remove.")
            return
        for row in rows:
            self.tableWidget.removeRow(row)
        self._refresh_table_row_styles()

    def clear(self):
        self.tableWidget.setRowCount(0)

    def getDuplicatesInList(self):
        paths = []
        for row in range(self.tableWidget.rowCount()):
            paths.append(path_from_table_item(self.tableWidget.item(row, 0)))
        return {name for name in paths if paths.count(name) > 1}

    def _refresh_table_row_styles(self):
        """Keep custom styling limited to duplicate warnings and variant hints."""
        duplicates = self.getDuplicatesInList()
        default_brush = QtGui.QBrush()
        warning_brush = QtGui.QBrush(QtGui.QColor("#7D2020"))

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            path = path_from_table_item(item) if item is not None else ""

            if item is not None:
                if path in duplicates:
                    item.setBackground(warning_brush)
                else:
                    item.setBackground(default_brush)

            for column in (1, 2, 3):
                combo = cell_combo(self.tableWidget, row, column)
                if combo is None:
                    continue
                multi_variant = column == 1 and bool(combo.property("multi_variant"))
                apply_table_combo_style(
                    combo,
                    multi_variant=multi_variant,
                )

    def _on_variant_changed(self, row: int):
        item = self.tableWidget.item(row, 0)
        if item is None:
            return
        asset_path = path_from_table_item(item)
        variant_combo = cell_combo(self.tableWidget, row, 1)
        version_combo = cell_combo(self.tableWidget, row, 2)
        if variant_combo is None or version_combo is None:
            return
        variant = variant_combo.currentText()
        layout = self._row_publish_layout(row)
        root_path = asset_path
        if layout == "asset_manager_model":
            root_path = asset_manager_asset_root(asset_path)
        fill_version_combo(
            version_combo,
            path=root_path,
            variant=variant,
            layout=layout,
        )

    def importAsset(self):
        run_import_for_table(self)
