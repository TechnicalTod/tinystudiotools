import unreal
from PySide6 import QtWidgets

from genTools.uiUtils import (
    center_widget,
    list_content_subdirs,
    load_qss,
    show_unreal_tool_window,
)

GAME_EPISODES_BASE = "/Game/02_Episodes"
CONTENT_EPISODES_SEGMENT = "02_Episodes"
WINDOW_OBJECT_NAME = "Unreal Shot Builder"


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(500, 100)
        self.setWindowTitle("Shot Builder")
        self.setFocus()
        self.center()
        self.show()

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 3)

        self.shotNameLabel = QtWidgets.QLabel("Shot Name:")
        self.shotNameDropdown = QtWidgets.QComboBox()
        self.shotNameDropdown.setEditable(True)
        self.updateComboBox(self.shotNameDropdown, CONTENT_EPISODES_SEGMENT)
        self.shotNameDropdown.currentIndexChanged.connect(self.updateShotNumberDropdown)
        self.shotNameDropdown.editTextChanged.connect(self.updateShotNumberDropdown)

        self.shotNumberLabel = QtWidgets.QLabel("Shot Number:")
        self.shotNumberDropdown = QtWidgets.QComboBox()
        self.shotNumberDropdown.setEditable(True)
        self.updateShotNumberDropdown()
        self.shotNumberDropdown.currentIndexChanged.connect(self.updateShotVersionDropdown)
        self.shotNumberDropdown.editTextChanged.connect(self.updateShotVersionDropdown)

        self.shotVersionLabel = QtWidgets.QLabel("Shot Version:")
        self.shotVersionDropdown = QtWidgets.QComboBox()
        self.shotVersionDropdown.setEditable(True)
        self.updateShotVersionDropdown()

        self.createShotFoldersButton = QtWidgets.QPushButton("Create Shot Folders")
        self.createShotFoldersButton.clicked.connect(self.createShotFolders)

        self.grid.addWidget(self.shotNameLabel, 0, 0)
        self.grid.addWidget(self.shotNameDropdown, 0, 1)
        self.grid.addWidget(self.shotNumberLabel, 1, 0)
        self.grid.addWidget(self.shotNumberDropdown, 1, 1)
        self.grid.addWidget(self.shotVersionLabel, 2, 0)
        self.grid.addWidget(self.shotVersionDropdown, 2, 1)
        self.grid.addWidget(self.createShotFoldersButton, 3, 0, 1, 2)

        self.setLayout(self.grid)

    def updateComboBox(self, comboBox, *content_segments):
        comboBox.blockSignals(True)
        comboBox.clear()
        comboBox.addItems(list_content_subdirs(*content_segments))
        comboBox.blockSignals(False)

    def updateShotNumberDropdown(self):
        shot_name = self.shotNameDropdown.currentText()
        if not shot_name:
            self.shotNumberDropdown.clear()
            return

        self.updateComboBox(self.shotNumberDropdown, CONTENT_EPISODES_SEGMENT, shot_name)

    def updateShotVersionDropdown(self):
        shot_name = self.shotNameDropdown.currentText()
        shot_number = self.shotNumberDropdown.currentText()
        if not all([shot_name, shot_number]):
            self.shotVersionDropdown.clear()
            return

        self.updateComboBox(
            self.shotVersionDropdown,
            CONTENT_EPISODES_SEGMENT,
            shot_name,
            shot_number,
        )

    def createShotFolders(self):
        selected_shot_name = self.shotNameDropdown.currentText()
        selected_shot_number = self.shotNumberDropdown.currentText()
        selected_version = self.shotVersionDropdown.currentText()

        if not all([selected_shot_name, selected_shot_number, selected_version]):
            print("Please make sure all selections are made.")
            return

        dir_path = (
            f"{GAME_EPISODES_BASE}/{selected_shot_name}/"
            f"{selected_shot_number}/{selected_version}"
        )

        if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
            unreal.EditorAssetLibrary.make_directory(dir_path)

        animation_folder_path = f"{dir_path}/Animation"
        if not unreal.EditorAssetLibrary.does_directory_exist(animation_folder_path):
            unreal.EditorAssetLibrary.make_directory(animation_folder_path)

        level_name = f"PL_{selected_shot_name}_{selected_shot_number}_{selected_version}"
        sequence_name = f"LS_{selected_shot_name}_{selected_shot_number}_{selected_version}"

        level_asset_path = f"{dir_path}/{level_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(level_asset_path + ".umap"):
            level_library = unreal.EditorLevelLibrary()
            if level_library.new_level(level_asset_path):
                print(f"New level created: {level_asset_path}.umap")
            else:
                print("Failed to create new level.")

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
        center_widget(self)


def openWindow():
    show_unreal_tool_window(MainWindow, WINDOW_OBJECT_NAME)
