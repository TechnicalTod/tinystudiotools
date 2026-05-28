import os
import subprocess
from genTools.genUtils import warningPopup
from genTools.uiUtils import load_qss
from PySide6 import QtGui, QtWidgets, QtCore
import mayaFilePaths


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Supported output formats
        self.output_formats = {
            "PNG": {"ext": ".png", "lossy": False},
            "JPEG": {"ext": ".jpg", "lossy": True},
            "TIFF": {"ext": ".tif", "lossy": False},
            "EXR": {"ext": ".exr", "lossy": False},
            "BMP": {"ext": ".bmp", "lossy": False},
            "TGA": {"ext": ".tga", "lossy": False},
        }
        self.initUI()

    def initUI(self):
        # window prefs
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(600, 400)
        self.setWindowTitle("Advanced Texture Converter")
        self.setFocus()
        self.center()
        self.show()

        # Input file section
        self.inputLabel = QtWidgets.QLabel("Input File:")
        self.getFilePath = QtWidgets.QLineEdit(self)
        self.getFilePath.setPlaceholderText("Select an image file to convert")
        self.getFilePath.textChanged.connect(self.updatePreview)

        browseButtoniconPath = mayaFilePaths.mayaShelfIconPath + "folder.png"
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(browseButtoniconPath))
        self.browseButton.clicked.connect(self.showFileDialog)

        # Output format section
        self.formatLabel = QtWidgets.QLabel("Output Format:")
        self.formatComboBox = QtWidgets.QComboBox()
        self.formatComboBox.addItems(list(self.output_formats.keys()))
        self.formatComboBox.setCurrentText("PNG")
        self.formatComboBox.currentTextChanged.connect(self.onFormatChanged)

        # Quality section (for lossy formats)
        self.qualityLabel = QtWidgets.QLabel("Quality:")
        self.qualitySlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.qualitySlider.setRange(10, 100)
        self.qualitySlider.setValue(90)
        self.qualitySlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.qualitySlider.setTickInterval(10)

        self.qualitySpinBox = QtWidgets.QSpinBox()
        self.qualitySpinBox.setRange(10, 100)
        self.qualitySpinBox.setValue(90)
        self.qualitySpinBox.setSuffix("%")

        # Connect quality controls
        self.qualitySlider.valueChanged.connect(self.qualitySpinBox.setValue)
        self.qualitySpinBox.valueChanged.connect(self.qualitySlider.setValue)

        # Initially hide quality controls (PNG is lossless)
        self.qualityLabel.hide()
        self.qualitySlider.hide()
        self.qualitySpinBox.hide()

        # Image preview section
        self.previewLabel = QtWidgets.QLabel("Preview:")
        self.imagePreview = QtWidgets.QLabel()
        self.imagePreview.setFixedSize(200, 150)
        self.imagePreview.setStyleSheet(
            "border: 1px solid #555555; background-color: #2b2b2b; color: #b0b0b0;"
        )
        self.imagePreview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.imagePreview.setText("No image selected")
        self.imagePreview.setScaledContents(True)

        # Convert button
        self.convertButton = QtWidgets.QPushButton("Convert Image", self)
        self.convertButton.clicked.connect(self.ConvertImage)
        self.convertButton.setMinimumHeight(40)

        # Layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # Add widgets to layout
        row = 0
        self.grid.addWidget(self.inputLabel, row, 0)
        row += 1
        self.grid.addWidget(self.getFilePath, row, 0)
        self.grid.addWidget(self.browseButton, row, 1)

        row += 1
        self.grid.addWidget(self.formatLabel, row, 0)
        row += 1
        self.grid.addWidget(self.formatComboBox, row, 0)

        row += 1
        self.grid.addWidget(self.qualityLabel, row, 0)
        row += 1
        qualityLayout = QtWidgets.QHBoxLayout()
        qualityLayout.addWidget(self.qualitySlider)
        qualityLayout.addWidget(self.qualitySpinBox)
        qualityWidget = QtWidgets.QWidget()
        qualityWidget.setLayout(qualityLayout)
        self.grid.addWidget(qualityWidget, row, 0)

        row += 1
        self.grid.addWidget(self.previewLabel, row, 0)
        row += 1
        self.grid.addWidget(self.imagePreview, row, 0, 1, 2)

        row += 1
        self.grid.addWidget(self.convertButton, row, 0, 1, 2)

        self.setLayout(self.grid)

    def onFormatChanged(self, format_name):
        """Show/hide quality controls based on selected format"""
        is_lossy = self.output_formats[format_name]["lossy"]

        self.qualityLabel.setVisible(is_lossy)
        self.qualitySlider.setVisible(is_lossy)
        self.qualitySpinBox.setVisible(is_lossy)

    def updatePreview(self):
        """Update the image preview when file path changes"""
        file_path = self.getFilePath.text()
        if file_path and os.path.exists(file_path):
            try:
                pixmap = QtGui.QPixmap(file_path)
                if not pixmap.isNull():
                    # Scale the pixmap to fit the preview area
                    scaled_pixmap = pixmap.scaled(
                        self.imagePreview.size(),
                        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation,
                    )
                    self.imagePreview.setPixmap(scaled_pixmap)
                else:
                    self.imagePreview.setText("Invalid image")
                    self.imagePreview.setPixmap(QtGui.QPixmap())
            except Exception as e:
                self.imagePreview.setText("Preview unavailable")
                self.imagePreview.setPixmap(QtGui.QPixmap())
        else:
            self.imagePreview.setText("No image selected")
            self.imagePreview.setPixmap(QtGui.QPixmap())

    def showFileDialog(self):
        initialDir = mayaFilePaths.downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        fileFilter = (
            "Image Files (*.jpg *.jpeg *.png *.bmp *.gif *.tif *.tiff *.exr *.hdr);;All Files (*)"
        )
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image File", initialDir, fileFilter, options=options
        )
        if filePath:
            # Set the selected file path in the QLineEdit
            self.getFilePath.setText(filePath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when button is pressed
    def ConvertImage(self):
        originalImagePath = self.getFilePath.text()
        if not originalImagePath:
            warningPopup("No texture selected")
            return

        if not os.path.exists(originalImagePath):
            warningPopup("Selected file does not exist")
            return

        try:
            # Get selected format
            selected_format = self.formatComboBox.currentText()
            format_info = self.output_formats[selected_format]

            # Create output path with _converted suffix
            file_dir = os.path.dirname(originalImagePath)
            file_name = os.path.splitext(os.path.basename(originalImagePath))[0]
            output_filename = f"{file_name}_converted{format_info['ext']}"
            outputImagePath = os.path.join(file_dir, output_filename)

            # Build ImageMagick command
            cmd = f'magick convert "{originalImagePath}"'

            # Add quality setting for lossy formats
            if format_info["lossy"]:
                quality = self.qualitySpinBox.value()
                cmd += f" -quality {quality}"

            cmd += f' "{outputImagePath}"'

            print(f"Executing: {cmd}")

            # Execute conversion
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                success_msg = f"Successfully converted to:\n{outputImagePath}"
                QtWidgets.QMessageBox.information(self, "Conversion Complete", success_msg)
                print(f"Conversion successful: {outputImagePath}")
            else:
                error_msg = f"Conversion failed:\n{result.stderr}"
                warningPopup(error_msg)
                print(f"Conversion error: {result.stderr}")

        except Exception as e:
            error_msg = f"An error occurred during conversion:\n{str(e)}"
            warningPopup(error_msg)
            print(f"Exception during conversion: {e}")


# definition to open UI
def launch():
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()


launch()
