import sys
import subprocess
import os
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox
from PySide2.QtGui import QIcon
from PySide2.QtCore import QSize, QSettings

'''
HOW TO BUILD:
-----------------------------------------------
cd L:\SagaTools\GenTools\scripts\SagaAppLauncher
python -m PyInstaller .\SagaAppLauncher.spec
-----------------------------------------------
'''

def resourcePath(relativePath):
    """Get absolute path to resource, works for PyInstaller"""
    basePath = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(basePath, relativePath)

class SagaLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resourcePath('icons/appIcon.ico')))  # Set the window icon here
        self.settings = QSettings("SagaTools", "SagaLauncher")  # Create a QSettings object
        self.initUI()

    def initUI(self):
        # Set window properties
        stylesheetPath = resourcePath('styles/dark.qss')
        with open(stylesheetPath, "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle('Saga App Launcher')

        # Create layout
        self.layout = QVBoxLayout()

        # Create the combo box
        self.showComboBox = QComboBox()

        # Populate combo box with directories from S:\
        self.populateShowList()

        # Load the last selected show from QSettings
        self.loadSettings()

        # Connect combo box index change to save settings
        self.showComboBox.currentIndexChanged.connect(self.saveSettings)

        # Create buttons without labels
        self.mayaButton = QPushButton()
        icon1Path = resourcePath('icons/mayaIcon.png')
        icon1 = QIcon(icon1Path)
        self.mayaButton.setIcon(icon1)
        self.mayaButton.setIconSize(QSize(120, 100))
        self.mayaButton.clicked.connect(self.openMaya)

        self.unrealButton = QPushButton()
        icon2Path = resourcePath('icons/unrealIcon.png')
        icon2 = QIcon(icon2Path)
        self.unrealButton.setIcon(icon2)
        self.unrealButton.setIconSize(QSize(120, 100))
        self.unrealButton.clicked.connect(self.openUnreal)

        self.aeButton = QPushButton()
        icon3Path = resourcePath('icons/aeIcon.png')
        icon2 = QIcon(icon3Path)
        self.aeButton.setIcon(icon2)
        self.aeButton.setIconSize(QSize(120, 100))
        self.aeButton.clicked.connect(self.openAfterEffects)

        # Create a horizontal layout for the buttons
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.mayaButton)
        self.buttonLayout.addWidget(self.unrealButton)
        self.buttonLayout.addWidget(self.aeButton)

        # Add widgets to layout via a function
        self.addWidgets()

        # Set layout
        self.setLayout(self.layout)

        # Adjust window size to content
        self.adjustSize()

    def populateShowList(self):
        """Populate the QComboBox with directories from the S:\ drive, excluding system folders."""
        drivePath = 'S:\\'
        if os.path.exists(drivePath):
            try:
                directories = [
                    d for d in os.listdir(drivePath)
                    if os.path.isdir(os.path.join(drivePath, d)) and d not in ['$RECYCLE.BIN', 'System Volume Information']
                ]
                self.showComboBox.addItems(directories)
            except Exception as e:
                print(f"Failed to list directories in {drivePath}: {e}")
        else:
            print(f"Drive {drivePath} not found")

    def addWidgets(self):
        self.layout.addWidget(self.showComboBox)
        self.layout.addLayout(self.buttonLayout)

    def loadSettings(self):
        """Load the last selected show from QSettings and set it in the combo box."""
        lastShow = self.settings.value("lastShow", "")
        if lastShow:
            index = self.showComboBox.findText(lastShow)  # Find the index of the saved show
            if index >= 0:
                self.showComboBox.setCurrentIndex(index)

    def saveSettings(self):
        """Save the currently selected show to QSettings."""
        selectedShow = self.showComboBox.currentText()
        self.settings.setValue("lastShow", selectedShow)

    def openMaya(self):
        selectedItem = self.showComboBox.currentText()
        mayaBatchPath = resourcePath('batch_files/launchMaya2023.bat')
        if selectedItem:
            subprocess.run([mayaBatchPath, selectedItem], shell=True)
        else:
            print("No selection made")

    def openUnreal(self):
        selectedItem = self.showComboBox.currentText()
        unrealBatchPath = resourcePath('batch_files/launchUnrealProject.bat')
        if selectedItem:
            subprocess.run([unrealBatchPath, selectedItem], shell=True)
        else:
            print("No selection made")

    def openAfterEffects(self):
        print("No selection made")

def main():
    app = QApplication(sys.argv)
    launcher = SagaLauncher()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
