import unreal
from PySide6 import QtGui, QtWidgets

from genTools.uiUtils import center_widget, load_qss, show_unreal_tool_window
import unrealFilePaths

import assetTools.USDExporter as USDExporter

WINDOW_OBJECT_NAME = "Unreal USD Asset Exporter"


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setObjectName(WINDOW_OBJECT_NAME)
        # window prefs
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(400, 50)
        self.setWindowTitle("Bulk Export Assets to USD")
        self.setFocus()
        self.center()
        self.show()

        # Create a combo box and populate it with files from the directory
        self.exportDirLabel = QtWidgets.QLabel("Export Directory:")
        self.exportDir = QtWidgets.QLineEdit(self)

        # button widget
        self.exportUSDButton = QtWidgets.QPushButton("Export Selected", self)
        self.exportUSDButton.clicked.connect(self.exportUSD)

        # button widget
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(
            QtGui.QIcon("{}/folder.png".format(unrealFilePaths.unrealIconPath))
        )
        self.browseButton.clicked.connect(self.browseButtonLaunch)

        # Initialize the grid layout with spacing
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # Set size policies for buttons
        self.exportUSDButton.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        self.browseButton.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred
        )

        # Add widgets to layout with consistent spanning
        self.grid.addWidget(self.exportDirLabel, 1, 0)
        self.grid.addWidget(self.exportDir, 1, 1, 1, 3)  # Span across all remaining columns
        self.grid.addWidget(self.browseButton, 1, 4)  # Single column on the right end

        self.grid.addWidget(self.exportUSDButton, 2, 0, 1, 5)  # Span across all columns

        # Set the overall layout
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        center_widget(self)

    # definition called when export button is pressed
    def exportUSD(self):
        exportDir = self.exportDir.text()
        USDExporter.exportSelectedAssets(exportDir)
        print(f"Exporting to directory: {exportDir}")

    def browseButtonLaunch(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if directory:
            self.exportDir.setText(directory)


def openWindow():
    show_unreal_tool_window(MainWindow, WINDOW_OBJECT_NAME)
