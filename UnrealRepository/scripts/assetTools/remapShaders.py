import unreal
from PySide6 import QtCore, QtGui, QtWidgets

from genTools.uiUtils import center_widget, load_qss, show_unreal_tool_window
import unrealFilePaths

WINDOW_OBJECT_NAME = "Unreal Remap Shaders"
MATERIAL_PATH_PROPERTY = "material_path"
SHADER_PLACEHOLDER = "Select a material in the Content Browser, then click the button..."
LOADED_SHADER_STYLE = "QLineEdit { font-weight: bold; color: rgb(80, 153, 255); }"
USER_ROLE = QtCore.Qt.ItemDataRole.UserRole


def _shader_icon():
    icon_root = unrealFilePaths.unrealIconPath or ""
    return QtGui.QIcon(f"{icon_root}shaderIcon.png")


def _object_path(path_name):
    """Strip the asset suffix from an Unreal object path."""
    return path_name.split(".", 1)[0]


def _sync_to_content_browser(path_name):
    if path_name:
        unreal.EditorAssetLibrary.sync_browser_to_objects([_object_path(path_name)])


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setStyleSheet(load_qss("dark.qss"))
        self.setWindowTitle("Remap multiple shaders")
        self.setFocus()
        center_widget(self)
        self.setGeometry(100, 100, 500, 500)

        self.tree_view = QtWidgets.QTreeView()
        self.model = QtGui.QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)

        self.add_selected_button = QtWidgets.QPushButton("Add (select in CB)")
        self.remove_button = QtWidgets.QPushButton("Remove Selected From List")
        self.toggle_button = QtWidgets.QPushButton("Toggle Selection")
        self.clear_button = QtWidgets.QPushButton("Clear All")
        self.remap_shaders_button = QtWidgets.QPushButton("Remap Shaders")
        self.remap_shaders_button.setStyleSheet(load_qss("importButton.qss"))

        self.loader_shader_name = QtWidgets.QLineEdit(SHADER_PLACEHOLDER)
        self.loader_shader_name.setReadOnly(True)

        self.browse_button = QtWidgets.QPushButton()
        self.browse_button.setIcon(_shader_icon())
        self.browse_button.setStyleSheet(load_qss("openButton.qss"))
        self.browse_button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.browse_button.customContextMenuRequested.connect(self._show_shader_context_menu)

        self.add_selected_button.clicked.connect(self._populate_list_with_selected)
        self.remove_button.clicked.connect(self._remove_selected_items)
        self.toggle_button.clicked.connect(self._toggle_all)
        self.clear_button.clicked.connect(self._clear_list)
        self.browse_button.clicked.connect(self._load_selected_shader)
        self.remap_shaders_button.clicked.connect(self._remap_shaders)

        button_layout = QtWidgets.QGridLayout()
        button_layout.addWidget(self.add_selected_button, 0, 0)
        button_layout.addWidget(self.remove_button, 1, 0)
        button_layout.addWidget(self.toggle_button, 2, 0)
        button_layout.addWidget(self.clear_button, 3, 0)

        shader_layout = QtWidgets.QGridLayout()
        shader_layout.addWidget(self.loader_shader_name, 0, 0, 1, 5)
        shader_layout.addWidget(self.browse_button, 0, 5, 1, 1)

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setRowStretch(1, 1)
        main_layout.addLayout(shader_layout, 0, 0, 1, 6)
        main_layout.addWidget(self.tree_view, 1, 0, 5, 5)
        main_layout.addLayout(button_layout, 1, 5, 3, 1, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(
            self.remap_shaders_button, 4, 5, alignment=QtCore.Qt.AlignmentFlag.AlignBottom
        )

    def _existing_mesh_paths(self):
        paths = set()
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item:
                paths.add(item.data(USER_ROLE))
        return paths

    def _populate_list_with_selected(self):
        existing_paths = self._existing_mesh_paths()

        for asset in unreal.EditorUtilityLibrary.get_selected_assets():
            if not isinstance(asset, unreal.StaticMesh):
                continue

            asset_path = asset.get_path_name()
            if asset_path in existing_paths:
                continue

            mesh_item = QtGui.QStandardItem(_shader_icon(), asset.get_name())
            mesh_item.setFlags(mesh_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mesh_item.setData(asset_path, USER_ROLE)
            self._make_item_bold(mesh_item)

            for material in asset.static_materials:
                slot_item = QtGui.QStandardItem(str(material.material_slot_name))
                slot_item.setFlags(slot_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                slot_item.setCheckable(True)
                slot_item.setData(asset_path, USER_ROLE)
                mesh_item.appendRow(slot_item)

            self.model.appendRow(mesh_item)
            existing_paths.add(asset_path)

        self.tree_view.expandAll()

    def _show_context_menu(self, position, sync_callback):
        menu = QtWidgets.QMenu(self)
        find_action = menu.addAction("Find in Content Browser")
        find_action.triggered.connect(sync_callback)
        menu.exec(position)

    def _show_tree_context_menu(self, position):
        if not self.tree_view.selectedIndexes():
            return
        self._show_context_menu(
            self.tree_view.viewport().mapToGlobal(position),
            self._find_mesh_in_content_browser,
        )

    def _show_shader_context_menu(self, position):
        if not self.loader_shader_name.property(MATERIAL_PATH_PROPERTY):
            return
        self._show_context_menu(QtGui.QCursor.pos(), self._find_shader_in_content_browser)

    def _find_mesh_in_content_browser(self):
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        path_name = self.model.itemFromIndex(indexes[0]).data(USER_ROLE)
        _sync_to_content_browser(path_name)

    def _find_shader_in_content_browser(self):
        _sync_to_content_browser(self.loader_shader_name.property(MATERIAL_PATH_PROPERTY))

    def _load_selected_shader(self):
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        if not selected_assets:
            return

        material = selected_assets[0]
        if not isinstance(material, (unreal.Material, unreal.MaterialInstance)):
            return

        self.loader_shader_name.setText(material.get_name())
        self.loader_shader_name.setProperty(MATERIAL_PATH_PROPERTY, material.get_path_name())
        self.loader_shader_name.setStyleSheet(LOADED_SHADER_STYLE)

    def _remap_shaders(self):
        loaded_shader_path = self.loader_shader_name.property(MATERIAL_PATH_PROPERTY)
        if not loaded_shader_path:
            return

        material = unreal.EditorAssetLibrary.load_asset(_object_path(loaded_shader_path))

        for mesh_row in range(self.model.rowCount()):
            mesh_item = self.model.item(mesh_row, 0)
            static_mesh = unreal.EditorAssetLibrary.load_asset(
                _object_path(mesh_item.data(USER_ROLE))
            )

            for slot_row in range(mesh_item.rowCount()):
                slot_item = mesh_item.child(slot_row, 0)
                if slot_item.checkState() != QtCore.Qt.CheckState.Checked:
                    continue

                slot_index = static_mesh.get_material_index(slot_item.text())
                static_mesh.set_material(slot_index, material)

    def _toggle_all(self):
        for mesh_row in range(self.model.rowCount()):
            mesh_item = self.model.item(mesh_row, 0)
            for slot_row in range(mesh_item.rowCount()):
                slot_item = mesh_item.child(slot_row, 0)
                checked = slot_item.checkState() == QtCore.Qt.CheckState.Checked
                slot_item.setCheckState(
                    QtCore.Qt.CheckState.Unchecked if checked else QtCore.Qt.CheckState.Checked
                )

    def _clear_list(self):
        self.model.clear()

    def _remove_selected_items(self):
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return

        rows_to_remove = set()
        for index in indexes:
            while index.parent().isValid():
                index = index.parent()
            rows_to_remove.add(index.row())

        for row in sorted(rows_to_remove, reverse=True):
            self.model.removeRow(row)

    def _make_item_bold(self, item, color=QtCore.Qt.GlobalColor.black):
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setForeground(QtGui.QBrush(color))


def show():
    show_unreal_tool_window(MainWindow, WINDOW_OBJECT_NAME)


openWindow = show
