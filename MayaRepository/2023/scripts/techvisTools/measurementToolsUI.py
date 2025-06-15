import os
import sys
from PySide2 import QtGui, QtWidgets, QtCore
import maya.cmds as cmds
import mayaFilePaths
import maya.OpenMayaUI as OMUI
import shiboken2

import techvisTools.measurementTools as mt

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Get Maya's main window
        mayaWin = OMUI.MQtUtil.mainWindow()
        self.mayaWin = shiboken2.wrapInstance(int(mayaWin), QtWidgets.QWidget)

        # Parent your window to Maya's main window
        self.setParent(self.mayaWin)
        self.setWindowFlags(QtCore.Qt.Window)
        self.initUI()

    def initUI(self):
        with open("{}/dark.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(500, 100)
        self.setWindowTitle('Measurement Tool')
        self.setFocus()
        self.center()
        self.show()

        self.grid = QtWidgets.QGridLayout()
        #self.grid.setSpacing(10)

        # Adjust column stretch factors
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        self.settingsLabel = QtWidgets.QLabel("Measurement Settings (Works on multiple selected)")
        self.settingsLabel.setFixedHeight(30)
        self.settingsLabel.setAlignment(QtCore.Qt.AlignCenter)
        with open("{}/QLabelTitleFont.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.settingsLabel.setStyleSheet(fh.read())

        # Gap Size Slider
        self.gapLabel = QtWidgets.QLabel("Gap Size:")
        self.gapLabel.setFixedWidth(80)
        self.gapLabel.setAlignment(QtCore.Qt.AlignRight)
        self.gapSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gapSlider.setMinimum(0)
        self.gapSlider.setMaximum(50)  # 0.5 scaled by 100
        self.gapSlider.setValue(40)  # Default value 0.4 scaled
        self.gapValueLabel = QtWidgets.QLabel("0.40")
        self.gapValueLabel.setFixedWidth(40)
        self.gapValueLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.gapSlider.valueChanged.connect(self.updateGapValue)
        
        # Font Size Slider
        self.fontSizeLabel = QtWidgets.QLabel("Font Size:")
        self.fontSizeLabel.setFixedWidth(80)
        self.fontSizeLabel.setAlignment(QtCore.Qt.AlignRight)
        self.fontSizeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fontSizeSlider.setMinimum(1)
        self.fontSizeSlider.setMaximum(1000)
        self.fontSizeSlider.setValue(150)
        self.fontSizeValueLabel = QtWidgets.QLabel("15")
        self.fontSizeValueLabel.setFixedWidth(40)
        self.fontSizeValueLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.fontSizeSlider.valueChanged.connect(self.updateFontSizeValue)
        
        #Cylinder Width Slider
        self.cylwidthLabel = QtWidgets.QLabel("Cylinder Width:")
        self.cylwidthLabel.setFixedWidth(80)
        self.cylwidthLabel.setAlignment(QtCore.Qt.AlignRight)
        self.cylSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.cylSlider.setMinimum(1)
        self.cylSlider.setMaximum(1000)
        self.cylSlider.setValue(150)
        self.cylwidthValueLabel = QtWidgets.QLabel("15")
        self.cylwidthValueLabel.setFixedWidth(40)
        self.cylwidthValueLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.cylSlider.valueChanged.connect(self.updateCylWidthValue)
        
        #Cone Length Slider
        self.coneLLabel = QtWidgets.QLabel("Cone Length:")
        self.coneLLabel.setFixedWidth(80)
        self.coneLLabel.setAlignment(QtCore.Qt.AlignRight)
        self.coneLSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.coneLSlider.setMinimum(1)
        self.coneLSlider.setMaximum(50)  # 0.5 scaled by 100
        self.coneLSlider.setValue(4)  # Default value 0.4 scaled
        self.coneLValueLabel = QtWidgets.QLabel("0.04")
        self.coneLValueLabel.setFixedWidth(40)
        self.coneLValueLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.coneLSlider.valueChanged.connect(self.updateConeLValue)
        
        #Cone Width Slider
        self.coneWLabel = QtWidgets.QLabel("Cone Width:")
        self.coneWLabel.setFixedWidth(80)
        self.coneWLabel.setAlignment(QtCore.Qt.AlignRight)
        self.coneWSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.coneWSlider.setMinimum(1)
        self.coneWSlider.setMaximum(1000)
        self.coneWSlider.setValue(150)
        self.coneWValueLabel = QtWidgets.QLabel("15")
        self.coneWValueLabel.setFixedWidth(40)
        self.coneWValueLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.coneWSlider.valueChanged.connect(self.updateConeWidthValue)
        
        # Button 'Create Shot Folders'
        self.buttonLabel = QtWidgets.QLabel("Create Measurements:")
        self.buttonLabel.setFixedHeight(30)
        self.buttonLabel.setAlignment(QtCore.Qt.AlignCenter)
        with open("{}/QLabelTitleFont.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.buttonLabel.setStyleSheet(fh.read())

        self.launchToolButton1 = QtWidgets.QPushButton("Raycast (Through camera)")
        self.launchToolButton1.clicked.connect(self.launchMeasurementToolRay)

        self.launchToolButton2 = QtWidgets.QPushButton("Selected (Two selected objects)")
        self.launchToolButton2.clicked.connect(self.launchMeasurementToolSel)

        with open("{}/importButton.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.launchToolButton1.setStyleSheet(fh.read())
        with open("{}/importButton.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.launchToolButton2.setStyleSheet(fh.read())

        self.settingslabelLayout = QtWidgets.QGridLayout()
        self.labelLayout = QtWidgets.QGridLayout()
        self.sliderLayout = QtWidgets.QGridLayout()
        self.valueLayout = QtWidgets.QGridLayout()
        self.buttonLayout = QtWidgets.QGridLayout()

        self.settingslabelLayout.addWidget(self.settingsLabel, 0, 0)

        # Adding widgets to the layout
        self.labelLayout.addWidget(self.gapLabel, 0, 0)
        self.sliderLayout.addWidget(self.gapSlider, 0, 1)
        self.valueLayout.addWidget(self.gapValueLabel, 0, 2)
        
        self.labelLayout.addWidget(self.fontSizeLabel, 1, 0)
        self.sliderLayout.addWidget(self.fontSizeSlider, 1, 1)
        self.valueLayout.addWidget(self.fontSizeValueLabel, 1, 2)
        
        self.labelLayout.addWidget(self.cylwidthLabel, 2, 0)
        self.sliderLayout.addWidget(self.cylSlider, 2, 1)
        self.valueLayout.addWidget(self.cylwidthValueLabel, 2, 2)
        
        self.labelLayout.addWidget(self.coneLLabel, 3, 0)
        self.sliderLayout.addWidget(self.coneLSlider, 3, 1)
        self.valueLayout.addWidget(self.coneLValueLabel, 3, 2)
        
        self.labelLayout.addWidget(self.coneWLabel, 4, 0)
        self.sliderLayout.addWidget(self.coneWSlider, 4, 1)
        self.valueLayout.addWidget(self.coneWValueLabel, 4, 2)

        self.buttonLayout.addWidget(self.buttonLabel, 0, 0, 1, 2)
        self.buttonLayout.addWidget(self.launchToolButton1, 1, 0, 1, 1)
        self.buttonLayout.addWidget(self.launchToolButton2, 1, 1, 1, 1)

        self.grid.addLayout(self.settingslabelLayout, 0, 0, 1, 3)
        self.grid.addLayout(self.labelLayout, 1, 0)
        self.grid.addLayout(self.sliderLayout, 1, 1)
        self.grid.addLayout(self.valueLayout, 1, 2)
        self.grid.addLayout(self.buttonLayout, 2, 0, 1, 3)

        self.setLayout(self.grid)
   
    def updateGapValue(self, value):
        real_value = value / 100.0
        self.gapValueLabel.setText("{:.2f}".format(real_value))
        selected_objects = cmds.ls(selection=True)
        measurement_group_objects = [obj for obj in selected_objects if obj.startswith('MeasurementGroup')]
        for object in measurement_group_objects:
            cmds.setAttr(f'{object}.GapSize', real_value)
            
    def updateFontSizeValue(self, value):
        real_value = value / 10.0
        self.fontSizeValueLabel.setText(str(real_value))
        selected_objects = cmds.ls(selection=True)
        measurement_group_objects = [obj for obj in selected_objects if obj.startswith('MeasurementGroup')]
        for object in measurement_group_objects:
            cmds.setAttr(f'{object}.FontSize', real_value)
            
    def updateCylWidthValue(self, value):
        real_value = value / 10.0
        self.cylwidthValueLabel.setText(str(real_value))
        selected_objects = cmds.ls(selection=True)
        measurement_group_objects = [obj for obj in selected_objects if obj.startswith('MeasurementGroup')]
        for object in measurement_group_objects:
            cmds.setAttr(f'{object}.CylinderWidth', real_value)
    
    def updateConeLValue(self, value):
        real_value = value / 100.0
        self.coneLValueLabel.setText("{:.2f}".format(real_value))
        selected_objects = cmds.ls(selection=True)
        measurement_group_objects = [obj for obj in selected_objects if obj.startswith('MeasurementGroup')]
        for object in measurement_group_objects:
            cmds.setAttr(f'{object}.coneLength', real_value)
    
    def updateConeWidthValue(self, value):
        real_value = value / 10.0
        self.coneWValueLabel.setText(str(real_value))
        selected_objects = cmds.ls(selection=True)
        measurement_group_objects = [obj for obj in selected_objects if obj.startswith('MeasurementGroup')]
        for object in measurement_group_objects:
            cmds.setAttr(f'{object}.coneWidth', real_value)
    
    def center(self):
            qr = self.frameGeometry()
            cp = QtWidgets.QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())

    def launchMeasurementToolRay(self):
        gap_size = self.gapSlider.value() / 100.0
        font_size = self.fontSizeSlider.value() / 10.0
        cylinder_width = self.fontSizeSlider.value() / 10
        cone_length = self.coneLSlider.value() / 100
        cone_width = self.coneWSlider.value() / 10
        mt.place_locator_ray(gap_size, font_size, cylinder_width, cone_length, cone_width)

    def launchMeasurementToolSel(self):
        gap_size = self.gapSlider.value() / 100.0
        font_size = self.fontSizeSlider.value() / 10.0
        cylinder_width = self.fontSizeSlider.value() / 10
        cone_length = self.coneLSlider.value() / 100
        cone_width = self.coneWSlider.value() / 10
        mt.place_locator(gap_size, font_size, cylinder_width, cone_length, cone_width)
            
def openWindow():
    if QtWidgets.QApplication.instance():
        for win in QtWidgets.QApplication.allWindows():
            print(win.objectName())
            if 'Measurement Tool' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()