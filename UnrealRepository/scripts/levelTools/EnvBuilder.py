import glob
import os
import re

import unreal
from PySide6 import QtWidgets

from genTools.uiUtils import (
    center_widget,
    content_path,
    list_content_subdirs,
    load_qss,
    show_unreal_tool_window,
)

GAME_ENV_BASE = "/Game/01_Assets/ENV"
CONTENT_ENV_SEGMENT = "01_Assets/ENV"
WINDOW_OBJECT_NAME = "Unreal ENV Builder"


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(500, 100)
        self.setWindowTitle("ENV Builder")
        self.setFocus()
        self.center()

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 3)

        self.envNameLabel = QtWidgets.QLabel("ENV:")
        self.envNameDropdown = QtWidgets.QComboBox()
        self.envNameDropdown.setEditable(True)
        self.updateComboBox(self.envNameDropdown, CONTENT_ENV_SEGMENT)
        self.envNameDropdown.currentIndexChanged.connect(self.updateEnvVarDropdown)

        self.envVarLabel = QtWidgets.QLabel("Variant:")
        self.envVarDropdown = QtWidgets.QComboBox()
        self.envVarDropdown.setEditable(True)
        self.updateEnvVarDropdown()

        self.createEnvButton = QtWidgets.QPushButton("Create ENV")
        self.createEnvButton.clicked.connect(self.createENV)

        self.grid.addWidget(self.envNameLabel, 0, 0)
        self.grid.addWidget(self.envNameDropdown, 0, 1)
        self.grid.addWidget(self.envVarLabel, 1, 0)
        self.grid.addWidget(self.envVarDropdown, 1, 1)
        self.grid.addWidget(self.createEnvButton, 2, 0, 1, 2)

        self.setLayout(self.grid)

    def updateComboBox(self, comboBox, *content_segments):
        comboBox.blockSignals(True)
        comboBox.clear()
        comboBox.addItems(list_content_subdirs(*content_segments))
        comboBox.blockSignals(False)

    def updateEnvVarDropdown(self):
        env_name = self.envNameDropdown.currentText()
        if not env_name:
            self.envVarDropdown.clear()
            return

        self.updateComboBox(self.envVarDropdown, CONTENT_ENV_SEGMENT, env_name)

    def _get_version_number(self, save_dir):
        version_numbers = []
        for file_path in glob.glob(os.path.join(save_dir, "v[0-9][0-9][0-9]")):
            match = re.search(r"v(\d{3})$", os.path.basename(file_path))
            if match:
                try:
                    version_numbers.append(int(match.group(1)))
                except ValueError:
                    print(
                        "Input file path not correctly versioned, must follow v001 with 3 numbers"
                    )

        if not version_numbers:
            latest_version = 1
            new_version = 1
        else:
            latest_version = max(version_numbers)
            new_version = latest_version + 1

        return f"v{latest_version:03d}", f"v{new_version:03d}"

    def _ensure_directory(self, dir_path):
        if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
            unreal.EditorAssetLibrary.make_directory(dir_path)

    def _create_level_if_missing(self, level_asset_path):
        if unreal.EditorAssetLibrary.does_asset_exist(level_asset_path + ".umap"):
            return

        level_library = unreal.EditorLevelLibrary()
        if level_library.new_level(level_asset_path):
            print(f"New level created: {level_asset_path}.umap")
        else:
            print(f"Failed to create new level: {level_asset_path}")

    def createENV(self):
        env_name = self.envNameDropdown.currentText()
        var_name = self.envVarDropdown.currentText()

        if not all([env_name, var_name]):
            print("Please make sure all selections are made.")
            return

        save_dir = content_path(CONTENT_ENV_SEGMENT, env_name, var_name)
        _, new_ver = self._get_version_number(save_dir)
        dir_path = f"{GAME_ENV_BASE}/{env_name}/{var_name}/{new_ver}"

        self._ensure_directory(dir_path)
        self._ensure_directory(f"{dir_path}/SL")

        lit_name = f"LIT_{env_name}_{var_name}_{new_ver}"
        pl_name = f"PL_{env_name}_{var_name}_{new_ver}"

        self._create_level_if_missing(f"{dir_path}/SL/{lit_name}")
        self._create_level_if_missing(f"{dir_path}/{pl_name}")

        print(f"Folder structure and assets created under: {dir_path}")

    def center(self):
        center_widget(self)


def show():
    show_unreal_tool_window(MainWindow, WINDOW_OBJECT_NAME)


openWindow = show
