import sys
import subprocess
import os
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox
from PySide2.QtGui import QIcon
from PySide2.QtCore import QSize

def resourcePath(relativePath):
    """Get absolute path to resource, works for PyInstaller"""
    basePath = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(basePath, relativePath)

class SagaLauncher(QWidget):
    def __init__(self):
        super().__init__()
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

        # Create a horizontal layout for the buttons
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.mayaButton)
        self.buttonLayout.addWidget(self.unrealButton)

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

def main():
    app = QApplication(sys.argv)
    launcher = SagaLauncher()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
