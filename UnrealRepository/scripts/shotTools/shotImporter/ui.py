"""Qt UI for importing published Maya shots into Unreal."""

from __future__ import annotations

import sys

import unreal
from PySide6 import QtGui, QtWidgets

from genTools.uiUtils import center_widget, load_qss
import unrealFilePaths

from .import_service import import_shot_from_json


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(600, 50)
        self.setWindowTitle("Import published Shot")
        self.setFocus()
        self.center()
        self.show()

        self.jsonFilePath = QtWidgets.QLineEdit(self)
        self.jsonFilePath.setPlaceholderText("File path")

        self.importJsonButton = QtWidgets.QPushButton(
            "Import Shot from Scene Description", self
        )
        self.importJsonButton.clicked.connect(self.importShot)

        open_folder_icon_filepath = unrealFilePaths.unrealIconPath + "folder.png"
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(open_folder_icon_filepath))
        self.browseButton.clicked.connect(self.showFileDialog)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.jsonFilePath, 0, 0, 1, 3)
        grid.addWidget(self.browseButton, 0, 3, 1, 1)
        grid.addWidget(self.importJsonButton, 1, 0, 1, 4)
        self.setLayout(grid)

    def showFileDialog(self):
        initial_dir = unrealFilePaths.downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        file_filter = "Json Files (*.json);;All Files (*)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Json File", initial_dir, file_filter, options=options
        )
        if file_path:
            self.jsonFilePath.setText(file_path)

    def center(self):
        center_widget(self)

    def importShot(self):
        json_path = self.jsonFilePath.text()
        result = import_shot_from_json(json_path)

        for warning in result.warnings:
            print(warning)

        if result.errors:
            self.warningPopup("\n".join(result.errors))
            return

        print("Shot import completed successfully.")

    def warningPopup(self, message):
        dialog = QtWidgets.QMessageBox(self)
        dialog.setStyleSheet(load_qss("dark.qss"))
        dialog.setText(message)
        dialog.setWindowTitle("Import Shot")
        dialog.exec_()
        print(message)


def openWindow():
    if QtWidgets.QApplication.instance():
        for win in QtWidgets.QApplication.allWindows():
            print(win.objectName())
            if "Import Unreal Assets" in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)

    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())
