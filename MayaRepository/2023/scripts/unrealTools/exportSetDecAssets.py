import os
import sys
import pymel.core as pm
import maya.cmds as mc
from PySide2 import QtGui, QtWidgets, QtCore
import shutil
import filePaths
import maya.OpenMayaUI as OMUI
import shiboken2

SHOWDRIVE = filePaths.showDir

parameterList = {
    'USDPreviewMaterial': {
        'diffuse': {'suffix': 'Diffuse', 'mayaParameter': 'diffuseColor'},
        'emissive': {'suffix': 'Emissive', 'mayaParameter': 'emissiveColor'},
        'ao': {'suffix': 'AO', 'mayaParameter': 'occlusion'},
        'opacity': {'suffix': 'Transparency', 'mayaParameter': 'opacity'},
        'metallic': {'suffix': 'Metallic', 'mayaParameter': 'metallic'},
        'roughness': {'suffix': 'Roughness', 'mayaParameter': 'roughness'},
        'normal': {'suffix': 'Normal', 'mayaParameter': 'normal'},
        'subsurface': {'suffix': 'Translucency', 'mayaParameter': 'clearcoat', 'fileNodeParameter': 'outAlpha'},
        'displacement': {'suffix': 'Displacement', 'mayaParameter': 'displacement', 'fileNodeParameter': 'outAlpha'}
    }
}

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
        # window prefs
        with open("{}/dark.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle('Publish Set Dec Assets')
        self.setFocus()
        self.center()
        self.show()

        self.setGeometry(100, 100, 1100, 500)

        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)

        #create table widget
        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnWidth(0, 800)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)

        self.tableWidgetHeader = self.tableWidget.horizontalHeader()
        self.tableWidgetHeader.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.tableWidget.setHorizontalHeaderLabels(["Set Dec name", "Variant", "Current Version", "New Version"])

        self.tableWidget.cellClicked.connect(self.cellClickedGrabShape)

        buttonslayout = QtWidgets.QGridLayout(self)

        # create buttons
        self.addButton = QtWidgets.QPushButton('Add Set Dec')
        self.addButton.clicked.connect(self.add)

        self.removeButton = QtWidgets.QPushButton('Remove Selection')
        self.removeButton.clicked.connect(self.remove)

        self.clearButton = QtWidgets.QPushButton('Clear All')
        self.clearButton.clicked.connect(self.clear)

        self.refreshButton = QtWidgets.QPushButton('Refresh List')
        self.refreshButton.clicked.connect(self.resetCurrentList)

        self.unpublishButton = QtWidgets.QPushButton('Unpublish Selection')
        self.unpublishButton.clicked.connect(self.unpublishSelected)

        self.exportButton = QtWidgets.QPushButton('Publish')
        self.exportButton.clicked.connect(self.collectListForPublish)

        ShowSettingslayout = QtWidgets.QGridLayout(self)

        self.showComboBoxLabel = QtWidgets.QLabel("Show")
        self.showComboBox = QtWidgets.QComboBox()
        self.showComboBox.currentTextChanged.connect(self.updateSetDecGroupComboBox)

        self.setDecGroupComboBoxLabel = QtWidgets.QLabel("Set Dec Group")
        self.setDecGroupComboBox = QtWidgets.QComboBox()
        self.setDecGroupComboBox.setEditable(True)
        self.setDecGroupComboBox.currentTextChanged.connect(self.resetCurrentList)

        #adjust the import button style sheet
        with open("{}/importButton.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            self.exportButton.setStyleSheet(fh.read())
        #adjust the unpublish button style sheet
        with open("{}/unpublishButton.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            self.unpublishButton.setStyleSheet(fh.read())

        layout.addWidget(self.tableWidget, 0, 1, 5, 4)

        buttonslayout.addWidget(self.addButton, 0, 5)
        buttonslayout.addWidget(self.removeButton, 1, 5)
        buttonslayout.addWidget(self.clearButton, 2, 5)
        buttonslayout.addWidget(self.refreshButton, 3, 5)
        buttonslayout.addWidget(self.unpublishButton, 4, 5)
        layout.addWidget(self.exportButton, 4, 5, alignment= QtCore.Qt.AlignBottom)

        ShowSettingslayout.addWidget(self.showComboBoxLabel, 0, 0)
        ShowSettingslayout.addWidget(self.showComboBox, 1, 0)
        ShowSettingslayout.addWidget(self.setDecGroupComboBoxLabel, 2, 0)
        ShowSettingslayout.addWidget(self.setDecGroupComboBox, 3, 0)

        layout.addLayout(ShowSettingslayout, 0, 0)
        layout.addLayout(buttonslayout, 0, 5)

        # Run all UI initial configuration
        self.getShowList()
        # show the window
        self.show()

    #sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    #Function to add rows to table
    def add(self, shapeList=None):
        #get folder paths from the selected show and set dec group
        selectedShow = self.showComboBox.currentText()
        setDecGroupFolderBasePath = "{}/{}/03_Production/Assets/SETDEC".format(SHOWDRIVE, selectedShow)
        setDecGroupFolderName = setDecGroupFolderBasePath + "/" + self.setDecGroupComboBox.currentText() + "/"

        #get list of selected shapes
        shapes = []
        if shapeList:
            shapes = shapeList
        else:
            shapes = pm.ls(sl=1)

        #loop over shape list to make sure all selected items are maya geo if not throw an error
        badShapeList = []
        for shape in shapes:
            shape = pm.PyNode(shape)
            if shape.getShape() and shape.getShape().nodeType() == 'mesh':
                pass
            else:
                badShapeList.append(shape.name())

        if badShapeList:
            badShapeListString = ", ".join(badShapeList)
            self.warningPopup("You are trying to load a Set Dec item with no connected shapes, this item has been removed from the list: {}".format(badShapeListString))

        shapes = [x for x in shapes if x not in badShapeList]
        #get initial row count
        init_row_number = self.tableWidget.rowCount()

        #Loop over shape selection and create new rows
        for row_number, shape in enumerate(shapes):
            shape = pm.PyNode(shape)
            splitShapeName = shape.nodeName().split("|")[-1]
            self.tableWidget.insertRow(init_row_number + row_number)
            self.tableWidget.setItem(init_row_number + row_number, 0, QtWidgets.QTableWidgetItem(shape.name()))

            #create combo box for variant column
            variantComboBox = QtWidgets.QComboBox()
            variantComboBox.setEditable(True)
            self.tableWidget.setCellWidget(init_row_number + row_number, 1, variantComboBox)
            variantList = []

            #get list of variants from path dir
            try:
                for variant in os.listdir(setDecGroupFolderName + splitShapeName):
                    variantList.append(variant)
                variantComboBox.addItems(variantList)
                variantComboBox.setCurrentIndex(0)
                if len(variantList) > 1:
                    with open("{}/qComboBoxMultiItemYellow.qss".format(filePaths.styleSheetFilepath), "r") as fh:
                        variantComboBox.setStyleSheet(fh.read())
            except:
                variantComboBox.addItems(["base"])
                variantComboBox.setCurrentIndex(0)

            #create combo box for version column
            versionComboBox = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(init_row_number + row_number, 2, versionComboBox)
            versionList = []
            #get list of versions from path dir
            try:
                for versionFolder in os.listdir(setDecGroupFolderName + splitShapeName + "/" + variantComboBox.currentText()):
                    versionList.append(versionFolder)
                versionComboBox.addItems(versionList)
                versionComboBox.setCurrentIndex(len(versionList)-1)
            except:
                versionComboBox.addItems(["N/A"])
                with open("{}/qComboBoxMultiItemGreen.qss".format(filePaths.styleSheetFilepath), "r") as fh:
                    versionComboBox.setStyleSheet(fh.read())
                versionComboBox.setCurrentIndex(0)

            #create combo box for new version column
            newVersionComboBox = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(init_row_number + row_number, 3, newVersionComboBox)

            self.getLatestVersionNumber(init_row_number + row_number, versionComboBox, newVersionComboBox)

            #set combobox update linking
            variantComboBox.currentTextChanged.connect(lambda
                                                        index,
                                                        row=init_row_number + row_number,
                                                        column=1:
                                                        self.updateVerNumOnVarChange(row))
            versionComboBox.currentTextChanged.connect(lambda
                                                        row=init_row_number + row_number,
                                                        versionComboBox=versionComboBox,
                                                        newVersionComboBox=newVersionComboBox:
                                                        self.getLatestVersionNumber(row,
                                                                                    versionComboBox,
                                                                                    newVersionComboBox))
            #set duplicate setDec names red
            self.setDuplicateInputsRed()
            self.setPublishedInputsBlue()

    def contextMenuEvent(self, event):
        # Create a context menu
        menu = QtWidgets.QMenu(self)
        # Add actions to the context menu
        MenuItem01 = menu.addAction("Set variant names on multiple selection")
        MenuItem01.triggered.connect(self.renameSelectedVariants)
        menu.addSeparator()
        MenuItem02 = menu.addAction("Remove selected item(s) from list")
        MenuItem02.triggered.connect(self.remove)

        # Show the context menu at the cursor position
        action = menu.exec_(self.mapToGlobal(event.pos()))

    def updateVerNumOnVarChange(self, row):
        #get folder paths from the selected show and set dec group
        selectedShow = self.showComboBox.currentText()
        setDecGroupFolderBasePath = "{}/{}/03_Production/Assets/SETDEC".format(SHOWDRIVE, selectedShow)
        setDecGroupFolderName = setDecGroupFolderBasePath + "/" + self.setDecGroupComboBox.currentText() + "/"
        #look up set Dec name from table
        setDecName = self.tableWidget.item(row, 0)
        setDecName = setDecName.text()
        setDecName = pm.PyNode(setDecName)
        splitSetDecObjectName = setDecName.nodeName().split("|")[-1]
        #look up corresponding variant name from table
        setDecVariant = self.tableWidget.cellWidget(row, 1)
        setDecVariant = setDecVariant.currentText()
        #look up corresponding asset type from table
        setDecCurrentVersion = self.tableWidget.cellWidget(row, 2)
        #look up corresponding asset type from table
        setDecNewVersion = self.tableWidget.cellWidget(row, 3)

        setDecCurrentVersion.clear()
        versionList = []
        #get list of versions from path dir
        try:
            for versionFolder in os.listdir(setDecGroupFolderName + splitSetDecObjectName + "/" + setDecVariant):
                versionList.append(versionFolder)
            setDecCurrentVersion.addItems(versionList)
            setDecCurrentVersion.setCurrentIndex(len(versionList)-1)
            self.getLatestVersionNumber(row, setDecCurrentVersion, setDecNewVersion)
            with open("{}/dark.qss".format(filePaths.styleSheetFilepath), "r") as fh:
                setDecCurrentVersion.setStyleSheet(fh.read())
        except:
            setDecNewVersion.clear()
            setDecCurrentVersion.addItems(["N/A"])
            with open("{}/qComboBoxMultiItemGreen.qss".format(filePaths.styleSheetFilepath), "r") as fh:
                setDecCurrentVersion.setStyleSheet(fh.read())
            setDecCurrentVersion.setCurrentIndex(0)
            setDecNewVersion.addItems(["v001"])
            setDecNewVersion.setCurrentIndex(0)

        print("Variant changed to {}/{} finding latest versions".format(splitSetDecObjectName, setDecVariant))

    #Function to remove rows to table (must remove in reverse order)
    def remove(self):
        rowList = sorted(set(index.row() for index in
                        self.tableWidget.selectedIndexes()))
        for row in reversed(sorted(rowList)):
            self.tableWidget.removeRow(row)
        self.resetCurrentList()

    #Function to completely clear table
    def clear(self):
        self.tableWidget.setRowCount(0)

    def renameSelectedVariants(self):
        input_dialog = QtWidgets.QInputDialog(self)
        with open("{}/dark.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            input_dialog.setStyleSheet(fh.read())
        newVariantName, ok = input_dialog.getText(self, "Set Variant Name", "Enter new variant name:")
        if ok:
            rowList = sorted(set(index.row() for index in
                            self.tableWidget.selectedIndexes()))
            for row in sorted(rowList):
                setDecVariant = self.tableWidget.cellWidget(row, 1)
                setDecVariant.addItem(newVariantName)
                setDecVariant.setCurrentText(newVariantName)
                self.updateVerNumOnVarChange(row)

    #Function to completely clear table
    def resetCurrentList(self):
        storeSelection = pm.ls(sl=1)
        pm.select(clear=1)
        setDecAssetList = []
        init_row_number = self.tableWidget.rowCount()
        #Initial sanity checks on the asset list for duplicate naming
        for row in range(init_row_number):
            #look up set Dec name from table
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            if pm.objExists(setDecName):
                setDecAssetList.append(setDecName)
            else:
                print ("Found asset that no longer exists, removing from list{}".format(setDecName))
                pass
        self.clear()
        self.add(setDecAssetList)
        pm.select(storeSelection)

    #Show file dialog (currently kinda hacky as it has to use non native dialog)
    #This is done so we can select multiple folders. could be a lot better
    def showFileDialog(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QtWidgets.QListView, 'listView')
        # to make it possible to select multiple directories:
        if file_view:
            file_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QtWidgets.QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        if file_dialog.exec():
            paths = file_dialog.selectedFiles()
            return paths

    def getShowList(self):
        unwanted_dirs = {'$RECYCLE.BIN', 'System Volume Information'}
        availableShows = [
            d for d in os.listdir(SHOWDRIVE)
            if os.path.isdir(os.path.join(SHOWDRIVE, d)) and not d.startswith('.') and d not in unwanted_dirs
        ]
        self.showComboBox.addItems(availableShows)

    def updateSetDecGroupComboBox(self):
        self.resetCurrentList()
        self.setDecGroupComboBox.clear()
        selectedShow = self.showComboBox.currentText()
        setDecGroupFolder = "{}/{}/03_Production/Assets/SETDEC".format(SHOWDRIVE, selectedShow)
        if os.path.exists(setDecGroupFolder):
            availableSetDecGroups = os.listdir(setDecGroupFolder)
            self.setDecGroupComboBox.addItems(availableSetDecGroups)

    def getDuplicatesInList(self):
        init_row_number = self.tableWidget.rowCount()
        #Initial sanity checks on the asset list for duplicate naming
        setDecAssetList = []
        for row in range(init_row_number):
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            setDecObject = pm.PyNode(setDecName)
            setDecObjectShortName = setDecObject.nodeName().split("|")[-1]
            setDecAssetList.append(setDecObjectShortName)
        duplicateShapeNames = set([name for name in setDecAssetList if setDecAssetList.count(name) > 1])
        return duplicateShapeNames

    def getPublishedInList(self):
        init_row_number = self.tableWidget.rowCount()
        #Initial sanity checks on the asset list for duplicate naming
        publishedSetDecAssetList = []
        for row in range(init_row_number):
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            setDecObject = pm.PyNode(setDecName)
            try:
                if setDecObject.published.get():
                    setDecObjectShortName = setDecObject.nodeName().split("|")[-1]
                    publishedSetDecAssetList.append(setDecObjectShortName)
            except:
                pass
        return publishedSetDecAssetList

    def checkShadersInList(self):
        init_row_number = self.tableWidget.rowCount()
        shaderNotOkList = []
        for row in range(init_row_number):
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            setDecObject = pm.PyNode(setDecName)
            setDecObjectShape = setDecObject.getShape()

            if self.hasUsdPreviewMaterial(setDecObjectShape) == False:
                setDecObjectShortName = setDecObject.nodeName().split("|")[-1]
                shaderNotOkList.append(setDecObjectShortName)

        return shaderNotOkList

    def hasUsdPreviewMaterial(self, shapeNode):
        shadingEngines = shapeNode.shadingGroups()
        if not shadingEngines:
            return False

        for shadingEngine in shadingEngines:
            materials = shadingEngine.surfaceShader.inputs()
            for material in materials:
                if material.type() == 'usdPreviewSurface':
                    return True
                else:
                    return False

    def setDuplicateInputsRed(self):
        getDuplicatesInList = self.getDuplicatesInList()
        init_row_number = self.tableWidget.rowCount()
        #Initial sanity checks on the asset list for duplicate naming
        setDecAssetList = []
        for row in range(init_row_number):
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            setDecObject = pm.PyNode(setDecName)
            setDecObjectShortName = setDecObject.nodeName().split("|")[-1]
            if setDecObjectShortName in getDuplicatesInList:
                self.tableWidget.item(row, 0).setBackground(QtGui.QColor("#7D2020"))

    def setPublishedInputsBlue(self):
        getPublishedInList = self.getPublishedInList()
        init_row_number = self.tableWidget.rowCount()
        #Initial sanity checks on the asset list for duplicate naming
        setDecAssetList = []
        for row in range(init_row_number):
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            setDecObject = pm.PyNode(setDecName)
            setDecObjectShortName = setDecObject.nodeName().split("|")[-1]
            if setDecObjectShortName in getPublishedInList:
                self.tableWidget.item(row, 0).setForeground(QtGui.QColor(80, 153, 255))

    #Function to remove rows to table (must remove in reverse order)
    def unpublishSelected(self):
        rowList = sorted(set(index.row() for index in
                        self.tableWidget.selectedIndexes()))
        for row in reversed(sorted(rowList)):
            setDecName = self.tableWidget.item(row, 0)
            setDecName = setDecName.text()
            setDecObject = pm.PyNode(setDecName)
            setDecObjectShortName = setDecObject.nodeName().split("|")[-1]

            try:
                if setDecObject.published.get():
                    #Run shader checks and try to set shader back to original if found otherwise rename shader to original name
                    #get a list of all shaders attached to imported published shape
                    publishedSetDecObjectShapeNode = setDecObject.getShape()
                    publishedSetDecShadingGroups = publishedSetDecObjectShapeNode.shadingGroups()
                    publishedSetDecObjectShaders = pm.ls(pm.listConnections(publishedSetDecShadingGroups), materials=True)
                    for shader in publishedSetDecObjectShaders:
                        importedShaderObject = pm.PyNode(shader)
                        importedShadingGroups = importedShaderObject.shadingGroups()
                        publishedShaderName = importedShaderObject.shaderName.get()
                        publishedShaderObject = []
                        try:
                            publishedShaderObject = pm.PyNode(publishedShaderName)
                            publishedShadingGroups = publishedShaderObject.shadingGroups()
                            if pm.objExists(publishedShaderObject):
                                print ("Found Original Shader name in scene re-applying this to imported asset")
                                faceAssignments = pm.sets(importedShadingGroups[0], q=True)
                                print (faceAssignments)
                                pm.sets(publishedShadingGroups[0], e=True, forceElement=faceAssignments)
                        except:
                            print ("Could not find original shader renaming current shader to original published name")
                            importedShaderObject.rename(publishedShaderName)

                    setDecObject.useOutlinerColor.set(False)
                    # Remove custom shape attributes added during publishing
                    customShapeAttrs = ["assetName",
                                "fbxExportPath",
                                "usdExportPath",
                                "mayaExportPath",
                                "textureDir",
                                "version",
                                "published",
                                "variantName",
                                "basePath",
                                "publishedShaderList"]
                    for attr in customShapeAttrs:
                        if setDecObject.hasAttr(attr):
                            pm.deleteAttr(setDecObject.attr(attr))
            except:
                pass

        self.resetCurrentList()

    def collectListForPublish(self):
        pm.undoInfo(openChunk=True)
        init_row_number = self.tableWidget.rowCount()
        duplicateShapeNames = self.getDuplicatesInList()
        publishedShapeNames = self.getPublishedInList()
        brokenShaderShapeNames = self.checkShadersInList()
        if brokenShaderShapeNames:
            brokenShaderShapeNames = ", ".join(brokenShaderShapeNames)
            self.warningPopup("Incorrect shaders found in list: {}, must be USD Preview material".format(brokenShaderShapeNames))
            return
        if duplicateShapeNames:
            duplicateShapeNames = ", ".join(duplicateShapeNames)
            self.warningPopup("Duplicate shape names found in list: {}, please fix or remove from list before publishing".format(duplicateShapeNames))
            return
        if publishedShapeNames:
            publishedShapeNames = ", ".join(publishedShapeNames)
            self.warningPopup("Published shapes found in list: {}, please unpublish or remove from list before publishing".format(publishedShapeNames))
            return
        else:
            print("No duplicate shape names found in the selection, continuing")
            for row in range(init_row_number):
                #look up set Dec name from table
                setDecName = self.tableWidget.item(row, 0)
                setDecName = setDecName.text()
                setDecObject = pm.PyNode(setDecName)
                if pm.objExists(setDecObject):
                    splitSetDecObjectName = setDecObject.nodeName().split("|")[-1]
                    #look up corresponding variant name from table
                    setDecVariant = self.tableWidget.cellWidget(row, 1)
                    setDecVariantName = setDecVariant.currentText()
                    #look up corresponding asset type from table
                    setDecNewVersion = self.tableWidget.cellWidget(row, 3)
                    setDecNewVersion = setDecNewVersion.currentText()

                    existingShaders, textureBasePath, pubTexturedict = self.publishSetDecTextures(setDecObject,
                                                                splitSetDecObjectName,
                                                                setDecVariantName,
                                                                setDecNewVersion)
                    self.publishSetDec(setDecObject,
                                        splitSetDecObjectName,
                                        setDecVariantName,
                                        setDecNewVersion,
                                        existingShaders,
                                        textureBasePath,
                                        pubTexturedict)
                else:
                    print("Node '{}' does not exist.".format(setDecObject))

        pm.undoInfo(openChunk=False)
        self.resetCurrentList()

    def publishSetDecTextures(self, setDecObject, splitSetDecObjectName, setDecVariantName, setDecNewVersion):
        selectedShow = self.showComboBox.currentText()
        setDecGroupFolderBasePath = "{}/{}/03_Production/Assets/SETDEC/".format(SHOWDRIVE, selectedShow)
        setDecGroupFolderName = setDecGroupFolderBasePath + self.setDecGroupComboBox.currentText() + "/"
        setDecAssetPath = setDecGroupFolderName + splitSetDecObjectName + "/" + setDecVariantName + "/" + setDecNewVersion + "/"

        shaderList = []
        #get a list of all shaders attached to shape
        setDecObjectShapeNode = setDecObject.getShape()
        getShadingGroups = setDecObjectShapeNode.shadingGroups()
        setDecObjectShaders = pm.ls(pm.listConnections(getShadingGroups), materials=True)
        print (setDecObjectShaders)
        for shader in setDecObjectShaders:
            shaderList.append(shader)
        pubTexturedict = {}
        # Loop through attached shaders and get all textures connected to materials
        for shader in set(shaderList):
            pubTexturedict[shader] = {}
            for parameter in parameterList.get('USDPreviewMaterial'):
                try:
                    mayaParameterName = parameterList.get('USDPreviewMaterial').get(parameter).get('mayaParameter')
                    fileNode = pm.listConnections('{}.{}'.format(shader, mayaParameterName), source=True, destination=False)

                    # Check if the parameter is 'normal' and traverse through the bump2d node
                    if parameter == 'normal':
                        fileNode = pm.listConnections(fileNode[0], source=True, destination=False)
                        print ("NORMAL", fileNode)
                    if fileNode:
                        print ("ATANDARD", fileNode)
                        texturePath = fileNode[0].fileTextureName.get()
                        texturePath = texturePath.replace("\\", "/")
                        fileName = texturePath.split("/")[-1]
                        fileNameSplit = fileName.split(".<UDIM>.png")[0]
                        texturePath = texturePath.split(fileName)[0]
                        textureList = [os.path.join(texturePath, tex) for tex in os.listdir(texturePath) if tex.endswith(".png") and fileNameSplit in tex]
                        pubTexturedict[shader][parameter] = textureList
                    else:
                        pubTexturedict[shader][parameter] = []
                except Exception as e:
                    print(f"No texture found for {parameter}: {e}")

        #build export directory
        textureBasePath = setDecAssetPath + "tex"
        self.createDir(textureBasePath)
        #copy all textures into the publish folder and swap the paths in the filenodes
        for shader in pubTexturedict:
            print (shader)
            for parameterName in pubTexturedict[shader]:
                print (parameterName)
                textureList = (pubTexturedict[shader][parameterName])
                mayaParameterName = (parameterList.get('USDPreviewMaterial').get(parameterName).get('mayaParameter'))
                for texturePath in textureList:
                    #copy texture to pub folder
                    shutil.copy(texturePath, textureBasePath)
                    fileNode = pm.listConnections('{}.{}'.format(shader, mayaParameterName))
                    if parameterName == 'normal':
                        fileNode = pm.listConnections(fileNode[0], source=True, destination=False)
                    texturePath = fileNode[0].fileTextureName.get()
                    texturePath = texturePath.replace("\\", "/")
                    textureNameFull = texturePath.split("/")[-1]
                    if texturePath.endswith(".<UDIM>.png"):
                        print ("found UDIM tag")
                        textureNameNoUdim = textureNameFull.split(".")[0]
                        textureNameAddUDIMTag = textureNameNoUdim + ".1001.png"
                        newTexturePathFull = textureBasePath + "/" + textureNameAddUDIMTag
                        print (newTexturePathFull)
                        fileNode[0].fileTextureName.set(newTexturePathFull)
                    else:
                        print ("no UDIM tag")
                        newTexturePathFull = textureBasePath + "/" + textureNameFull
                        print (newTexturePathFull)
                        fileNode[0].fileTextureName.set(newTexturePathFull)

        return shaderList, textureBasePath, pubTexturedict

    def publishSetDec(self,
                    setDecObject,
                    splitSetDecObjectName,
                    setDecVariantName,
                    setDecNewVersion,
                    existingShaders,
                    textureBasePath,
                    pubTexturedict):

        selectedShow = self.showComboBox.currentText()
        setDecGroupFolderBasePath = "{}/{}/03_Production/Assets/SETDEC/".format(SHOWDRIVE, selectedShow)
        setDecGroupFolderName = setDecGroupFolderBasePath + self.setDecGroupComboBox.currentText() + "/"
        setDecAssetPath = setDecGroupFolderName + splitSetDecObjectName + "/" + setDecVariantName + "/" + setDecNewVersion + "/"

        fbxBasePath = setDecAssetPath + "fbx"
        fbxFileName = "{}_{}.fbx".format(splitSetDecObjectName, setDecNewVersion)
        fbxFullPath = fbxBasePath + "/" + fbxFileName
        usdBasePath = setDecAssetPath + "usd"
        usdFileName = "{}_{}.usda".format(splitSetDecObjectName, setDecNewVersion)
        usdFullPath = usdBasePath + "/" + usdFileName
        mayaBasePath = setDecAssetPath + "maya"
        mayaFileName = "{}_{}.ma".format(splitSetDecObjectName, setDecNewVersion)
        mayaFullPath = mayaBasePath + "/" + mayaFileName

        newDirList = (fbxBasePath, usdBasePath, mayaBasePath)

        for dir in newDirList:
            self.createDir(dir)

        # Store original parent and world matrix for later
        originalParent = setDecObject.getParent()
        originalMatrix = setDecObject.getMatrix(worldSpace=True)
        # Unparent and reset transformations
        pm.parent(setDecObject, world=True)
        setDecObject.setMatrix(pm.dt.Matrix(), worldSpace=True)

        # Change the outliner color to blue just before adding attributes
        setDecObject.useOutlinerColor.set(True)
        setDecObject.outlinerColor.set([0, 0.6, 1])  # RGB for blue

        # Add custom attributes for export paths and version
        pm.addAttr(setDecObject, longName='assetName', dataType='string', k=True)
        setDecObject.assetName.set(splitSetDecObjectName)
        pm.addAttr(setDecObject, longName='variantName', dataType='string', k=True)
        setDecObject.variantName.set(setDecVariantName)
        pm.addAttr(setDecObject, longName='version', dataType='string', k=True)
        setDecObject.version.set(setDecNewVersion)
        pm.addAttr(setDecObject, longName='basePath', dataType='string', k=True)
        setDecObject.basePath.set(setDecGroupFolderName)
        pm.addAttr(setDecObject, longName='published', attributeType='bool', k=True)
        setDecObject.published.set(True)
        pm.addAttr(setDecObject, longName='publishedShaderList', dataType='string', k=True)
        setDecObject.publishedShaderList.set(",".join(str(i) for i in existingShaders))

        #set extra attributes on shaders
        for shader in existingShaders:
            shaderObject = pm.PyNode(shader)

            # Add custom attributes
            if not shaderObject.hasAttr("shaderName"):
                pm.addAttr(shaderObject, longName='shaderName', dataType='string', k=True)
            shaderObject.shaderName.set(shader)

        # Export operations
        pm.select(setDecObject)
        #FBX
        pm.mel.FBXResetExport()
        pm.mel.FBXExportSmoothingGroups(v=True)
        pm.mel.FBXExport(file=fbxFullPath, s=True)
        #USDA
        USDExportoptions = ('parentScope={};materialsScopeName=mtl'.format(splitSetDecObjectName))
        pm.exportSelected(usdFullPath, force=True, type="USD export", options=USDExportoptions)
        #Maya Ascii
        pm.exportSelected(mayaFullPath, force=True, type='mayaAscii', options="v=0;")

        # Cleanup: delete the transform node
        pm.delete(setDecObject)

        # Re-import the .ma file and reapply transformations and parent, ensuring no namespace is added
        importedNodes = pm.importFile(mayaFullPath, returnNewNodes=True, mergeNamespacesOnClash=False)
        importedTransform = [node for node in importedNodes if isinstance(node, pm.nt.Transform)][0]
        # Re-parent to original parent and apply original transforms
        if originalParent:
            pm.parent(importedTransform, originalParent)
        importedTransform.setMatrix(originalMatrix, worldSpace=True)

    def getTransformData(self, node):
        # Get translate, rotate, and scale values
        translation = node.getTranslation(space='world')
        rotation = node.getRotation(space='world')
        scale = node.getScale()
        return translation, rotation, scale

    def getLatestVersionNumber(self, row, currentVersionComboBox, newVersionComboBox):
        newVersionComboBox.clear()
        if currentVersionComboBox.currentText() == "N/A":
            newVersionComboBox.addItems(["v001"])
            newVersionComboBox.setCurrentIndex(0)
        else:
            try:
                verNum = int(currentVersionComboBox.currentText()[1:])
                newVersion = verNum + 1
                newVersionList = []
                for num in range(newVersion):
                    versions = 'v{:03d}'.format(num + 1)
                    newVersionList.append(versions)
                newVersionComboBox.addItems(newVersionList)
                newVersionComboBox.setCurrentIndex(len(newVersionList)-1)
            except ValueError:
                    pass

    def cellClickedGrabShape(self, row, column):
        if column == 0:
            current_row = self.tableWidget.currentRow()
            current_column = self.tableWidget.currentColumn()
            cell_value = self.tableWidget.item(current_row, current_column).text()
            pm.select(cell_value)
        else:
            pass

    def warningPopup(self, message):
        selectionWarningDialog = QtWidgets.QMessageBox()
        with open("{}/dark.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            selectionWarningDialog.setStyleSheet(fh.read())
        selectionWarningDialog.setText(message)
        selectionWarningDialog.setWindowTitle("Warning")
        selectionWarningDialog.exec_()
        print (message)

    #funtion to check if folder exists, if not create it
    def createDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory '{path}' created.")
        else:
            print(f"Directory '{path}' already exists.")

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