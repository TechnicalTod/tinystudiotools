import json
import os
import unreal
import sys
import subprocess
from PySide2 import QtGui, QtWidgets, QtCore

from importlib import reload
import unrealFilePaths
reload(unrealFilePaths)
import genTools.genUnrealImportUtils as genUnrealImportUtils
reload(genUnrealImportUtils)

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.UNREAL_styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(1100, 50)
        self.setWindowTitle('Import All levels into Current')
        self.setFocus()
        self.center()
        self.show()

        # Current level text field widget
        self.currentLevelPath = QtWidgets.QLineEdit(self)
        self.currentLevelPath.setPlaceholderText("Current Level")

        # Source level text field widget
        self.sourceLevelPath = QtWidgets.QLineEdit(self)
        self.sourceLevelPath.setPlaceholderText("Source Level")

        # button widget
        self.currentLevelButton = QtWidgets.QPushButton('Set Current Level', self)
        self.currentLevelButton.clicked.connect(self.getCurrentLevelPath)

        # button widget
        self.sourceLevelButton = QtWidgets.QPushButton('Set Source Level', self)
        self.sourceLevelButton.clicked.connect(self.getSelectedLevelPath)

        # button widget
        self.importLevelsButton = QtWidgets.QPushButton('Import Levels', self)
        self.importLevelsButton.clicked.connect(self.importAllLevelsToCurrent)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.currentLevelPath, 0, 0, 1, 2)
        self.grid.addWidget(self.sourceLevelPath, 0, 2, 1, 2)
        self.grid.addWidget(self.currentLevelButton, 1, 0, 1, 2)
        self.grid.addWidget(self.sourceLevelButton, 1, 2, 1, 2)
        self.grid.addWidget(self.importLevelsButton, 2, 0, 1, 4)
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def getCurrentLevelPath(self):
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        self.currentLevelPath.setText(str(world.get_path_name().split(".")[0]))

    def getSelectedLevelPath(self):
        selectedAsset = unreal.EditorUtilityLibrary.get_selected_asset_data()
        self.sourceLevelPath.setText(str(selectedAsset[0].get_asset().get_path_name().split(".")[0]))

    #Import all levels into current
    #This works independant of the open level and runs on the currently saved version
    def importAllLevelsToCurrent(self):
        currentLevelSeq = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
        currentLevel = self.currentLevelPath.text()
        sourceLevel = self.sourceLevelPath.text()

        for levelPath in (currentLevel, sourceLevel):
            levelPathExists = unreal.EditorAssetLibrary.does_asset_exist(levelPath)
            if not levelPathExists:
                print("Level {} does not exist".format(levelPath))
                break
        else:
            #Open the source level to grab the list of levels required for import
            #this builds a dictionary and grabs the visibility status of each
            unreal.EditorLoadingAndSavingUtils.load_map(sourceLevel)
            world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            subLevelList = unreal.EditorLevelUtils.get_levels(world)

            SubLevelPathDict = {}

            for subLevel in subLevelList:
                subLevelPackageName = subLevel.get_package().get_name()
                streamingLevel = unreal.GameplayStatics.get_streaming_level(world, subLevelPackageName)
                SubLevelPathDict[subLevel.get_path_name()] = {}
                if streamingLevel:
                    SubLevelPathDict[subLevel.get_path_name()] = streamingLevel.is_level_visible()
                    isLevelLoaded = streamingLevel.is_level_loaded()
                    print (isLevelLoaded)
                else:
                    SubLevelPathDict[subLevel.get_path_name()] = True

            #open current shot and import the levels based on the provided dictionary
            unreal.EditorLoadingAndSavingUtils.load_map(currentLevel)
            world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

            for subLevel in SubLevelPathDict:
                subLevelVisibility = SubLevelPathDict.get(subLevel)
                newSubLevel = unreal.EditorLevelUtils.add_level_to_world(world, subLevel, unreal.LevelStreamingAlwaysLoaded)
                unreal.EditorLevelUtils.set_level_visibility(newSubLevel.get_loaded_level(), subLevelVisibility, True)

            #Open the previously open level sequence again
            if currentLevelSeq:
                unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(currentLevelSeq)
            else:
                print ("No Level Sequence is currently open.")
            #Commenting this out for now as Im not sure we want to save these changes by default
            #unreal.EditorLevelLibrary.save_current_level()

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