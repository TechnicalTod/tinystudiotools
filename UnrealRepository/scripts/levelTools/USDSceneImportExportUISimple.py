import os
import unreal
import sys
import subprocess
from PySide6 import QtGui, QtWidgets, QtCore

from importlib import reload
import unrealFilePaths

reload(unrealFilePaths)

import levelTools.USDSceneBuilderUnreal as usd_builder
import levelTools.USDSceneExporterUnreal as usd_exporter


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(600, 50)
        self.setWindowTitle("Import / Export USD Scene description")
        self.setFocus()
        self.center()
        self.show()

        # text field widget
        self.USDFilePath = QtWidgets.QLineEdit(self)
        self.USDFilePath.setPlaceholderText("File path")

        # button widget
        self.importUSDButton = QtWidgets.QPushButton("Import USD", self)
        self.importUSDButton.clicked.connect(self.importUSD)

        # button widget
        self.exportUSDButton = QtWidgets.QPushButton("Export USD", self)
        self.exportUSDButton.clicked.connect(self.exportUSD)

        openFolderIconFilepath = unrealFilePaths.unrealIconPath + "folder.png"
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(openFolderIconFilepath))
        self.browseButton.clicked.connect(self.showFileDialog)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.USDFilePath, 1, 0, 1, 3)
        self.grid.addWidget(self.browseButton, 1, 3, 1, 1)
        self.grid.addWidget(self.importUSDButton, 2, 0, 1, 2)
        self.grid.addWidget(self.exportUSDButton, 2, 2, 1, 2)
        self.setLayout(self.grid)

    def showFileDialog(self):
        initialDir = unrealFilePaths.downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        fileFilter = "USD Files (*.usd *.usda *.usdz);;All Files (*)"
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open USD File", initialDir, fileFilter, options=options
        )
        if filePath:
            # Set the selected file path in the QLineEdit
            self.USDFilePath.setText(filePath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when import button is pressed
    def importUSD(self):
        USDPath = self.USDFilePath.text()
        usd_builder.BuildScene(USDPath)

    # definition called when export button is pressed
    def exportUSD(self):
        USDPath = self.USDFilePath.text()
        usd_exporter.ExportScene(USDPath)


# definition to open UI


# open UI
def openWindow():
    if QtWidgets.QApplication.instance():
        # Id any current instances of tool and destroy
        for win in QtWidgets.QApplication.allWindows():
            print(win.objectName())
            if "Import Unreal Assets" in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())
