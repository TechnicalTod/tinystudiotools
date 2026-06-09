import os
import sys
import getpass
import unreal
from PySide6 import QtGui, QtWidgets, QtCore

import genTools.genUnrealUtils as genUnrealUtils
import genTools.genUnrealImportUtils as genUnrealImportUtils
from genTools.uiUtils import center_widget, load_qss
from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()
from publish_bundle_paths import parse_version_folder_name  # type: ignore[import-not-found]
from assetTools.setdec_import_ops import (
    import_setdec_static_mesh_pipeline,
    import_static_mesh_publish_pipeline,
    identity_from_base_path,
)
from assetTools.setdec_paths import (
    is_setdec_asset_folder,
    list_setdec_groups,
    normalize_disk_path,
    setdec_group_folder,
    setdec_production_folder,
    show_root_for,
)

_BROWSER_STYLE = """
QFrame#ImportBrowserPanel {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    background-color: #2a2a2a;
}
QLabel#BrowserSectionLabel {
    color: #aaaaaa;
    font-size: 11px;
    font-weight: bold;
    padding-top: 2px;
}
QListWidget#ImportAssetList {
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    background-color: #1e1e1e;
    padding: 2px;
}
QListWidget#ImportAssetList::item {
    padding: 4px 6px;
}
QTableWidget#ImportAssetTable {
    gridline-color: #333333;
}
"""

_TABLE_COMBO_QSS = """
QComboBox {
    color: #d0d0d0;
    background-color: #4e4e4e;
    border: 1px solid #1e1e1e;
    border-radius: 3px;
    padding: 0px 20px 0px 6px;
    font-size: 11px;
}
QComboBox:hover,
QComboBox:focus,
QComboBox:on {
    color: #d0d0d0;
    background-color: #4e4e4e;
    border: 1px solid #1e1e1e;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid #3a3a3a;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
"""

_TABLE_ROW_HEIGHT = 32

_WINDOW = None
DEFAULT_VARIANT_NAME = "main"


