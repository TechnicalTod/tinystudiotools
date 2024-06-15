import os
import subprocess
from genTools.genUtils import warningPopup
from PySide2 import QtGui, QtWidgets, QtCore

from importlib import reload
import filePaths
reload(filePaths)

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        self.style_sheet_file_loc = filePaths.styleSheetFilepath
        with open(self.style_sheet_file_loc, "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(600, 50)
        self.setWindowTitle('Convert textures to PNG')
        self.setFocus()
        self.center()
        self.show()

        # text field widget
        self.getFilePath = QtWidgets.QLineEdit(self)
        self.getFilePath.setPlaceholderText("File path")

        # button widget
        self.convertButton = QtWidgets.QPushButton('Convert Image', self)
        self.convertButton.clicked.connect(self.ConvertImage)

        browseButtoniconPath = filePaths.mayaShelfIconPath + "folder.png"
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(browseButtoniconPath))
        self.browseButton.clicked.connect(self.showFileDialog)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.getFilePath, 1, 0)
        self.grid.addWidget(self.browseButton, 1, 1)
        self.grid.addWidget(self.convertButton, 2, 0, 2, 2)
        self.setLayout(self.grid)

    def showFileDialog(self):
        initialDir = filePaths.downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        fileFilter = "Image Files (*.jpg *.jpeg *.png *.bmp *.gif *.tif *.exr);;All Files (*)"
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                "Open Image File",
                                                initialDir,
                                                fileFilter,
                                                options=options)
        if filePath:
            # Set the selected file path in the QLineEdit
            self.getFilePath.setText(filePath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when button is pressed
    def ConvertImage(self):
        originalImagePath = self.getFilePath.text()
        if not originalImagePath:
            warningPopup('No texture selected')
        else:
            originalImagePath = originalImagePath.replace('\\', '\\')
            print (originalImagePath)
            outputImagePath = originalImagePath[:-4] + ".png"
            print (outputImagePath)
            #os.system("ocioconvert " +"%s" % (originalImagePath) +" digisx " "%s" % (outputImagePath) +" srgb")
            cmd = "magick convert {0}".format(originalImagePath) + " {0}".format(outputImagePath)
            returned_value = subprocess.check_output(cmd, shell=True)
            print (returned_value)

# definition to open UI

def launch():
     global win
     win = MainWindow()
     win.raise_()
     win.activateWindow()
     win.show()


launch()
