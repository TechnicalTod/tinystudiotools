import sys
import subprocess
import os
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QTextEdit,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, QSettings

"""
HOW TO BUILD:
-----------------------------------------------
cd L:\SagaTools\GenTools\scripts\SagaAppLauncher
python -m PyInstaller .\SagaAppLauncher.spec
Might need to hard code the drop down arrow to the local drive?
-----------------------------------------------
"""


def resourcePath(relativePath):
    """Get absolute path to resource, works for PyInstaller"""
    basePath = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(basePath, relativePath)


def setupLogging():
    """Setup logging to file for debugging"""
    logPath = os.path.join(os.path.expanduser("~"), "SagaAppLauncher_debug.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(logPath),
            logging.StreamHandler(),  # Also log to console when available
        ],
    )
    logging.info(f"Logging started. Log file: {logPath}")
    return logPath


class SagaLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resourcePath("icons/appIcon.ico")))  # Set the window icon here
        self.settings = QSettings("SagaTools", "SagaLauncher")  # Create a QSettings object
        self.initUI()

    def initUI(self):
        # Set window properties
        stylesheetPath = resourcePath("styles/dark.qss")
        with open(stylesheetPath, "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle("Saga App Launcher")

        # Create layout
        self.layout = QVBoxLayout()

        # Create the show combo box with label
        self.showLabel = QLabel("Select Show:")
        self.showComboBox = QComboBox()

        # Create the Maya version combo box with label
        self.mayaVersionLabel = QLabel("Maya Version:")
        self.mayaVersionComboBox = QComboBox()
        self.populateMayaVersions()

        # Create console window first (before populating show list)
        self.consoleLabel = QLabel("Console Output:")
        self.consoleOutput = QTextEdit()
        self.consoleOutput.setMaximumHeight(150)
        self.consoleOutput.setReadOnly(True)
        self.consoleOutput.setStyleSheet(
            "background-color: #1e1e1e; color: #ffffff; font-family: 'Courier New'; font-size: 9pt;"
        )

        # Log initial message
        self.logToConsole("Saga App Launcher started")

        # Populate combo box with directories from S:\ (after console is created)
        self.populateShowList()

        # Load the last selected show and Maya version from QSettings
        self.loadSettings()

        # Connect combo box index changes to save settings
        self.showComboBox.currentIndexChanged.connect(self.saveSettings)
        self.mayaVersionComboBox.currentIndexChanged.connect(self.saveSettings)

        # Create buttons without labels
        self.mayaButton = QPushButton()
        icon1Path = resourcePath("icons/mayaIcon.png")
        icon1 = QIcon(icon1Path)
        self.mayaButton.setIcon(icon1)
        self.mayaButton.setIconSize(QSize(120, 100))
        self.mayaButton.clicked.connect(self.openMaya)

        self.unrealButton = QPushButton()
        icon2Path = resourcePath("icons/unrealIcon.png")
        icon2 = QIcon(icon2Path)
        self.unrealButton.setIcon(icon2)
        self.unrealButton.setIconSize(QSize(120, 100))
        self.unrealButton.clicked.connect(self.openUnreal)

        self.aeButton = QPushButton()
        icon3Path = resourcePath("icons/aeIcon.png")
        icon3 = QIcon(icon3Path)
        self.aeButton.setIcon(icon3)
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

        # Set minimum width to double the current size and adjust height to content
        self.setMinimumWidth(1000)  # Double the typical width for better layout
        self.adjustSize()

    def populateShowList(self):
        """Populate the QComboBox with directories from the S:\ drive, excluding system folders."""
        drivePath = "S:\\"
        if os.path.exists(drivePath):
            try:
                directories = [
                    d
                    for d in os.listdir(drivePath)
                    if os.path.isdir(os.path.join(drivePath, d))
                    and d not in ["$RECYCLE.BIN", "System Volume Information"]
                ]
                self.showComboBox.addItems(directories)
                self.logToConsole(f"Found {len(directories)} shows in {drivePath}")
            except Exception as e:
                error_msg = f"Failed to list directories in {drivePath}: {e}"
                self.logToConsole(f"ERROR: {error_msg}")
        else:
            error_msg = f"Drive {drivePath} not found"
            self.logToConsole(f"ERROR: {error_msg}")

    def populateMayaVersions(self):
        """Populate the Maya version QComboBox with available Maya versions."""
        mayaVersions = ["Maya 2023", "Maya 2026"]
        self.mayaVersionComboBox.addItems(mayaVersions)
        # Set Maya 2023 as default
        defaultIndex = self.mayaVersionComboBox.findText("Maya 2023")
        if defaultIndex >= 0:
            self.mayaVersionComboBox.setCurrentIndex(defaultIndex)

    def addWidgets(self):
        self.layout.addWidget(self.showLabel)
        self.layout.addWidget(self.showComboBox)
        self.layout.addWidget(self.mayaVersionLabel)
        self.layout.addWidget(self.mayaVersionComboBox)
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.consoleLabel)
        self.layout.addWidget(self.consoleOutput)

    def loadSettings(self):
        """Load the last selected show and Maya version from QSettings and set them in the combo boxes."""
        lastShow = self.settings.value("lastShow", "")
        if lastShow:
            index = self.showComboBox.findText(lastShow)
            if index >= 0:
                self.showComboBox.setCurrentIndex(index)
                self.logToConsole(f"Loaded last show: {lastShow}")

        lastMayaVersion = self.settings.value("lastMayaVersion", "Maya 2023")
        if lastMayaVersion:
            index = self.mayaVersionComboBox.findText(lastMayaVersion)
            if index >= 0:
                self.mayaVersionComboBox.setCurrentIndex(index)
                self.logToConsole(f"Loaded last Maya version: {lastMayaVersion}")

    def saveSettings(self):
        """Save the currently selected show and Maya version to QSettings."""
        selectedShow = self.showComboBox.currentText()
        selectedMayaVersion = self.mayaVersionComboBox.currentText()
        self.settings.setValue("lastShow", selectedShow)
        self.settings.setValue("lastMayaVersion", selectedMayaVersion)

    def openMaya(self):
        selectedItem = self.showComboBox.currentText()
        selectedMayaVersion = self.mayaVersionComboBox.currentText()

        self.logToConsole(f"Opening Maya - Show: {selectedItem}, Version: {selectedMayaVersion}")
        logging.info(f"Opening Maya - Show: {selectedItem}, Version: {selectedMayaVersion}")

        if selectedItem and selectedMayaVersion:
            # Extract year from version string (e.g., "Maya 2023" -> "2023")
            mayaYear = selectedMayaVersion.split()[-1]

            # Use the same batch file for all Maya versions
            mayaBatchPath = resourcePath("batch_files/launchMaya.bat")

            self.logToConsole(f"Maya year extracted: {mayaYear}")
            self.logToConsole(f"Using batch file: {mayaBatchPath}")
            logging.info(f"Maya year extracted: {mayaYear}")
            logging.info(f"Using batch file: {mayaBatchPath}")

            # Check if the batch file exists
            if os.path.exists(mayaBatchPath):
                self.logToConsole(
                    f"Launching Maya {mayaYear} with: {mayaBatchPath} {selectedItem} {mayaYear}"
                )
                logging.info(
                    f"Launching Maya {mayaYear} with: {mayaBatchPath} {selectedItem} {mayaYear}"
                )
                subprocess.run([mayaBatchPath, selectedItem, mayaYear], shell=True)
            else:
                error_msg = f"Batch file not found: {mayaBatchPath}"
                self.logToConsole(f"ERROR: {error_msg}")
                logging.error(error_msg)
        else:
            error_msg = "No show or Maya version selected"
            self.logToConsole(f"WARNING: {error_msg}")
            logging.warning(error_msg)

    def openUnreal(self):
        selectedItem = self.showComboBox.currentText()
        unrealBatchPath = resourcePath("batch_files/launchUnrealProject.bat")

        self.logToConsole(f"Opening Unreal - Show: {selectedItem}")

        if selectedItem:
            self.logToConsole(f"Launching Unreal with batch: {unrealBatchPath}")
            subprocess.run([unrealBatchPath, selectedItem], shell=True)
        else:
            self.logToConsole("WARNING: No show selected for Unreal")

    def openAfterEffects(self):
        self.logToConsole("After Effects launcher not implemented yet")

    def logToConsole(self, message):
        """Add a message to the console output with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.consoleOutput.append(formatted_message)
        # Auto-scroll to bottom
        self.consoleOutput.verticalScrollBar().setValue(
            self.consoleOutput.verticalScrollBar().maximum()
        )


def main():
    logPath = setupLogging()
    logging.info("Starting Saga App Launcher")

    app = QApplication(sys.argv)
    launcher = SagaLauncher()

    logging.info(f"Debug log will be saved to: {logPath}")
    print(f"Debug log will be saved to: {logPath}")  # Show in console if available

    launcher.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