def _list_subdirs(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    return sorted(
        name
        for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    )


def _version_sort_key(version_label: str) -> int:
    if version_label.lower().startswith("v") and version_label[1:].isdigit():
        return int(version_label[1:])
    return 0


def _is_asset_manager_version_path(path: str) -> bool:
    folder_name = os.path.basename(normalize_disk_path(path).rstrip("/\\"))
    return parse_version_folder_name(folder_name) is not None


def _is_asset_manager_asset_root(path: str) -> bool:
    path = normalize_disk_path(path).rstrip("/\\")
    model_dir = os.path.join(path, "publish", "model")
    return os.path.isdir(model_dir) and not _is_asset_manager_version_path(path)


def _asset_manager_asset_root(path: str) -> str:
    path = normalize_disk_path(path).rstrip("/\\")
    if _is_asset_manager_version_path(path):
        return normalize_disk_path(
            os.path.dirname(os.path.dirname(os.path.dirname(path)))
        )
    return path


def _asset_manager_publish_variants(asset_root: str) -> dict[str, list[str]]:
    model_dir = os.path.join(normalize_disk_path(asset_root), "publish", "model")
    variants: dict[str, list[str]] = {}
    for folder in _list_subdirs(model_dir):
        parsed = parse_version_folder_name(folder)
        if not parsed:
            continue
        _asset, _publish_type, variant, version = parsed
        variants.setdefault(variant, []).append(version)
    for variant, versions in variants.items():
        variants[variant] = sorted(set(versions), key=_version_sort_key)
    return variants


def _setdec_variants(asset_path: str) -> dict[str, list[str]]:
    variants: dict[str, list[str]] = {}
    for variant in _list_subdirs(asset_path):
        versions = sorted(_list_subdirs(os.path.join(asset_path, variant)), key=_version_sort_key)
        if versions:
            variants[variant] = versions
    return variants


def _apply_table_combo_style(
    combo: QtWidgets.QComboBox,
    *,
    multi_variant: bool = False,
) -> None:
    if multi_variant:
        combo.setStyleSheet(_TABLE_COMBO_QSS + load_qss("qComboBoxMultiItemYellow.qss"))
    else:
        combo.setStyleSheet(_TABLE_COMBO_QSS)
    combo.setSizeAdjustPolicy(
        QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
    )
    combo.setMinimumContentsLength(10)


def _make_table_combo(*, multi_variant: bool = False) -> QtWidgets.QComboBox:
    combo = QtWidgets.QComboBox()
    _apply_table_combo_style(combo, multi_variant=multi_variant)
    return combo


def _set_table_combo_cell(
    table: QtWidgets.QTableWidget,
    row: int,
    column: int,
    combo: QtWidgets.QComboBox,
) -> None:
    table.setCellWidget(row, column, combo)


def _fit_table_row(table: QtWidgets.QTableWidget, row: int) -> None:
    table.setRowHeight(row, _TABLE_ROW_HEIGHT)


def _path_from_table_item(item: QtWidgets.QTableWidgetItem | None) -> str:
    if item is None:
        return ""
    stored = item.data(QtCore.Qt.ItemDataRole.UserRole)
    return normalize_disk_path(str(stored or item.text()))


def _asset_display_name(path: str) -> str:
    return os.path.basename(normalize_disk_path(path).rstrip("/\\"))


def _cell_combo(table: QtWidgets.QTableWidget, row: int, column: int) -> QtWidgets.QComboBox | None:
    widget = table.cellWidget(row, column)
    if isinstance(widget, QtWidgets.QComboBox):
        return widget
    return None


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setObjectName("Import Unreal Assets")
        self._current_show = self._resolve_current_show()
        self._current_user = self._resolve_current_user()
        self._base_show_dir = self._resolve_base_show_dir()
        self._setdec_root = setdec_production_folder(self._current_show)
        self._assets_root = (show_root_for(self._current_show) / "assets").as_posix()
        self._browser_mode = "setdec"
        self.initUI()

    def initUI(self):
        self.setStyleSheet(load_qss("dark.qss") + _BROWSER_STYLE)
        self.setWindowTitle("Import Assets — {}".format(self._current_show))
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
        self.tableWidget.verticalHeader().setDefaultSectionSize(_TABLE_ROW_HEIGHT)
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
        self.show()

    def center(self):
        center_widget(self)

    @staticmethod
    def _resolve_current_show():
        current_show = os.environ.get("SHOW_NAME", "").strip()
        if not current_show:
            raise RuntimeError(
                "SHOW_NAME is not set. Launch Unreal through TinyStudioLauncher, "
                "then reopen Import Assets."
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
        self.browser_tabs.currentChanged.connect(self._on_browser_tab_changed)

        layout.addWidget(self.browser_tabs)
        return panel

    def _on_browser_tab_changed(self, index):
        self._browser_mode = "assets" if index == 1 else "setdec"
        self._update_root_label()

    def _update_root_label(self):
        if self._browser_mode == "assets":
            self.root_label.setText(
                "<b>Assets root:</b> <code>{}</code>".format(self._assets_root)
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

        for asset_name in _list_subdirs(group_path):
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
        for asset_name in _list_subdirs(category_path):
            asset_path = normalize_disk_path(os.path.join(category_path, asset_name))
            if _is_asset_manager_asset_root(asset_path):
                self.manager_asset_list.addItem(asset_name)
                count += 1

        self.asset_browser_status.setText(
            "{} assets with model publishes. Select folders, then Add Selected.".format(count)
        )

    def _paths_from_browser_selection(self):
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
    ):
        variant_combo = _make_table_combo()
        version_combo = _make_table_combo()
        asset_type_combo = _make_table_combo()
        asset_type_combo.addItems(["Static Mesh", "Skeletal Mesh"])
        asset_type_combo.setCurrentText(asset_type_default)

        if _is_asset_manager_asset_root(path) or _is_asset_manager_version_path(path):
            asset_root = _asset_manager_asset_root(path)
            variants = _asset_manager_publish_variants(asset_root)
            variant_names = sorted(variants.keys())
            variant_combo.addItems(variant_names or ["main"])

            if _is_asset_manager_version_path(path):
                parsed = parse_version_folder_name(os.path.basename(path.rstrip("/\\")))
                if parsed:
                    _asset, _publish_type, default_variant, default_version = parsed
                    variant_index = variant_combo.findText(default_variant)
                    if variant_index >= 0:
                        variant_combo.setCurrentIndex(variant_index)
            elif len(variant_names) > 1:
                variant_combo.setProperty("multi_variant", True)
                _apply_table_combo_style(variant_combo, multi_variant=True)

            self._fill_version_combo(
                version_combo,
                path=asset_root,
                variant=variant_combo.currentText(),
                is_asset_manager=True,
            )
            asset_type_combo.setCurrentText("Static Mesh")
        else:
            variants = _setdec_variants(path)
            variant_names = sorted(variants.keys()) if variants else _list_subdirs(path)
            variant_combo.addItems(variant_names or [DEFAULT_VARIANT_NAME])
            if len(variant_names) > 1:
                variant_combo.setProperty("multi_variant", True)
                _apply_table_combo_style(variant_combo, multi_variant=True)

            self._fill_version_combo(
                version_combo,
                path=path,
                variant=variant_combo.currentText(),
                is_asset_manager=False,
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

        _set_table_combo_cell(self.tableWidget, row, 1, variant_combo)
        _set_table_combo_cell(self.tableWidget, row, 2, version_combo)
        _set_table_combo_cell(self.tableWidget, row, 3, asset_type_combo)
        _fit_table_row(self.tableWidget, row)
        self._refresh_table_row_styles()

    def _fill_version_combo(
        self,
        version_combo: QtWidgets.QComboBox,
        *,
        path: str,
        variant: str,
        is_asset_manager: bool,
    ):
        version_combo.blockSignals(True)
        version_combo.clear()
        if is_asset_manager:
            variants = _asset_manager_publish_variants(path)
            versions = variants.get(variant, [])
        else:
            versions = sorted(
                _list_subdirs(os.path.join(path, variant)),
                key=_version_sort_key,
            )
        version_combo.addItems(versions or ["v001"])
        if versions:
            version_combo.setCurrentIndex(len(versions) - 1)
        version_combo.blockSignals(False)

    def _populate_row_from_path(self, row: int, path: str):
        path = normalize_disk_path(path.replace("\\", "/"))
        if _is_asset_manager_version_path(path):
            path = _asset_manager_asset_root(path)
        item = QtWidgets.QTableWidgetItem(_asset_display_name(path))
        item.setToolTip(path)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
        self.tableWidget.setItem(row, 0, item)
        self._populate_variant_version_combos(row, path)

    def add(self, pathList=None):
        paths = pathList or self._paths_from_browser_selection()
        if not paths:
            genUnrealUtils.warningPopup(
                "Select one or more asset folders in the browser first."
            )
            return

        existing = {
            _path_from_table_item(self.tableWidget.item(row, 0))
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
            self._populate_row_from_path(row, normalized)
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
            paths.append(_path_from_table_item(self.tableWidget.item(row, 0)))
        return {name for name in paths if paths.count(name) > 1}

    def _refresh_table_row_styles(self):
        """Keep custom styling limited to duplicate warnings and variant hints."""
        duplicates = self.getDuplicatesInList()
        default_brush = QtGui.QBrush()
        warning_brush = QtGui.QBrush(QtGui.QColor("#7D2020"))

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            path = _path_from_table_item(item) if item is not None else ""

            if item is not None:
                if path in duplicates:
                    item.setBackground(warning_brush)
                else:
                    item.setBackground(default_brush)

            for column in (1, 2, 3):
                combo = _cell_combo(self.tableWidget, row, column)
                if combo is None:
                    continue
                multi_variant = column == 1 and bool(combo.property("multi_variant"))
                _apply_table_combo_style(
                    combo,
                    multi_variant=multi_variant,
                )

    def _on_variant_changed(self, row: int):
        item = self.tableWidget.item(row, 0)
        if item is None:
            return
        asset_path = _path_from_table_item(item)
        variant_combo = _cell_combo(self.tableWidget, row, 1)
        version_combo = _cell_combo(self.tableWidget, row, 2)
        if variant_combo is None or version_combo is None:
            return
        variant = variant_combo.currentText()
        is_asset_manager = _is_asset_manager_asset_root(asset_path)
        root_path = _asset_manager_asset_root(asset_path) if is_asset_manager else asset_path
        self._fill_version_combo(
            version_combo,
            path=root_path,
            variant=variant,
            is_asset_manager=is_asset_manager,
        )

    def importAsset(self):
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if item is None:
                continue

            asset_path = _path_from_table_item(item)
            variant_combo = _cell_combo(self.tableWidget, row, 1)
            version_combo = _cell_combo(self.tableWidget, row, 2)
            asset_type_combo = _cell_combo(self.tableWidget, row, 3)
            if variant_combo is None or version_combo is None or asset_type_combo is None:
                continue
            variant_name = variant_combo.currentText()
            version_number = version_combo.currentText()
            asset_type = asset_type_combo.currentText()

            if asset_type == "Static Mesh":
                if _is_asset_manager_asset_root(asset_path) or _is_asset_manager_version_path(
                    asset_path
                ):
                    asset_root = _asset_manager_asset_root(asset_path)
                    base_path = (
                        normalize_disk_path(os.path.join(asset_root, "publish", "model")) + "/"
                    )
                    asset_name = os.path.basename(asset_root.rstrip("/\\"))
                    identity = identity_from_base_path(
                        base_path,
                        asset_name,
                        variant_name,
                        version_number,
                    )
                    import_static_mesh_publish_pipeline(
                        identity,
                        warn=genUnrealUtils.warningPopup,
                    )
                else:
                    import_setdec_static_mesh_pipeline(
                        asset_path,
                        variant_name,
                        version_number,
                        warn=genUnrealUtils.warningPopup,
                    )

            elif asset_type == "Skeletal Mesh":
                imported_mesh, unreal_mesh_import_path = self.importSkeletalMesh(
                    asset_path, variant_name, version_number
                )
                imported_textures = self.importTextures(
                    asset_path,
                    variant_name,
                    version_number,
                    unreal_mesh_import_path,
                    asset_type,
                )
                self.assignMaterialInstanceToMesh(
                    imported_mesh, unreal_mesh_import_path, imported_textures, asset_type
                )

    def importSkeletalMesh(self, assetPath, variantName, versionNumber):
        publishedFBXPath = "{}/{}/{}/unrealExport/".format(
            assetPath, variantName, versionNumber
        )
        assetName = assetPath.split("/")[-1]
        publishDir = assetPath.split("/")[-4]
        unrealMeshImportPath = "/Game/01_Assets/{}/{}/{}/{}".format(
            publishDir, assetName, variantName, versionNumber
        )
        fbxList = [
            fbx for fbx in os.listdir(publishedFBXPath) if fbx.endswith(".fbx")
        ]
        if len(fbxList) > 1:
            genUnrealUtils.warningPopup(
                "Found too many FBX files in {} publish directory".format(assetName)
            )
        if len(fbxList) == 0:
            genUnrealUtils.warningPopup(
                "No FBX files found in {} publish directory".format(assetName)
            )
            return None, unrealMeshImportPath

        fbx_asset_path = publishedFBXPath + fbxList[0]
        import_mesh_task = genUnrealImportUtils.buildImportTask(
            fbx_asset_path,
            unrealMeshImportPath,
            genUnrealImportUtils.buildSkeletalMeshImportOptions(),
        )
        imported_mesh = genUnrealImportUtils.executeImportTasks([import_mesh_task])
        return imported_mesh, unrealMeshImportPath

    def importTextures(
        self, assetPath, variantName, versionNumber, unrealMeshImportPath, assetType
    ):
        tex_list = []
        if assetType == "Skeletal Mesh":
            published_tex_path = "{}/{}/{}/tex/".format(
                assetPath, variantName, versionNumber
            )
            for texture in os.listdir(published_tex_path):
                if texture.endswith(".png"):
                    tex_list.append(published_tex_path + texture)

        unreal_tex_import_path = "{}/TEX".format(unrealMeshImportPath)
        unreal_mat_import_path = "{}/MAT".format(unrealMeshImportPath)

        if not tex_list:
            unreal.EditorAssetLibrary.make_directory(unreal_tex_import_path)
            unreal.EditorAssetLibrary.make_directory(unreal_mat_import_path)
            return None

        tex_import_task_list = []
        for sorted_texture in tex_list:
            tex_import_task_list.append(
                genUnrealImportUtils.buildImportTask(
                    sorted_texture,
                    unreal_tex_import_path,
                )
            )
        return genUnrealImportUtils.executeImportTasks(tex_import_task_list)

    def assignMaterialInstanceToMesh(
        self, importedMesh, unrealMeshImportPath, importedTextures, assetType
    ):
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        unreal_eal = unreal.EditorAssetLibrary()
        imported_mesh = importedMesh[0].split(".")[0]
        loaded_imported_mesh = unreal_eal.load_asset(imported_mesh)
        loaded_master_material = unreal_eal.load_asset(
            "/Game/03_Shared/MasterMaterials/M_BaseMaterial_Standard_VT"
        )
        unreal_mat_import_path = "{}/MAT".format(unrealMeshImportPath)

        loaded_tex_list = []
        material_instances = []
        if importedTextures is not None:
            for texture_path in importedTextures:
                texture_path = texture_path.split(".")[0]
                loaded_texture = unreal_eal.load_asset(texture_path)
                loaded_tex_list.append(loaded_texture)

        if assetType == "Static Mesh":
            material_type_function = loaded_imported_mesh.static_materials
        if assetType == "Skeletal Mesh":
            material_type_function = loaded_imported_mesh.materials
            material_array = unreal.Array(unreal.SkeletalMaterial)

        for material in material_type_function:
            index = material_type_function.index(material)
            new_mat_name = "MI_" + str(material.material_slot_name).split("_", 1)[1]
            material_instance = asset_tools.create_asset(
                new_mat_name,
                unreal_mat_import_path,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew(),
            )
            material_instances.append(material_instance)
            material_instance.set_editor_property("parent", loaded_master_material)

            if assetType == "Static Mesh":
                loaded_imported_mesh.set_material(index, material_instance)
            if assetType == "Skeletal Mesh":
                materials_to_change = {
                    str(material.material_slot_name): material_instance
                }
                new_sk_material = unreal.SkeletalMaterial()
                slot_name = material.get_editor_property("material_slot_name")
                material_interface = material.get_editor_property("material_interface")
                if materials_to_change.get(str(slot_name)):
                    material_interface = materials_to_change[str(slot_name)]
                new_sk_material.set_editor_property("material_slot_name", slot_name)
                new_sk_material.set_editor_property("material_interface", material_interface)
                material_array.append(new_sk_material)

            if loaded_tex_list:
                for texture in loaded_tex_list:
                    if str(material.material_slot_name) in texture.get_name():
                        parameter_name = texture.get_name().split("_")[-1]
                        if parameter_name in ("AO", "Metallic", "Roughness"):
                            texture.set_editor_property("srgb", 0)
                        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                            material_instance,
                            "use{}Texture".format(parameter_name),
                            True,
                        )
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                            material_instance, parameter_name, texture
                        )
            else:
                unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                    material_instance,
                    "use{}Texture".format("Diffuse"),
                    True,
                )

        if assetType == "Skeletal Mesh":
            loaded_imported_mesh.set_editor_property("materials", material_array)

        new_assets = [loaded_tex_list, material_instances, [loaded_imported_mesh]]
        if assetType == "Skeletal Mesh":
            physics_asset = loaded_imported_mesh.get_editor_property("physics_asset")
            skeleton_asset = loaded_imported_mesh.get_editor_property("skeleton")
            new_assets.append([physics_asset])
            new_assets.append([skeleton_asset])

        for asset_list in new_assets:
            for asset in asset_list:
                asset_name_clean = asset.get_path_name().split(".")[0]
                unreal.EditorAssetLibrary.save_asset(asset_name_clean)


def openWindow():
    global _WINDOW

    app = QtWidgets.QApplication.instance()
    if app:
        if _WINDOW is not None:
            _WINDOW.close()
            _WINDOW.deleteLater()
    else:
        QtWidgets.QApplication(sys.argv)

    _WINDOW = MainWindow()
    _WINDOW.show()
    unreal.parent_external_window_to_slate(_WINDOW.winId())
