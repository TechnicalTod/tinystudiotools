from PySide6 import QtGui, QtWidgets, QtCore
import pymel.core as pm
import maya.mel as mm
import maya.cmds as mc
import json
import os
from genTools.uiUtils import load_qss
import mayaFilePaths
import maya.OpenMayaUI as OMUI
import shiboken6


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Get Maya's main window
        mayaWin = OMUI.MQtUtil.mainWindow()
        self.mayaWin = shiboken6.wrapInstance(int(mayaWin), QtWidgets.QWidget)

        # Parent your window to Maya's main window
        self.setParent(self.mayaWin)
        self.setWindowFlags(QtCore.Qt.Window)
        self.initUI()

    def initUI(self):
        # window prefs
        self.setStyleSheet(load_qss("dark.qss"))
        self.setWindowTitle("Publish Shot For Unreal")
        self.setFocus()
        self.center()
        self.show()
        self.setGeometry(100, 100, 500, 500)

        # window layout setup
        self.createWidgets()
        self.connectLayout()

    # sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def createWidgets(self):
        self.treeView = QtWidgets.QTreeView()
        self.refreshButton = QtWidgets.QPushButton("Refresh")
        self.removeButton = QtWidgets.QPushButton("Remove Selected")
        self.clearButton = QtWidgets.QPushButton("Clear All")
        self.openFolderButton = QtWidgets.QPushButton("Open publish dir")
        self.publishButton = QtWidgets.QPushButton("Publish Shot")

        # Set custom context menu
        self.openFolderButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.openFolderButton.customContextMenuRequested.connect(self.showContextMenu)

        # adjust the import button style sheet
        self.publishButton.setStyleSheet(load_qss("importButton.qss"))
        self.openFolderButton.setStyleSheet(load_qss("openButton.qss"))

        # Set up the model for QTreeView
        self.model = QtGui.QStandardItemModel()
        self.treeView.setModel(self.model)
        self.treeView.setHeaderHidden(True)  # Hide the default header

        # Populate the tree view with groups
        self.populatePublishTree()

    def showContextMenu(self, position):
        contextMenu = QtWidgets.QMenu(self)
        copyAction = contextMenu.addAction("Copy Scene Desc Json Path")
        copyAction.triggered.connect(self.copyPathToClipboard)
        contextMenu.exec_(QtGui.QCursor.pos())

    def copyPathToClipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(str(self.getSceneDescriptionPath()))

    # connect and populate the layout
    def connectLayout(self):
        self.treeView.clicked.connect(self.itemGrabShape)
        self.refreshButton.clicked.connect(self.populatePublishTree)
        self.removeButton.clicked.connect(self.removeSelectedItems)
        self.publishButton.clicked.connect(self.collectPublishData)
        self.openFolderButton.clicked.connect(self.getExportDir)
        self.clearButton.clicked.connect(self.clearList)

        buttonLayout = QtWidgets.QGridLayout()
        buttonLayout.addWidget(self.refreshButton, 0, 0)
        buttonLayout.addWidget(self.removeButton, 1, 0)
        buttonLayout.addWidget(self.clearButton, 2, 0)

        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.setRowStretch(1, 1)
        mainLayout.addWidget(self.treeView, 0, 0, 5, 4)
        mainLayout.addLayout(buttonLayout, 0, 5, 1, 1)
        mainLayout.addWidget(self.openFolderButton, 3, 5, alignment=QtCore.Qt.AlignBottom)
        mainLayout.addWidget(self.publishButton, 4, 5, alignment=QtCore.Qt.AlignBottom)

    def populatePublishTree(self):
        self.clearList()
        # Create group nodes with icons
        self.cameraGroup = QtGui.QStandardItem(
            QtGui.QIcon("{}snapshotTools.png".format(mayaFilePaths.mayaShelfIconPath)), "Cameras"
        )
        self.puppetGroup = QtGui.QStandardItem(
            QtGui.QIcon("{}centerPivot.png".format(mayaFilePaths.mayaShelfIconPath)), "Puppets"
        )
        self.shotInfoGroup = QtGui.QStandardItem(
            QtGui.QIcon("{}techvis.png".format(mayaFilePaths.mayaShelfIconPath)), "Shot Info"
        )
        self.extraInfoGroup = QtGui.QStandardItem(
            QtGui.QIcon("{}modelling.png".format(mayaFilePaths.mayaShelfIconPath)), "Extra Info"
        )
        self.makeItemBold(
            [self.cameraGroup, self.puppetGroup, self.shotInfoGroup, self.extraInfoGroup],
            QtCore.Qt.black,
        )
        # Add top group nodes to the model
        self.model.appendRow(self.cameraGroup)
        self.model.appendRow(self.puppetGroup)
        self.model.appendRow(self.shotInfoGroup)
        self.model.appendRow(self.extraInfoGroup)
        # Expand all groups
        self.treeView.expandAll()
        # populate each list based on current scene
        self.getCameraData()
        self.getPuppetData()
        self.getShotInfo()
        self.getExtraInfo()

    def getCameraData(self):
        cameraInfoDict = {}

        # Get all cameras in the scene, skipping default cameras
        cameras = pm.ls(type="camera", long=True)
        for camera in cameras:
            cameraShape = camera
            cameraName = camera.getParent()
            if cameraName not in ("persp", "back", "front", "side", "top"):
                cameraInfoDict[cameraName] = {}

                # Get focal length
                cameraInfoDict[cameraName]["focalLength"] = cameraShape.attr("focalLength").get()

                # Convert film aperture from inches to millimeters
                cameraInfoDict[cameraName]["horizontalFilmAperture"] = round(
                    cameraShape.attr("horizontalFilmAperture").get() * 25.4, 3
                )
                cameraInfoDict[cameraName]["verticalFilmAperture"] = round(
                    cameraShape.attr("verticalFilmAperture").get() * 25.4, 3
                )

                # Fetch image plane data
                imagePlaneList = pm.listConnections(cameraShape, type="imagePlane")
                if not imagePlaneList:
                    cameraInfoDict[cameraName]["ImagePlate"] = ""
                else:
                    try:
                        imagePlanePath = pm.getAttr("{}.imageName".format(imagePlaneList[0]))
                        cameraInfoDict[cameraName]["ImagePlate"] = imagePlanePath
                    except:
                        cameraInfoDict[cameraName]["ImagePlate"] = ""

        # loop through dictionary to populate shot info
        for info in cameraInfoDict:
            titleItem = QtGui.QStandardItem("{}".format(info))
            self.makeItemBold([titleItem], QtCore.Qt.white)
            self.cameraGroup.appendRow(titleItem)
            secondaryItem = QtGui.QStandardItem(str(cameraInfoDict.get(info)))
            titleItem.appendRow(secondaryItem)

    def getPuppetData(self):
        puppetInfoDict = {}

        customPuppetAttrs = [
            "assetType",
            "assetName",
            "variant",
            "version",
            "rootJointName",
            "visGeoGroupName",
            "version",
        ]
        # Get all puppets in scene
        puppets = [node for node in pm.ls(type="transform") if node.hasAttr("rootJointName")]
        for puppet in puppets:
            puppetInfoDict[puppet] = {}
            for attr in customPuppetAttrs:
                puppetInfoDict[puppet][attr] = puppet.attr(attr).get()

        # loop through dictionary to populate shot info
        for info in puppetInfoDict:
            titleItem = QtGui.QStandardItem("{}".format(info))
            self.makeItemBold([titleItem], QtCore.Qt.white)
            self.puppetGroup.appendRow(titleItem)
            secondaryItem = QtGui.QStandardItem(str(puppetInfoDict.get(info)))
            titleItem.appendRow(secondaryItem)

    def getShotInfo(self):
        shotNumberFromPath = None
        projectNameFromPath = None
        versionNumberFromPath = None
        ShotInfoDict = {}

        # Get shot number from open maya file
        try:
            currentFileName = mc.file(sceneName=True, q=True)
            shotNumberFromPath = currentFileName.split("/")[-5]
            projectNameFromPath = currentFileName.split("/")[-9]
            versionNumberFromPath = currentFileName.split("/")[-1].split("_")[-1].split(".")[0]
        except:
            print("You are not in a saved shot scene")

        ShotInfoDict["Project"] = "{}".format(projectNameFromPath)
        ShotInfoDict["Shot Number"] = "{}".format(shotNumberFromPath)
        ShotInfoDict["Version"] = "{}".format(versionNumberFromPath)

        # timeline details
        startFrame = pm.playbackOptions(query=True, min=True)
        endFrame = pm.playbackOptions(query=True, max=True)
        ShotInfoDict["Timeline"] = {}
        ShotInfoDict["Timeline"]["Start Frame"] = startFrame
        ShotInfoDict["Timeline"]["End Frame"] = endFrame
        # FPS details
        ShotInfoDict["FPS"] = mm.eval("currentTimeUnitToFPS()")

        # loop through dictionary to populate shot info
        for info in ShotInfoDict:
            titleItem = QtGui.QStandardItem("{}".format(info))
            self.makeItemBold([titleItem], QtCore.Qt.white)
            self.shotInfoGroup.appendRow(titleItem)
            secondaryItem = QtGui.QStandardItem(str(ShotInfoDict.get(info)))
            titleItem.appendRow(secondaryItem)
            titleItemIndex = self.model.indexFromItem(titleItem)
            self.treeView.expand(titleItemIndex)

    def getExtraInfo(self):
        # Placeholder for now
        # We can add things like animated abjects etc
        item = QtGui.QStandardItem("N/A")
        self.extraInfoGroup.appendRow(item)

    # Clear all existing items
    def clearList(self):
        self.model.clear()

    # Get selected items and remove them from the model
    def removeSelectedItems(self):
        # Get the selected item from the tree view
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        # Ensure the selected item is not a top-level node and check if selection in Shot Info
        if index.parent().isValid():
            currentItem = self.model.itemFromIndex(index.parent())
            while currentItem.parent():
                currentItem = currentItem.parent()
            parent = currentItem.text()
            if parent in ("Shot Info"):
                pass
            else:
                self.model.removeRow(index.row(), index.parent())

    def exportInitialTreeToJson(self):
        def serializeTree(item):
            # Attempt to parse item's text as a JSON object
            try:
                # This will succeed if item.text() is a JSON-like string
                item_content = json.loads(item.text().replace("'", '"'))
            except ValueError:
                # If it's not a JSON-like string, just use the raw text
                item_content = item.text()

            if item.rowCount() > 0:
                # If the item has children, recursively serialize them
                children = [serializeTree(item.child(i)) for i in range(item.rowCount())]
                # Return the node with its children
                return {item_content if isinstance(item_content, dict) else item.text(): children}
            else:
                # If no children, return the content directly
                return item_content

        root = self.model.invisibleRootItem()
        data = [serializeTree(root.child(i)) for i in range(root.rowCount())]
        jsonData = json.dumps(data, indent=4)
        return jsonData

    def getExportDir(self):
        jsonData = json.loads(self.exportInitialTreeToJson())
        for item in jsonData:
            if "Shot Info" in item:
                for info in item["Shot Info"]:
                    if "Shot Number" in info:
                        shotNumber = info["Shot Number"][0]
                    if "Version" in info:
                        versionNumber = info["Version"][0]
                    if "Project" in info:
                        project = info["Project"][0]
        # Base directory for all shots
        baseDir = "Y:/{}/episodes/".format(project)
        # Extract episode from the shot number
        episode = shotNumber.split("_")[
            0
        ]  # Assumes the first three characters represent the episode
        seq = "{}_{}".format(shotNumber.split("_")[0], shotNumber.split("_")[1])
        # Construct directory path
        publishDir = "{}/{}/{}/publish/unreal/sceneDescription/{}/".format(
            episode, seq, shotNumber, versionNumber
        )
        fullPath = "{}{}".format(baseDir, publishDir)
        os.startfile(fullPath)

    def getSceneDescriptionPath(self):
        jsonData = json.loads(self.exportInitialTreeToJson())
        for item in jsonData:
            if "Shot Info" in item:
                for info in item["Shot Info"]:
                    if "Shot Number" in info:
                        shotNumber = info["Shot Number"][0]
                    if "Version" in info:
                        versionNumber = info["Version"][0]
                    if "Project" in info:
                        project = info["Project"][0]
        sceneDescriptionPath = self.buildExportPath(
            "ShotDesciption", project, shotNumber, versionNumber, ".json"
        )
        return sceneDescriptionPath

    def collectPublishData(self):
        jsonData = json.loads(self.exportInitialTreeToJson())
        for item in jsonData:
            if "Shot Info" in item:
                for info in item["Shot Info"]:
                    if "Shot Number" in info:
                        shotNumber = info["Shot Number"][0]
                    if "Version" in info:
                        versionNumber = info["Version"][0]
                    if "Project" in info:
                        project = info["Project"][0]
        # Grab all cameras and puppets in json and send for bake and export
        # Then add the export paths into the json
        try:
            cameraList = jsonData[0]["Cameras"]
            newCameraList = []
            for cameraDict in cameraList:
                newCameraDict = {}
                for camera, attrs in cameraDict.items():
                    newCameraDict[camera] = {}
                    cameraExportPath = self.buildExportPath(
                        camera, project, shotNumber, versionNumber, ".fbx"
                    )
                    publishDict = self.processCamera(camera, cameraExportPath)
                    attrs[0].update(publishDict)
                    newCameraDict[camera] = attrs
        except Exception as e:
            print("No Cameras found in list:", e)
        try:
            puppetList = jsonData[1]["Puppets"]
            newPuppetList = []
            for puppetDict in puppetList:
                newPuppetDict = {}
                for puppet, attrs in puppetDict.items():
                    newPuppetDict[puppet] = {}
                    puppetExportPath = self.buildExportPath(
                        puppet.split(":")[0], project, shotNumber, versionNumber, ".fbx"
                    )
                    publishDict = self.processPuppet(puppet, puppetExportPath)
                    attrs[0].update(publishDict)
                    newPuppetDict[puppet] = attrs
        except Exception as e:
            print("No Puppets found in list:", e)

        # Export json file to pub dir
        jsonExportPath = self.buildExportPath(
            "ShotDesciption", project, shotNumber, versionNumber, ".json"
        )
        with open(jsonExportPath, "w") as json_file:
            json.dump(jsonData, json_file, indent=4)

    def processCamera(self, camName, exportPath):
        publishDict = {}
        publishDict["Export Path"] = {}
        publishDict["Export Path"] = exportPath

        # Duplicate the camera with input connections (includes animation)
        duplicatedCamera = pm.duplicate(camName, name=camName + "_UECam", un=True, ic=True)[0]

        # Get the current timeline range
        startFrame = pm.playbackOptions(query=True, minTime=True)
        endFrame = pm.playbackOptions(query=True, maxTime=True)

        # Bake the camera keys on the duplicated camera
        pm.bakeResults(
            duplicatedCamera,
            simulation=True,
            t=(startFrame, endFrame),
            sampleBy=1,
            oversamplingRate=1,
            disableImplicitControl=True,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=False,
            bakeOnOverrideLayer=False,
            minimizeRotation=True,
            controlPoints=False,
            shape=True,
        )

        pm.parent(duplicatedCamera, world=True)
        # Export the duplicated camera to FBX
        pm.select(duplicatedCamera, replace=True)
        pm.mel.FBXResetExport()
        pm.mel.FBXExport(file=exportPath, s=True)

        # Delete the duplicated camera
        pm.delete(duplicatedCamera)

        return publishDict

    def processPuppet(self, puppetName, exportPath):
        publishDict = {}
        publishDict["Export Path"] = {}
        publishDict["Export Path"] = exportPath

        # Duplicate the puppet with input connections (includes animation)
        duplicatedPuppet = pm.duplicate(
            puppetName, name=puppetName + "_puppetExport", un=True, ic=True
        )[0]
        try:
            # get root joint from published attrs and get list of all bakeable joints
            rootJoint = duplicatedPuppet.attr("rootJointName").get()
            allJoints = pm.listRelatives(rootJoint, allDescendents=True, type="joint")
            allJoints.append(rootJoint)

            # Get the current timeline range
            startFrame = pm.playbackOptions(query=True, minTime=True)
            endFrame = pm.playbackOptions(query=True, maxTime=True)

            # Bake the camera keys on the duplicated camera
            pm.bakeResults(
                allJoints,
                simulation=True,
                t=(startFrame, endFrame),
                sampleBy=1,
                oversamplingRate=1,
                disableImplicitControl=True,
                preserveOutsideKeys=True,
                sparseAnimCurveBake=False,
                removeBakedAttributeFromLayer=False,
                bakeOnOverrideLayer=False,
                minimizeRotation=True,
                controlPoints=False,
                shape=True,
            )

            pm.parent(rootJoint, world=True)
            pm.delete(duplicatedPuppet)

            pm.select(rootJoint, replace=True)
            pm.mel.FBXResetExport()
            pm.mel.FBXExport(file=exportPath, s=True)

            pm.delete(rootJoint)

            return publishDict
        except Exception as e:
            print(e)

    def buildExportPath(self, assetName, project, shotNumber, versionNumber, fileExtension):
        # Base directory for all shots
        baseDir = "Y:/{}/episodes/".format(project)
        # Extract episode from the shot number
        episode = shotNumber.split("_")[
            0
        ]  # Assumes the first three characters represent the episode
        seq = "{}_{}".format(shotNumber.split("_")[0], shotNumber.split("_")[1])
        # Construct directory path
        publishDir = "{}/{}/{}/publish/unreal/sceneDescription/{}/".format(
            episode, seq, shotNumber, versionNumber
        )
        self.createDir("{}{}".format(baseDir, publishDir))
        # Construct the file name using the new naming convention and file extension
        fileName = "{}_{}{}".format(assetName, versionNumber, fileExtension)
        # Complete path with file name
        fullPath = "{}{}{}".format(baseDir, publishDir, fileName)
        return fullPath

    # helper function to make certain items bold with argument to feed in a color
    def makeItemBold(self, items, color):
        for item in items:
            font = QtGui.QFont()
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QtGui.QBrush(color))

    # Called on item change, tries to select a shape if it corresponds to the items text
    def itemGrabShape(self, index: QtCore.QModelIndex):
        item = self.model.itemFromIndex(index)
        try:
            pm.select(item.text())
        except:
            pass

    # funtion to check if folder exists, if not create it
    def createDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory '{path}' created.")
        else:
            print(f"Directory '{path}' already exists.")


# Definition to open UI
def launch():
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()
