from __future__ import annotations

import os

import maya.OpenMayaUI as OMUI
import pymel.core as pm
import shiboken6
from PySide6 import QtCore, QtGui, QtWidgets

import mayaFilePaths
from genTools.uiUtils import load_qss

from . import paths, publish_ops, scene_scan


ITEM_ROLE = QtCore.Qt.UserRole


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        maya_win = OMUI.MQtUtil.mainWindow()
        self.mayaWin = shiboken6.wrapInstance(int(maya_win), QtWidgets.QWidget)
        self.setParent(self.mayaWin)
        self.setWindowFlags(QtCore.Qt.Window)
        self.manifest = None
        self.initUI()

    def initUI(self):
        self.setStyleSheet(load_qss("dark.qss"))
        self.setWindowTitle("Publish Shot For Unreal")
        self.setFocus()
        self.center()
        self.resize(500, 500)

        self.createWidgets()
        self.connectLayout()
        self.populatePublishTree()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        screen = QtWidgets.QApplication.primaryScreen() or QtGui.QGuiApplication.primaryScreen()
        if screen is not None:
            qr.moveCenter(screen.availableGeometry().center())
            self.move(qr.topLeft())

    def createWidgets(self):
        self.treeView = QtWidgets.QTreeView()
        self.refreshButton = QtWidgets.QPushButton("Refresh")
        self.removeButton = QtWidgets.QPushButton("Remove Selected")
        self.clearButton = QtWidgets.QPushButton("Clear All")
        self.openFolderButton = QtWidgets.QPushButton("Open publish dir")
        self.publishButton = QtWidgets.QPushButton("Publish Shot")

        self.openFolderButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.openFolderButton.customContextMenuRequested.connect(self.showContextMenu)

        self.publishButton.setStyleSheet(load_qss("importButton.qss"))
        self.openFolderButton.setStyleSheet(load_qss("openButton.qss"))

        self.model = QtGui.QStandardItemModel()
        self.treeView.setModel(self.model)
        self.treeView.setHeaderHidden(True)

    def connectLayout(self):
        self.treeView.clicked.connect(self.itemGrabShape)
        self.refreshButton.clicked.connect(self.refreshManifest)
        self.removeButton.clicked.connect(self.removeSelectedItems)
        self.publishButton.clicked.connect(self.collectPublishData)
        self.openFolderButton.clicked.connect(self.getExportDir)
        self.clearButton.clicked.connect(self.clearList)

        button_layout = QtWidgets.QGridLayout()
        button_layout.addWidget(self.refreshButton, 0, 0)
        button_layout.addWidget(self.removeButton, 1, 0)
        button_layout.addWidget(self.clearButton, 2, 0)

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setRowStretch(1, 1)
        main_layout.addWidget(self.treeView, 0, 0, 5, 4)
        main_layout.addLayout(button_layout, 0, 5, 1, 1)
        main_layout.addWidget(self.openFolderButton, 3, 5, alignment=QtCore.Qt.AlignBottom)
        main_layout.addWidget(self.publishButton, 4, 5, alignment=QtCore.Qt.AlignBottom)

    def showContextMenu(self, position):
        context_menu = QtWidgets.QMenu(self)
        copy_action = context_menu.addAction("Copy Scene Desc Json Path")
        copy_action.triggered.connect(self.copyPathToClipboard)
        context_menu.exec_(QtGui.QCursor.pos())

    def copyPathToClipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(str(self.getSceneDescriptionPath()))

    def refreshManifest(self):
        self.manifest = scene_scan.build_manifest()
        self.populatePublishTree()

    def populatePublishTree(self):
        if self.manifest is None:
            self.manifest = scene_scan.build_manifest()

        self.model.clear()
        self.cameraGroup = self._group_item("snapshotTools.png", "Cameras")
        self.puppetGroup = self._group_item("centerPivot.png", "Puppets")
        self.customGeoGroup = self._group_item("modelling.png", "Custom Geo")
        self.shotInfoGroup = self._group_item("techvis.png", "Shot Info")
        self.extraInfoGroup = self._group_item("modelling.png", "Extra Info")

        self.model.appendRow(self.cameraGroup)
        self.model.appendRow(self.puppetGroup)
        self.model.appendRow(self.customGeoGroup)
        self.model.appendRow(self.shotInfoGroup)
        self.model.appendRow(self.extraInfoGroup)

        self._populate_cameras()
        self._populate_puppets()
        self._populate_custom_geo()
        self._populate_shot_info()
        self._populate_extra_info()
        self.treeView.expandAll()

    def _icon(self, icon_name):
        icon_root = mayaFilePaths.mayaShelfIconPath or ""
        icon_path = "{}{}".format(icon_root, icon_name)
        return QtGui.QIcon(icon_path) if icon_root else QtGui.QIcon()

    def _group_item(self, icon_name, label):
        item = QtGui.QStandardItem(self._icon(icon_name), label)
        self.makeItemBold([item], QtCore.Qt.black)
        return item

    def _title_item(self, label, payload=None):
        item = QtGui.QStandardItem(label)
        item.setEditable(False)
        if payload is not None:
            item.setData(payload, ITEM_ROLE)
        self.makeItemBold([item], QtCore.Qt.white)
        return item

    def _child_item(self, label, value):
        item = QtGui.QStandardItem("{}: {}".format(label, value))
        item.setEditable(False)
        return item

    def _populate_cameras(self):
        for camera in self.manifest.cameras:
            title_item = self._title_item(camera.name, ("camera", camera.name))
            self.cameraGroup.appendRow(title_item)
            for label, value in camera.attributes().items():
                title_item.appendRow(self._child_item(label, value))

    def _populate_puppets(self):
        for puppet in self.manifest.puppets:
            title_item = self._title_item(puppet.name, ("puppet", puppet.name))
            self.puppetGroup.appendRow(title_item)
            for label, value in puppet.attributes().items():
                title_item.appendRow(self._child_item(label, value))

    def _populate_custom_geo(self):
        if not self.manifest.custom_geo:
            self.customGeoGroup.appendRow(
                QtGui.QStandardItem(
                    "N/A — use Add Custom Geo to Set on Unreal Tools shelf"
                )
            )
            return
        for item in self.manifest.custom_geo:
            title_item = self._title_item(item.name, ("custom_geo", item.name))
            self.customGeoGroup.appendRow(title_item)
            for label, value in item.attributes().items():
                title_item.appendRow(self._child_item(label, value))

    def _populate_shot_info(self):
        for label, value in self.manifest.shot_info.display_rows():
            title_item = self._title_item(label)
            self.shotInfoGroup.appendRow(title_item)
            title_item.appendRow(QtGui.QStandardItem(str(value)))

    def _populate_extra_info(self):
        if not self.manifest.extra_info:
            self.extraInfoGroup.appendRow(QtGui.QStandardItem("N/A"))
            return
        for label, value in self.manifest.extra_info.items():
            self.extraInfoGroup.appendRow(self._child_item(label, value))

    def clearList(self):
        if self.manifest is None:
            self.manifest = scene_scan.build_manifest()
        self.manifest.clear_publish_items()
        self.populatePublishTree()

    def _payload_for_index(self, index):
        if not index.isValid():
            return None
        item = self.model.itemFromIndex(index)
        while item is not None:
            payload = item.data(ITEM_ROLE)
            if payload:
                return payload
            item = item.parent()
        return None

    def removeSelectedItems(self):
        payload = self._payload_for_index(self.treeView.currentIndex())
        if not payload:
            return
        item_type, item_name = payload
        if item_type == "camera":
            self.manifest.remove_camera(item_name)
        elif item_type == "puppet":
            self.manifest.remove_puppet(item_name)
        elif item_type == "custom_geo":
            self.manifest.remove_custom_geo(item_name)
        self.populatePublishTree()

    def getExportDir(self):
        try:
            publish_root = paths.publish_root(self.manifest.shot_info)
            paths.create_directory(publish_root)
            os.startfile(publish_root.as_posix())
        except Exception as exc:
            self.warningPopup(str(exc))

    def getSceneDescriptionPath(self):
        try:
            return paths.scene_description_path(self.manifest.shot_info).as_posix()
        except Exception as exc:
            self.warningPopup(str(exc))
            return ""

    def collectPublishData(self):
        try:
            json_export_path = publish_ops.publish_manifest(self.manifest)
        except Exception as exc:
            self.warningPopup(str(exc))
            return
        self.populatePublishTree()
        print("Shot description exported: {}".format(json_export_path.as_posix()))

    def makeItemBold(self, items, color):
        for item in items:
            font = QtGui.QFont()
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QtGui.QBrush(color))

    def itemGrabShape(self, index: QtCore.QModelIndex):
        payload = self._payload_for_index(index)
        if payload:
            _, item_name = payload
            try:
                pm.select(item_name)
            except Exception:
                pass

    def warningPopup(self, message):
        dialog = QtWidgets.QMessageBox(self)
        dialog.setStyleSheet(load_qss("dark.qss"))
        dialog.setText(message)
        dialog.setWindowTitle("Warning")
        dialog.exec_()
        print(message)


def launch():
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()

