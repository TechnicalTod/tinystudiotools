import os
import unreal
import sys
import subprocess
from PySide2 import QtGui, QtWidgets, QtCore

import re
from importlib import reload
import unrealFilePaths
reload(unrealFilePaths)

import USD_exporter

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.UNREAL_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(400, 50)
        self.setWindowTitle('Bulk Export Assets to USD')
        self.setFocus()
        self.center()
        self.show()

        # Create a combo box and populate it with files from the directory
        self.exportDirLabel = QtWidgets.QLabel("Export Directory:")
        self.exportDir = QtWidgets.QLineEdit(self)

        # button widget
        self.exportUSDButton = QtWidgets.QPushButton('Export Selected', self)
        self.exportUSDButton.clicked.connect(self.exportUSD)
       
        # button widget
        openFolderIconFilepath = unrealFilePaths.UNREAL_openFolderIconFilepath
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(openFolderIconFilepath))
        self.browseButton.clicked.connect(self.browseButtonLaunch)

        # Initialize the grid layout with spacing
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # Set size policies for buttons
        self.exportUSDButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.browseButton.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)

        # Add widgets to layout with consistent spanning
        self.grid.addWidget(self.exportDirLabel, 1, 0)
        self.grid.addWidget(self.exportDir, 1, 1, 1, 3)  # Span across all remaining columns
        self.grid.addWidget(self.browseButton, 1, 4)  # Single column on the right end

        self.grid.addWidget(self.exportUSDButton, 2, 0, 1, 5)  # Span across all columns

        # Set the overall layout
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when export button is pressed
    def exportUSD(self):
        exportDir = self.exportDir.text()
        USD_exporter.exportSelectedAssets(exportDir)
        print(f"Exporting to directory: {exportDir}")
        
    def browseButtonLaunch(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if directory:
            self.exportDir.setText(directory)

#open UI
def openWindow():
    if QtWidgets.QApplication.instance():
        #Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            print(win.objectName())
            if 'Import Unreal Assets' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())

#openWindow()
