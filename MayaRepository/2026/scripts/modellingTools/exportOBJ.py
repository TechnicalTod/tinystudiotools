import os
import subprocess
from PySide6 import QtGui, QtWidgets, QtCore
import maya.cmds as mc
import re
from genTools.genUtils import warningPopup, viewportMessage
import mayaFilePaths


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(600, 50)
        self.setWindowTitle("Export multiple Obj")
        self.setFocus()
        self.center()
        self.show()

        # text field widget
        self.getFilePath = QtWidgets.QLineEdit(self)
        self.getFilePath.setPlaceholderText("File path")

        # button widget
        self.exportButton = QtWidgets.QPushButton("Export each selected as Obj", self)
        self.exportButton.clicked.connect(self.ExportOBJ)

        browseButtoniconPath = mayaFilePaths.mayaShelfIconPath + "folder.png"
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(browseButtoniconPath))
        self.browseButton.clicked.connect(self.showFileDialog)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.getFilePath, 1, 0)
        self.grid.addWidget(self.browseButton, 1, 1)
        self.grid.addWidget(self.exportButton, 2, 0, 2, 2)
        self.setLayout(self.grid)

    def showFileDialog(self):
        initialDir = mayaFilePaths.downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            initialDir,
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        if dirPath:
            # Set the selected file path in the QLineEdit
            self.getFilePath.setText(dirPath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when button is pressed
    def ExportOBJ(self):
        sel = mc.ls(sl=1)
        exportPath = self.getFilePath.text()

        if not sel:
            warningPopup("No Objects Selected")
        if not exportPath:
            warningPopup("No Export folder selected")
        else:
            for objName in sel:

                print(objName)
                mc.select(objName)
                fileName = exportPath + "\\" + objName + ".obj"

                print(fileName)
                viewportMessage("exporting OBJs.......", "", "#00ff00")
                mc.file(
                    fileName,
                    pr=1,
                    typ="OBJexport",
                    es=1,
                    op="materials=0, smoothing=0, normals=0, groups=0, ptgroups=0",
                )


# definition to open UI


def launch():
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()


launch()
