import os
import subprocess
from genTools.genUtils import warningPopup
from PySide2 import QtGui, QtWidgets, QtCore

from importlib import reload
import filePaths
reload(filePaths)

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        self.resize(600, 50)
        self.setWindowTitle('Create asset directories')
        self.setFocus()
        self.style_sheet_file_loc = filePaths.styleSheetFilepath
        with open("{}/dark.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.center()
        self.show()

        # text field widget
        self.getAssetName = QtWidgets.QLineEdit(self)
        self.getAssetName.setPlaceholderText("Asset Name")

        # button widget
        button = QtWidgets.QPushButton('Create folder structure', self)
        button.clicked.connect(self.makeAssetDir)

        # radio widget
        self.AssetDirRadioButton = QtWidgets.QRadioButton('Asset Directory')
        self.techvisDirRadioButton = QtWidgets.QRadioButton(
            'Techvis Directory')

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.AssetDirRadioButton, 0, 0)
        self.grid.addWidget(self.techvisDirRadioButton, 0, 1)
        self.grid.addWidget(self.getAssetName, 1, 0, 1, 2)
        self.grid.addWidget(button, 2, 0, 1, 2)
        self.AssetDirRadioButton.setChecked(True)
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when button is pressed
    def makeAssetDir(self):
        folderName = None

        if self.AssetDirRadioButton.isChecked():
            folderName = 'assets\\'
        if self.techvisDirRadioButton.isChecked():
            folderName = 'techvis\\'

        assetname = self.getAssetName.text()

        if not assetname:
            warningPopup('No asset name specified')
        else:
            baseUserDir = filePaths.userProjectsDir + folderName

            dirList = []

            dirList.append(baseUserDir + assetname)
            dirList.append(baseUserDir + assetname + '\\scenes')
            dirList.append(baseUserDir + assetname + '\\sourceimages')
            dirList.append(baseUserDir + assetname + '\\sourceimages\\ref')
            dirList.append(baseUserDir + assetname + '\\sourceimages\\textures')
            dirList.append(baseUserDir + assetname + '\\tempOBJ')

            print (baseUserDir + assetname)

            for dir in dirList:
                try:
                    os.mkdir(dir)
                except:
                    print ('looks like {0} already exists...skipping'.format(dir))

            fileList = []

            fileList.append(baseUserDir + assetname +
                            '\\scenes\\{0}_workingMayaFile_V001.ma'.format(assetname))
            fileList.append(baseUserDir + assetname +
                            '\\scenes\\{0}_workingSubstanceFile_V001.spp'.format(assetname))

            for fileName in fileList:
                with open(fileName, 'a'):
                    os.utime(fileName, None)

# definition to open UI

def launch():
     global win
     win = MainWindow()
     win.raise_()
     win.activateWindow()
     win.show()
