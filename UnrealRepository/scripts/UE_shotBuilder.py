import unreal
import os
import sys
from PySide2 import QtGui, QtWidgets, QtCore

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
        self.setWindowTitle('Shot Builder')
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
        self.shotNameLabel = QtWidgets.QLabel("Shot Name:")
        self.shotNameDropdown = QtWidgets.QComboBox()
        self.updateComboBox(self.shotNameDropdown, self.getUnrealDir('02_Episodes'))
        self.shotNameDropdown.currentIndexChanged.connect(lambda: self.updateShotNumberDropdown())
        self.shotNameDropdown.setEditable(True)
        self.shotNameDropdown.editTextChanged.connect(lambda: self.updateShotNumberDropdown())

        # Label and Dropdown for 'Shot Number'
        self.shotNumberLabel = QtWidgets.QLabel("Shot Number:")
        self.shotNumberDropdown = QtWidgets.QComboBox()
        self.updateShotNumberDropdown()
        self.shotNumberDropdown.currentIndexChanged.connect(lambda: self.updateShotVersionDropdown())
        self.shotNumberDropdown.setEditable(True)
        self.shotNumberDropdown.editTextChanged.connect(lambda: self.updateShotVersionDropdown())

        # Label and Dropdown for 'Shot Version'
        self.shotVersionLabel = QtWidgets.QLabel("Shot Version:")
        self.shotVersionDropdown = QtWidgets.QComboBox()
        self.updateShotVersionDropdown()
        self.shotVersionDropdown.setEditable(True)

        # Button 'Create Shot Folders'
        self.createShotFoldersButton = QtWidgets.QPushButton("Create Shot Folders")
        self.createShotFoldersButton.clicked.connect(self.createShotFolders)

        # Adding widgets to the layout
        self.grid.addWidget(self.shotNameLabel, 0, 0)
        self.grid.addWidget(self.shotNameDropdown, 0, 1)
        self.grid.addWidget(self.shotNumberLabel, 1, 0)
        self.grid.addWidget(self.shotNumberDropdown, 1, 1)
        self.grid.addWidget(self.shotVersionLabel, 2, 0)
        self.grid.addWidget(self.shotVersionDropdown, 2, 1)
        self.grid.addWidget(self.createShotFoldersButton, 3, 0, 1, 2)  # Span 2 columns

        self.setLayout(self.grid)

    def getUnrealDir(self, specific_path):
        content_directory = unreal.Paths.project_content_dir()
        return os.path.join(content_directory, specific_path.replace("/", os.sep))

    def updateComboBox(self, comboBox, path):
        comboBox.clear()
        if os.path.exists(path):
            existing_files = os.listdir(path)
            comboBox.addItems(sorted(existing_files))

    def updateShotNumberDropdown(self):
        selected_shot_name = self.shotNameDropdown.currentText()
        self.updateComboBox(self.shotNumberDropdown, self.getUnrealDir(f'02_Episodes/{selected_shot_name}'))

    def updateShotVersionDropdown(self):
        selected_shot_name = self.shotNameDropdown.currentText()
        selected_shot_number = self.shotNumberDropdown.currentText()
        self.updateComboBox(self.shotVersionDropdown, self.getUnrealDir(f'02_Episodes/{selected_shot_name}/{selected_shot_number}'))

    def createShotFolders(self):
        # Ensure selections are not empty
        selected_shot_name = self.shotNameDropdown.currentText()
        selected_shot_number = self.shotNumberDropdown.currentText()
        selected_version = self.shotVersionDropdown.currentText()

        if not all([selected_shot_name, selected_shot_number, selected_version]):
            print("Please make sure all selections are made.")
            return

        # Constructing the directory and asset paths in Unreal's format
        base_path = "/Game/02_Episodes"
        dir_path = f"{base_path}/{selected_shot_name}/{selected_shot_number}/{selected_version}"

        # Create the directory if it doesn't exist
        if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
            unreal.EditorAssetLibrary.make_directory(dir_path)
        
        # Create the "Animation" folder within the same directory
        animation_folder_path = f"{dir_path}/Animation"
        if not unreal.EditorAssetLibrary.does_directory_exist(animation_folder_path):
            unreal.EditorAssetLibrary.make_directory(animation_folder_path)

        # Construct asset names
        level_name = f"PL_{selected_shot_name}_{selected_shot_number}_{selected_version}"
        sequence_name = f"LS_{selected_shot_name}_{selected_shot_number}_{selected_version}"

        # Create a new level
        level_asset_path = f"{dir_path}/{level_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(level_asset_path + ".umap"):
            levelLibrary = unreal.EditorLevelLibrary()
            success = levelLibrary.new_level(level_asset_path)
            if success:
                print(f"New level created: {level_asset_path}.umap")
            else:
                print("Failed to create new level.")

        # Creating a level sequence asset
        sequence_asset_path = f"{dir_path}/{sequence_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(sequence_asset_path + ".uasset"):
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            factory = unreal.LevelSequenceFactoryNew()
            sequence_asset = asset_tools.create_asset(sequence_name, dir_path, None, factory)
            if sequence_asset:
                print(f"Level Sequence created: {sequence_asset_path}.uasset")
            else:
                print("Failed to create Level Sequence.")

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
            if 'Unreal Shot Builder' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())

#openWindow()