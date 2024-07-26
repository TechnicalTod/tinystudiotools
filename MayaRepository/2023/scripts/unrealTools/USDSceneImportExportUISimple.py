import os
import sys
import subprocess
from PySide2 import QtGui, QtWidgets, QtCore

import mayaFilePaths

import unrealTools.USDSceneBuilderMaya as sceneBuilder
import unrealTools.USDSceneExporterMaya as sceneExporter

import unrealTools.USDSceneImportExportUISimple as simpleUI

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(previsFilePaths.PREVISSHELF_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(600, 50)
        self.setWindowTitle('Import / Export USD Scene description')
        self.setFocus()
        self.center()
        self.show()

        # Create a combo box and populate it with files from the directory
        self.showDirLabel = QtWidgets.QLabel("Show Directory:")
        self.showDir = QtWidgets.QComboBox(self)
        self.populateShowComboBox('Y:/')
        self.showDir.currentIndexChanged.connect(lambda: self.populateAssetComboBox())

        # Create a combo box and populate it with files from the directory
        self.assetDirLabel = QtWidgets.QLabel("Environment Name:")
        self.assetDir = QtWidgets.QComboBox(self)
        self.populateAssetComboBox()
        self.assetDir.setEditable(True)
        self.assetDir.currentIndexChanged.connect(lambda: self.populateItemComboBox())
        self.assetDir.editTextChanged.connect(lambda: self.populateItemComboBox())

        # Create a combo box and populate it with files from the directory
        self.itemDirLabel = QtWidgets.QLabel("USD Name:")
        self.itemDir = QtWidgets.QComboBox(self)
        self.populateItemComboBox()
        self.itemDir.setEditable(True)
        
        # button widget
        self.importUSDButton = QtWidgets.QPushButton('Import USD', self)
        self.importUSDButton.clicked.connect(self.importUSD)

        # button widget
        self.exportUSDButton = QtWidgets.QPushButton('Export USD', self)
        self.exportUSDButton.clicked.connect(self.exportUSD)
        
        # button widget
        openFolderIconFilepath = previsFilePaths.PREVISSHELF_openFolderIconFilepath
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(openFolderIconFilepath))
        self.browseButton.clicked.connect(lambda: self.browseButtonLaunch())

        # Initialize the grid layout with spacing
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # Set size policies for buttons
        self.importUSDButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.exportUSDButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.browseButton.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)

        # Add widgets to layout with consistent spanning
        self.grid.addWidget(self.showDirLabel, 1, 0)
        self.grid.addWidget(self.showDir, 1, 1, 1, -1)  # Span across all remaining columns
        self.grid.addWidget(self.assetDirLabel, 2, 0)
        self.grid.addWidget(self.assetDir, 2, 1, 1, -1)  # Same span for consistency
        self.grid.addWidget(self.itemDirLabel, 3, 0)
        self.grid.addWidget(self.itemDir, 3, 1, 1, -1)  # Consistent span

        # Adding buttons with adjusted spans to fill space appropriately
        self.grid.addWidget(self.importUSDButton, 4, 0, 1, 2)  # Spans two columns, adjusted for more space
        self.grid.addWidget(self.exportUSDButton, 4, 2, 1, 2)  # Spans two columns, adjusted for equal size
        self.grid.addWidget(self.browseButton, 4, 4)  # Single column on the right end

        # Set column stretches to manage space distribution effectively
        self.grid.setColumnStretch(0, 2)  # Larger stretch for first part of the buttons
        self.grid.setColumnStretch(1, 2)  # Equal stretch to the first, for import button
        self.grid.setColumnStretch(2, 2)  # Equal stretch to the first, for export button
        self.grid.setColumnStretch(3, 2)  # Equal stretch to the second, for export button
        self.grid.setColumnStretch(4, 1)  # Less stretch for browse button

        # Set the overall layout
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when import button is pressed
    def importUSD(self):
        showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        itemdir = self.itemDir.currentText()
        USDPath = 'Y:/' + showdir + '/assets/SceneDesc/' + assetdir + '/' + itemdir
        USDPath = USDPath.replace(" ", '_')
        sceneBuilder.BuildScene(USDPath)

    # definition called when export button is pressed
    def exportUSD(self):
        showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        itemdir = self.itemDir.currentText()
        if showdir != '' and assetdir != '' and itemdir != '':
            coredir = 'Y:/' + showdir + '/assets/SceneDesc/' + assetdir
            coredir = coredir.replace(" ", '_')
            if not os.path.exists(coredir):
                os.makedirs(coredir)
            USDPath = 'Y:/' + showdir + '/assets/SceneDesc/' + assetdir + '/' + itemdir
            USDPath = USDPath.replace(" ", '_')
            sceneExporter.ExportScene(USDPath)
            self.populateAssetComboBox()
            self.populateItemComboBox()


    def populateShowComboBox(self, directory):
        try:
            # List all directories in the given path
            directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
            self.showDir.addItems(directories)
        except Exception as e:
            self.showDir.addItem(str(e))
            print(f"Error accessing the directory: {str(e)}")  # Print the error to console for debugging
    
    def populateAssetComboBox(self):
        self.assetDir.clear()
        showdir = self.showDir.currentText()
        directory = 'Y:/' + showdir + '/assets/SceneDesc'
        if not os.path.exists(directory):
            return
        try:
            # List all directories in the given path
            directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
            self.assetDir.addItems(directories)
        except Exception as e:
            self.assetDir.addItem(str(e))
            print(f"Error accessing the directory: {str(e)}")  # Print the error to console for debugging

    def populateItemComboBox(self):
        self.itemDir.clear()
        showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        directory = 'Y:/' + showdir + '/assets/SceneDesc/' + assetdir
        #print(directory)
        if not os.path.exists(directory):
            return
        try:
            # List all directories in the given path
            directories = [d for d in os.listdir(directory) if os.path.isfile(os.path.join(directory, d))]
            self.itemDir.addItems(directories)
            if directories:
                self.itemDir.setCurrentIndex(len(directories) - 1)
        except Exception as e:
            self.assetDir.addItem(str(e))
            print(f"Error accessing the directory: {str(e)}")  # Print the error to console for debugging

    def browseButtonLaunch(self):
        simpleUI.launch()
        self.close()

#open UI
def launch():
    if QtWidgets.QApplication.instance():
        #Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            print (win.objectName())
            if 'Import/Export Tool' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()