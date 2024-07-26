import os
import unreal
import sys
import subprocess
from PySide2 import QtGui, QtWidgets, QtCore

import re
from importlib import reload
import unrealFilePaths
reload(unrealFilePaths)

import UE_USDSceneBuilder as usd_builder
import UE_USDSceneExporter as usd_exporter

import ImportExportUSDUI as simpleUI

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.UNREAL_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(400, 50)
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
        self.assetDir.currentIndexChanged.connect(lambda: self.populateVarComboBox())
        self.assetDir.editTextChanged.connect(lambda: self.populateVarComboBox())

        # Create a combo box and populate it with files from the directory
        self.varDirLabel = QtWidgets.QLabel("Varient Name:")
        self.varDir = QtWidgets.QComboBox(self)
        self.populateVarComboBox()
        self.varDir.setEditable(True)
        self.varDir.currentIndexChanged.connect(lambda: self.populateVerComboBoxes())
        self.varDir.editTextChanged.connect(lambda: self.populateVerComboBoxes())
        
        # Create a combo box and populate it with files from the directory
        self.USDNameLabel = QtWidgets.QLabel("USD Name:")
        self.USDName = QtWidgets.QLabel("")
        #self.itemDir.setEditable(True)

        # Create a combo box and populate it with files from the directory
        self.importVerLabel = QtWidgets.QLabel("Current Version:")
        self.importVer = QtWidgets.QComboBox(self)
        #self.populateVerComboBoxes()
        #self.importVer.setEditable(True)
        self.importVer.currentIndexChanged.connect(lambda: self.populateUSDName())
        self.importVer.editTextChanged.connect(lambda: self.populateUSDName())

        # Create a label for displaying the next version
        self.exportVerLabel = QtWidgets.QLabel("Next Version:")
        self.exportVerNum = QtWidgets.QLabel("")  # Correctly initialize the QLabel
        self.populateVerComboBoxes()

        self.populateUSDName()

        # button widget
        self.importUSDButton = QtWidgets.QPushButton('Import USD', self)
        self.importUSDButton.clicked.connect(self.importUSD)

        # button widget
        self.exportUSDButton = QtWidgets.QPushButton('Export USD', self)
        self.exportUSDButton.clicked.connect(self.exportUSD)
        
        # button widget
        openFolderIconFilepath = unrealFilePaths.UNREAL_openFolderIconFilepath
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

        self.grid.addWidget(self.varDirLabel, 3, 0)
        self.grid.addWidget(self.varDir, 3, 1, 1, -1)

        self.grid.addWidget(self.importVerLabel, 4, 0)
        self.grid.addWidget(self.importVer, 4, 1)
        self.grid.addWidget(self.exportVerLabel, 4, 2)
        self.grid.addWidget(self.exportVerNum, 4, 3)

        self.grid.addWidget(self.USDNameLabel, 5, 0)
        self.grid.addWidget(self.USDName, 5, 1, 1, -1)  # Consistent span

        # Adding buttons with adjusted spans to fill space appropriately
        self.grid.addWidget(self.importUSDButton, 6, 0, 1, 2)  # Spans two columns, adjusted for more space
        self.grid.addWidget(self.exportUSDButton, 6, 2, 1, 2)  # Spans two columns, adjusted for equal size
        self.grid.addWidget(self.browseButton, 6, 4)  # Single column on the right end

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
        vardir = self.varDir.currentText()
        itemver = self.importVer.currentText()
        itemdir = self.USDName.text()
        USDPath = 'Y:/' + showdir + '/assets/ENV/' + assetdir + '/publish/unreal/layoutSceneDescription/' + vardir + '/' + itemver + '/' + itemdir
        USDPath = USDPath.replace(" ", '_')
        usd_builder.BuildScene(USDPath)

    # definition called when export button is pressed
    def exportUSD(self):
        showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        vardir = self.varDir.currentText()
        itemver = self.exportVerNum.text()     
        itemdir = self.USDName.text()
        itemdir = itemdir[:-9]
        itemdir += itemver + '.usda'
        if showdir != '' and assetdir != '':
            coredir = USDPath = 'Y:/' + showdir + '/assets/ENV/' + assetdir + '/publish/unreal/layoutSceneDescription/' + vardir + '/' + itemver
            coredir = coredir.replace(" ", '_')
            if not os.path.exists(coredir):
                os.makedirs(coredir)
            USDPath = 'Y:/' + showdir + '/assets/ENV/' + assetdir + '/publish/unreal/layoutSceneDescription/' + vardir + '/' + itemver + '/' + itemdir
            USDPath = USDPath.replace(" ", '_')
            usd_exporter.ExportScene(USDPath)
            self.populateAssetComboBox()
            self.populateVarComboBox()
            self.populateVerComboBoxes()
            self.populateUSDName()

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
        directory = 'Y:/' + showdir + '/assets/ENV'
        if not os.path.exists(directory):
            return
        try:
            # List all directories in the given path
            directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
            self.assetDir.addItems(directories)
        except Exception as e:
            self.assetDir.addItem(str(e))
            print(f"Error accessing the directory: {str(e)}")  # Print the error to console for debugging

    def populateVarComboBox(self):
        self.varDir.clear()
        showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        directory = 'Y:/' + showdir + '/assets/ENV/' + assetdir + '/publish/unreal/layoutSceneDescription/'
        if not os.path.exists(directory):
            return
        try:
            # List all directories in the given path
            directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
            self.varDir.addItems(directories)
        except Exception as e:
            self.varDir.addItem(str(e))
            print(f"Error accessing the directory: {str(e)}")  # Print the error to console for debugging

    def populateVerComboBoxes(self):
        self.importVer.clear()
        showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        vardir = self.varDir.currentText()
        directory = f'Y:/{showdir}/assets/ENV/{assetdir}/publish/unreal/layoutSceneDescription/{vardir}'
       
        if not os.path.exists(directory):
            self.importVer.addItem('v001')  # Add v001 as default if directory does not exist
            self.exportVerNum.setText('v001')  # Update QLabel for next version
            return

        versionNumList = []
        try:
            # List all directories in the given path
            directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
            for d in directories:
                match = re.search(r'v(\d{3})$', d)
                if match:
                    versionNumber = match.group(1)
                    try:
                        num = int(versionNumber)
                        versionNumList.append(num)
                    except ValueError:
                        print("Directory name not correctly versioned, must follow v001 with 3 numbers")
           
            if len(versionNumList) == 0:
                self.importVer.addItem('None')  # Add v001 as default if no versioned directories are found
                self.exportVerNum.setText("v001")  # Update QLabel for next version
            else:
                # Populate the combo box with existing versions
                for num in sorted(versionNumList):
                    self.importVer.addItem(f'v{num:03d}')
                
                self.importVer.setCurrentIndex(self.importVer.count() - 1)

                # Determine the next version
                nextVersion = max(versionNumList) + 1
                nextVersion = f'v{nextVersion:03d}'
                self.exportVerNum.setText(nextVersion)  # Update QLabel with the next version
        except Exception as e:
            self.importVer.addItem(str(e))
            self.exportVerNum.setText("")  # Update QLabel if there's an error
            print(f"Error accessing the directory: {str(e)}")  # Print the error to console for debugging
    
    def populateUSDName(self):
        #showdir = self.showDir.currentText()
        assetdir = self.assetDir.currentText()
        vardir = self.varDir.currentText()
        itemver = self.importVer.currentText()
        if not vardir == '':
            self.USDName.setText(f'{assetdir}_{vardir}_{itemver}.usda')


    def browseButtonLaunch(self):
        simpleUI.openWindow()
        self.close()

#open UI
def openWindow():
    if QtWidgets.QApplication.instance():
        #Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            print (win.objectName())
            if 'Import Unreal Assets' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())