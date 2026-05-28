import os
import getpass

import pymel.core as pm
import maya.OpenMayaUI as OMUI
import shiboken6
from PySide6 import QtCore, QtGui, QtWidgets

from .constants import MAIN_WINDOW_OBJECT_NAME
from .paths import setdec_group_folder, setdec_production_folder, version_asset_root
from .publish_ops import publish_set_dec, publish_set_dec_textures
from .styling import load_qss
from .unpublish_ops import unpublish_set_dec_object
from . import validation


COL_NAME = 0
COL_VARIANT = 1
COL_CUR_VERSION = 2
COL_NEW_VERSION = 3

DUPLICATE_BG_COLOR = QtGui.QColor("#7D2020")
PUBLISHED_FG_COLOR = QtGui.QColor(80, 153, 255)


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self._current_show = self._resolve_current_show()
        self._current_user = self._resolve_current_user()
        self._base_show_dir = self._resolve_base_show_dir()
        maya_win = OMUI.MQtUtil.mainWindow()
        self.setParent(shiboken6.wrapInstance(int(maya_win), QtWidgets.QWidget))
        self.setWindowFlags(QtCore.Qt.Window)
        self.initUI()

    # ---------------- construction ----------------

    def initUI(self):
        self.setObjectName(MAIN_WINDOW_OBJECT_NAME)
        self.setStyleSheet(load_qss("dark.qss"))
        self.setWindowTitle("Publish Set Dec Assets")
        self.setFocus()
        self.center()
        self.setGeometry(100, 100, 1100, 500)

        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)

        header_frame = self._build_header()
        self._build_table()
        button_layout = self._build_buttons()
        show_settings_layout = self._build_show_settings()

        layout.addWidget(header_frame, 0, 0, 1, 6)
        layout.addWidget(self.tableWidget, 1, 1, 5, 4)
        layout.addLayout(show_settings_layout, 1, 0)
        layout.addLayout(button_layout, 1, 5)
        layout.addWidget(self.exportButton, 5, 5, alignment=QtCore.Qt.AlignBottom)

        self.getShowList()
        self.show()

    def _build_table(self):
        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnWidth(COL_NAME, 800)
        self.tableWidget.setColumnWidth(COL_VARIANT, 200)
        self.tableWidget.setColumnWidth(COL_CUR_VERSION, 100)
        self.tableWidget.setColumnWidth(COL_NEW_VERSION, 100)
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(COL_NAME, QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Set Dec name", "Variant", "Current Version", "New Version"]
        )
        self.tableWidget.cellClicked.connect(self.cellClickedGrabShape)

    def _build_buttons(self):
        button_layout = QtWidgets.QGridLayout()

        self.addButton = QtWidgets.QPushButton("Add Set Dec")
        self.addButton.clicked.connect(self.add)

        self.removeButton = QtWidgets.QPushButton("Remove Selection")
        self.removeButton.clicked.connect(self.remove)

        self.clearButton = QtWidgets.QPushButton("Clear All")
        self.clearButton.clicked.connect(self.clear)

        self.refreshButton = QtWidgets.QPushButton("Refresh List")
        self.refreshButton.clicked.connect(self.resetCurrentList)

        self.unpublishButton = QtWidgets.QPushButton("Unpublish Selection")
        self.unpublishButton.clicked.connect(self.unpublishSelected)
        self.unpublishButton.setStyleSheet(load_qss("unpublishButton.qss"))

        self.exportButton = QtWidgets.QPushButton("Publish")
        self.exportButton.clicked.connect(self.collectListForPublish)
        self.exportButton.setStyleSheet(load_qss("importButton.qss"))

        button_layout.addWidget(self.addButton, 0, 5)
        button_layout.addWidget(self.removeButton, 1, 5)
        button_layout.addWidget(self.clearButton, 2, 5)
        button_layout.addWidget(self.refreshButton, 3, 5)
        button_layout.addWidget(self.unpublishButton, 4, 5)
        return button_layout

    def _build_show_settings(self):
        show_settings_layout = QtWidgets.QGridLayout()

        self.setDecGroupComboBoxLabel = QtWidgets.QLabel("Set Dec Group")
        self.setDecGroupComboBox = QtWidgets.QComboBox()
        self.setDecGroupComboBox.setEditable(True)
        self.setDecGroupComboBox.currentTextChanged.connect(self.resetCurrentList)

        show_settings_layout.addWidget(self.setDecGroupComboBoxLabel, 0, 0)
        show_settings_layout.addWidget(self.setDecGroupComboBox, 1, 0)
        return show_settings_layout

    def _build_header(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        title = QtWidgets.QLabel("<b>Show:</b> {}".format(self._current_show))
        user = QtWidgets.QLabel("<b>User:</b> {}".format(self._current_user))
        drive = QtWidgets.QLabel("<b>Drive:</b> {}".format(self._base_show_dir))

        for widget in (title, user, drive):
            widget.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(user)
        layout.addStretch(1)
        layout.addWidget(drive)
        return frame

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # ---------------- context ----------------

    @staticmethod
    def _resolve_current_show():
        current_show = os.environ.get("SHOW_NAME", "").strip()
        if not current_show:
            raise RuntimeError(
                "SHOW_NAME is not set. Launch Maya through TinyStudioLauncher, "
                "then reopen Publish Set Dec Assets."
            )
        return current_show

    @staticmethod
    def _resolve_current_user():
        return os.environ.get("USERNAME", "").strip() or getpass.getuser()

    @staticmethod
    def _resolve_base_show_dir():
        return os.environ.get("TINYSTUDIO_BASE_SHOW_DIR", "").strip() or "N/A"

    # ---------------- table helpers ----------------

    def _selected_rows(self):
        return sorted({i.row() for i in self.tableWidget.selectedIndexes()})

    def _row_set_dec(self, row):
        """Return (pyNode, short_name) for the asset at `row`."""
        set_dec_name = self.tableWidget.item(row, COL_NAME).text()
        obj = pm.PyNode(set_dec_name)
        return obj, obj.nodeName().split("|")[-1]

    def _transform_dag_paths_from_table(self):
        return [
            self.tableWidget.item(row, COL_NAME).text()
            for row in range(self.tableWidget.rowCount())
        ]

    # ---------------- add row ----------------

    def add(self, shapeList=None):
        set_dec_group_folder_name = setdec_group_folder(
            self._current_show, self.setDecGroupComboBox.currentText()
        )

        shapes = shapeList if shapeList else pm.ls(sl=1)

        bad_shape_list = []
        for shape in shapes:
            shape = pm.PyNode(shape)
            shape_node = shape.getShape()
            if not (shape_node and shape_node.nodeType() == "mesh"):
                bad_shape_list.append(shape.name())

        if bad_shape_list:
            self.warningPopup(
                "You are trying to load a Set Dec item with no connected shapes, "
                "this item has been removed from the list: {}".format(", ".join(bad_shape_list))
            )

        shapes = [x for x in shapes if x not in bad_shape_list]
        init_row_number = self.tableWidget.rowCount()

        for row_number, shape in enumerate(shapes):
            shape = pm.PyNode(shape)
            split_shape_name = shape.nodeName().split("|")[-1]
            row = init_row_number + row_number
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, COL_NAME, QtWidgets.QTableWidgetItem(shape.name()))

            variant_combo_box = QtWidgets.QComboBox()
            variant_combo_box.setEditable(True)
            self.tableWidget.setCellWidget(row, COL_VARIANT, variant_combo_box)
            try:
                variant_list = os.listdir(set_dec_group_folder_name + split_shape_name)
                variant_combo_box.addItems(variant_list)
                variant_combo_box.setCurrentIndex(0)
                if len(variant_list) > 1:
                    variant_combo_box.setStyleSheet(load_qss("qComboBoxMultiItemYellow.qss"))
            except Exception:
                variant_combo_box.addItems(["base"])
                variant_combo_box.setCurrentIndex(0)

            version_combo_box = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(row, COL_CUR_VERSION, version_combo_box)
            try:
                version_list = os.listdir(
                    set_dec_group_folder_name
                    + split_shape_name
                    + "/"
                    + variant_combo_box.currentText()
                )
                version_combo_box.addItems(version_list)
                version_combo_box.setCurrentIndex(len(version_list) - 1)
            except Exception:
                version_combo_box.addItems(["N/A"])
                version_combo_box.setStyleSheet(load_qss("qComboBoxMultiItemGreen.qss"))
                version_combo_box.setCurrentIndex(0)

            new_version_combo_box = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(row, COL_NEW_VERSION, new_version_combo_box)

            self.getLatestVersionNumber(version_combo_box, new_version_combo_box)

            variant_combo_box.currentTextChanged.connect(
                lambda _text, row=row: self.updateVerNumOnVarChange(row)
            )
            version_combo_box.currentTextChanged.connect(
                lambda _text,
                v=version_combo_box,
                nv=new_version_combo_box: self.getLatestVersionNumber(v, nv)
            )

        self.setDuplicateInputsRed()
        self.setPublishedInputsBlue()

    # ---------------- context / table actions ----------------

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Set variant names on multiple selection", self.renameSelectedVariants)
        menu.addSeparator()
        menu.addAction("Remove selected item(s) from list", self.remove)
        menu.exec_(self.mapToGlobal(event.pos()))

    def updateVerNumOnVarChange(self, row):
        set_dec_group_folder_name = setdec_group_folder(
            self._current_show, self.setDecGroupComboBox.currentText()
        )

        _, split_set_dec_object_name = self._row_set_dec(row)
        set_dec_variant = self.tableWidget.cellWidget(row, COL_VARIANT).currentText()
        set_dec_current_version = self.tableWidget.cellWidget(row, COL_CUR_VERSION)
        set_dec_new_version = self.tableWidget.cellWidget(row, COL_NEW_VERSION)

        set_dec_current_version.clear()
        try:
            version_list = os.listdir(
                set_dec_group_folder_name + split_set_dec_object_name + "/" + set_dec_variant
            )
            set_dec_current_version.addItems(version_list)
            set_dec_current_version.setCurrentIndex(len(version_list) - 1)
            self.getLatestVersionNumber(set_dec_current_version, set_dec_new_version)
            set_dec_current_version.setStyleSheet(load_qss("dark.qss"))
        except Exception:
            set_dec_new_version.clear()
            set_dec_current_version.addItems(["N/A"])
            set_dec_current_version.setStyleSheet(load_qss("qComboBoxMultiItemGreen.qss"))
            set_dec_current_version.setCurrentIndex(0)
            set_dec_new_version.addItems(["v001"])
            set_dec_new_version.setCurrentIndex(0)

        print(
            "Variant changed to {}/{} finding latest versions".format(
                split_set_dec_object_name, set_dec_variant
            )
        )

    def remove(self):
        for row in reversed(self._selected_rows()):
            self.tableWidget.removeRow(row)
        self.resetCurrentList()

    def clear(self):
        self.tableWidget.setRowCount(0)

    def renameSelectedVariants(self):
        input_dialog = QtWidgets.QInputDialog(self)
        input_dialog.setStyleSheet(load_qss("dark.qss"))
        new_variant_name, ok = input_dialog.getText(
            self, "Set Variant Name", "Enter new variant name:"
        )
        if not ok:
            return
        for row in self._selected_rows():
            set_dec_variant = self.tableWidget.cellWidget(row, COL_VARIANT)
            set_dec_variant.addItem(new_variant_name)
            set_dec_variant.setCurrentText(new_variant_name)
            self.updateVerNumOnVarChange(row)

    def resetCurrentList(self):
        store_selection = pm.ls(sl=1)
        pm.select(clear=1)
        set_dec_asset_list = []
        for row in range(self.tableWidget.rowCount()):
            set_dec_name = self.tableWidget.item(row, COL_NAME).text()
            if pm.objExists(set_dec_name):
                set_dec_asset_list.append(set_dec_name)
            else:
                print(
                    "Found asset that no longer exists, removing from list{}".format(set_dec_name)
                )
        self.clear()
        self.add(set_dec_asset_list)
        pm.select(store_selection)

    def getShowList(self):
        self.updateSetDecGroupComboBox()

    def updateSetDecGroupComboBox(self):
        self.resetCurrentList()
        self.setDecGroupComboBox.clear()
        production_folder = setdec_production_folder(self._current_show)
        if os.path.exists(production_folder):
            self.setDecGroupComboBox.addItems(os.listdir(production_folder))

    # ---------------- validation passthrough ----------------

    def getDuplicatesInList(self):
        return validation.duplicate_short_names(self._transform_dag_paths_from_table())

    def getPublishedInList(self):
        return validation.published_short_names(self._transform_dag_paths_from_table())

    def checkShadersInList(self):
        return validation.invalid_shader_short_names(self._transform_dag_paths_from_table())

    def setDuplicateInputsRed(self):
        duplicates = self.getDuplicatesInList()
        for row in range(self.tableWidget.rowCount()):
            _, short_name = self._row_set_dec(row)
            if short_name in duplicates:
                self.tableWidget.item(row, COL_NAME).setBackground(DUPLICATE_BG_COLOR)

    def setPublishedInputsBlue(self):
        published = set(self.getPublishedInList())
        for row in range(self.tableWidget.rowCount()):
            _, short_name = self._row_set_dec(row)
            if short_name in published:
                self.tableWidget.item(row, COL_NAME).setForeground(PUBLISHED_FG_COLOR)

    # ---------------- publish / unpublish ----------------

    def unpublishSelected(self):
        for row in reversed(self._selected_rows()):
            obj, _ = self._row_set_dec(row)
            unpublish_set_dec_object(obj)
        self.resetCurrentList()

    def collectListForPublish(self):
        broken_shader_shape_names = self.checkShadersInList()
        if broken_shader_shape_names:
            self.warningPopup(
                "Incorrect shaders found in list: {}, must be USD Preview material".format(
                    ", ".join(broken_shader_shape_names)
                )
            )
            return

        duplicate_shape_names = self.getDuplicatesInList()
        if duplicate_shape_names:
            self.warningPopup(
                "Duplicate shape names found in list: {}, "
                "please fix or remove from list before publishing".format(
                    ", ".join(duplicate_shape_names)
                )
            )
            return

        published_shape_names = self.getPublishedInList()
        if published_shape_names:
            self.warningPopup(
                "Published shapes found in list: {}, "
                "please unpublish or remove from list before publishing".format(
                    ", ".join(published_shape_names)
                )
            )
            return

        print("No duplicate shape names found in the selection, continuing")
        group_name = self.setDecGroupComboBox.currentText()
        set_dec_group_folder_name = setdec_group_folder(self._current_show, group_name)

        pm.undoInfo(openChunk=True)
        try:
            for row in range(self.tableWidget.rowCount()):
                set_dec_name = self.tableWidget.item(row, COL_NAME).text()
                if not pm.objExists(set_dec_name):
                    print("Node '{}' does not exist.".format(set_dec_name))
                    continue
                set_dec_object = pm.PyNode(set_dec_name)
                split_set_dec_object_name = set_dec_object.nodeName().split("|")[-1]
                set_dec_variant_name = self.tableWidget.cellWidget(row, COL_VARIANT).currentText()
                set_dec_new_version = self.tableWidget.cellWidget(
                    row, COL_NEW_VERSION
                ).currentText()

                set_dec_asset_path = version_asset_root(
                    self._current_show,
                    group_name,
                    split_set_dec_object_name,
                    set_dec_variant_name,
                    set_dec_new_version,
                )
                existing_shaders, _, _ = publish_set_dec_textures(
                    set_dec_object,
                    set_dec_asset_path,
                )
                publish_set_dec(
                    set_dec_object,
                    split_set_dec_object_name,
                    set_dec_variant_name,
                    set_dec_new_version,
                    existing_shaders,
                    set_dec_group_folder_name,
                )
        finally:
            pm.undoInfo(closeChunk=True)

        self.resetCurrentList()

    # ---------------- misc ----------------

    def getLatestVersionNumber(self, current_version_combo_box, new_version_combo_box):
        new_version_combo_box.clear()
        if current_version_combo_box.currentText() == "N/A":
            new_version_combo_box.addItems(["v001"])
            new_version_combo_box.setCurrentIndex(0)
            return
        try:
            ver_num = int(current_version_combo_box.currentText()[1:])
            new_version_list = ["v{:03d}".format(num + 1) for num in range(ver_num + 1)]
            new_version_combo_box.addItems(new_version_list)
            new_version_combo_box.setCurrentIndex(len(new_version_list) - 1)
        except ValueError:
            pass

    def cellClickedGrabShape(self, row, column):
        if column != COL_NAME:
            return
        current_row = self.tableWidget.currentRow()
        current_column = self.tableWidget.currentColumn()
        pm.select(self.tableWidget.item(current_row, current_column).text())

    def warningPopup(self, message):
        dialog = QtWidgets.QMessageBox()
        dialog.setStyleSheet(load_qss("dark.qss"))
        dialog.setText(message)
        dialog.setWindowTitle("Warning")
        dialog.exec_()
        print(message)
