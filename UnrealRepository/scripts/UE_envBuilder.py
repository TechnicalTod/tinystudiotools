import unreal
import os
import sys
from PySide2 import QtGui, QtWidgets, QtCore

import glob
import re

from importlib import reload
import unrealFilePaths
reload(unrealFilePaths)

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        with open("{}/dark.qss".format(unrealFilePaths.UNREAL_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(500, 100)
        self.setWindowTitle('ENV Builder')
        self.setFocus()
        self.center()
        self.show()

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)
        self.grid = QtWidgets.QGridLayout()

        # Adjust column stretch factors
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 3)

        self.project_name = unreal.SystemLibrary.get_game_name()

        # Label and Dropdown for 'Shot Name'
        self.envNameLabel = QtWidgets.QLabel("location:")
        self.envNameDropdown = QtWidgets.QComboBox()
        self.updateComboBox(self.envNameDropdown, f'Y:/{self.project_name}/assets/locations')
        self.envNameDropdown.setEditable(True)
        self.envNameDropdown.currentIndexChanged.connect(lambda: self.updateEnvVarDropdown())

        self.envVarLabel = QtWidgets.QLabel("Variant:")
        self.envVarDropdown = QtWidgets.QComboBox()
        self.updateComboBox(self.envVarDropdown, f'Y:/{self.project_name}/assets/locations/{self.envNameDropdown.currentText()}/publish/unreal/layoutSceneDescription')
        self.envVarDropdown.setEditable(True)

        # Button 'Create Shot Folders'
        self.createShotFoldersButton = QtWidgets.QPushButton("Create locations Folder")
        self.createShotFoldersButton.clicked.connect(self.createENV)
        
        # Adding widgets to the layout
        self.grid.addWidget(self.envNameLabel, 0, 0)
        self.grid.addWidget(self.envNameDropdown, 0, 1)
        self.grid.addWidget(self.envVarLabel, 1, 0)
        self.grid.addWidget(self.envVarDropdown, 1, 1)
        #self.grid.addWidget(self.shotVersionLabel, 2, 0)
        #self.grid.addWidget(self.shotVersionDropdown, 2, 1)
        self.grid.addWidget(self.createShotFoldersButton, 2, 0, 1, 2)  # Span 2 columns

        self.setLayout(self.grid)

    def updateComboBox(self, comboBox, path):
        print(path)
        comboBox.clear()
        if os.path.exists(path):
            existing_files = os.listdir(path)
            comboBox.addItems(sorted(existing_files))

    def updateEnvVarDropdown(self):
        self.updateComboBox(self.envVarDropdown, f'Y:/{self.project_name}/assets/locations/{self.envNameDropdown.currentText()}/publish/unreal/layoutSceneDescription')

    def GetVersionNumber(self, saveDir):
        versionNumList = []
        # Adjust the glob pattern to match files with the version format
        getAllMatching = glob.glob(os.path.join(saveDir, 'v[0-9][0-9][0-9]'), recursive=True)
        
        print(f"Debug: Matching files in {saveDir} -> {getAllMatching}")

        for filePath in getAllMatching:
            baseName = os.path.basename(filePath)
            print(f"Debug: Processing file -> {baseName}")
            match = re.search(r'v(\d{3})$', baseName)
            
            if match:
                versionNumber = match.group(1)
                print(f"Debug: Found version number -> {versionNumber}")
                try:
                    num = int(versionNumber)
                    versionNumList.append(num)
                except ValueError:
                    print("Input file path not correctly versioned, must follow v001 with 3 numbers")
        
        if len(versionNumList) == 0:
            latestVersion = 1
            newVersion = 1
        else:
            latestVersion = max(versionNumList)
            newVersion = latestVersion + 1
        
        # Format the version numbers
        latestVersionStr = f'v{latestVersion:03d}'
        newVersionStr = f'v{newVersion:03d}'
        
        return latestVersionStr, newVersionStr

    def createENV(self):
        path = unreal.Paths.get_project_file_path()
        path = path.replace('\\', '/')
        path = path.rsplit('/', 1)[0]        
        env_name = self.envNameDropdown.currentText()
        var_name = self.envVarDropdown.currentText()

        saveDir = path + f'/Content/01_Assets/locations/{env_name}/{var_name}/'
        currentVer, newVer = self.GetVersionNumber(saveDir)

        if not all([env_name, var_name]):
            print("Please make sure all selections are made.")
            return

        # Constructing the directory and asset paths in Unreal's format
        base_path = "/Game/01_Assets/locations"
        dir_path = f"{base_path}/{env_name}/{var_name}/{newVer}"

        # Create the directory if it doesn't exist
        if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
            unreal.EditorAssetLibrary.make_directory(dir_path)
        
        # Create the "Animation" folder within the same directory
        subLevel_folder_path = f"{dir_path}/SL"
        if not unreal.EditorAssetLibrary.does_directory_exist(subLevel_folder_path):
            unreal.EditorAssetLibrary.make_directory(subLevel_folder_path)

         # Construct asset names
        LT_name = f"LT_{env_name}_{var_name}_{newVer}"

        # Create a new level
        LT_asset_path = f"{dir_path}/SL/{LT_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(LT_asset_path + ".umap"):
            levelLibrary = unreal.EditorLevelLibrary()
            success = levelLibrary.new_level(LT_asset_path)
            if success:
                print(f"New level created: {LT_asset_path}.umap")
            else:
                print("Failed to create new level.")

        # Construct asset names
        level_name = f"PL_{env_name}_{var_name}_{newVer}"

        # Create a new level
        level_asset_path = f"{dir_path}/{level_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(level_asset_path + ".umap"):
            levelLibrary = unreal.EditorLevelLibrary()
            success = levelLibrary.new_level(level_asset_path)
            if success:
                print(f"New level created: {level_asset_path}.umap")
            else:
                print("Failed to create new level.")

        print(f"Folder structure and assets created under: {dir_path}")
        
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

def openWindow():
    if QtWidgets.QApplication.instance():
        for win in QtWidgets.QApplication.allWindows():
            print(win.objectName())
            if 'Unreal Env Level Builder' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())