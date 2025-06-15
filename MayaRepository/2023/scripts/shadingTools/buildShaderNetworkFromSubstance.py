from importlib import reload
from PySide6 import QtWidgets, QtGui
import genTools.genUtils as genUtils
from genTools.genUtils import warningPopup
import os
import subprocess
import json
import pymel.core as pm
import maya.cmds as mc
import mayaFilePaths

parameterList = {
    "USDPreviewMaterial": {
        "diffuse": {
            "suffix": "Diffuse",
            "mayaParameter": "diffuseColor",
            "fileNodeParameter": "outColor",
        },
        "emissive": {
            "suffix": "Emissive",
            "mayaParameter": "emissiveColor",
            "fileNodeParameter": "outColor",
        },
        "ao": {"suffix": "AO", "mayaParameter": "occlusion", "fileNodeParameter": "outAlpha"},
        "opacity": {
            "suffix": "Opacity.",
            "mayaParameter": "opacity",
            "fileNodeParameter": "outAlpha",
        },
        "metallic": {
            "suffix": "Metallic",
            "mayaParameter": "metallic",
            "fileNodeParameter": "outAlpha",
        },
        "roughness": {
            "suffix": "Roughness",
            "mayaParameter": "roughness",
            "fileNodeParameter": "outAlpha",
        },
        "normal": {"suffix": "Normal", "mayaParameter": "normal", "fileNodeParameter": "outColor"},
        "subsurface": {
            "suffix": "Translucency",
            "mayaParameter": "clearcoat",
            "fileNodeParameter": "outAlpha",
        },
        "displacement": {
            "suffix": "Displacement",
            "mayaParameter": "displacement",
            "fileNodeParameter": "outAlpha",
        },
    }
}


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(600, 50)
        self.setWindowTitle("Build shaders from Substance exports")
        self.setFocus()
        self.center()
        self.show()

        # tex field widget
        self.getFilePathTextures = QtWidgets.QLineEdit(self)
        self.getFilePathTextures.setPlaceholderText("Texture Directory")

        # button widget
        self.createShaderButton = QtWidgets.QPushButton("Build Shader Network(s)", self)
        self.createShaderButton.clicked.connect(self.buildNetwork)

        # Create the combo box for shader preset selection
        self.shaderPresetComboBox = QtWidgets.QComboBox(self)
        self.shaderPresetComboBox.addItems(["Standard"])

        browseButtoniconPath = mayaFilePaths.mayaShelfIconPath + "folder.png"
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon(browseButtoniconPath))
        self.browseButton.clicked.connect(self.showFileDialog)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.getFilePathTextures, 0, 0, 1, 3)
        self.grid.addWidget(self.browseButton, 0, 3, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Shader Preset:"), 1, 0, 1, 1)
        self.grid.addWidget(self.shaderPresetComboBox, 1, 1, 1, 3)
        self.grid.addWidget(self.createShaderButton, 2, 0, 1, 4)

        self.setLayout(self.grid)

    def showFileDialog(self):
        initialDir = mayaFilePaths.downloadsFolder
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            initialDir,
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        if dirPath:
            # Set the selected file path in the QLineEdit
            self.getFilePathTextures.setText(dirPath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def createShader(self, shaderName, shaderType="usdPreviewSurface"):
        newShader = mc.shadingNode(shaderType, name=shaderName, asShader=True)
        newSG = mc.sets(
            name="{}_SG".format(newShader), empty=True, renderable=True, noSurfaceShader=True
        )
        mc.connectAttr("{}.outColor".format(newShader), "{}.surfaceShader".format(newSG))
        mc.setAttr("{}.diffuseColor".format(shaderName), 1, 1, 1, type="double3")

        return newShader

    def findExistingShadersInScene(self, texSet):
        # Shader check to see if the shaders already exist in the scene
        shaderBaseName = "M_" + texSet
        try:
            shader = pm.ls(shaderBaseName, materials=True)
            shading_engines = shader[0].listConnections(type="shadingEngine")
            connected_shapes = pm.sets(shading_engines[0], query=True)
        except:
            shader = None
            connected_shapes = None

        return shader, connected_shapes

    def getTextureSetList(self, texturePath):
        textureSetList = []
        textureList = []

        for textureFilename in os.listdir(texturePath):
            if textureFilename.endswith(".db"):
                pass
            else:
                # Check if the filename starts with "M_"
                if not textureFilename.startswith("M_"):
                    # Warning for files not starting with "M_" and stop the function
                    warningPopup(
                        "Textures found with incorrect naming, all textures should start with 'M_'"
                    )
                    return

                # Further checks if it ends with ".png"
                if not textureFilename.endswith(".png"):
                    # Warning for non-png files
                    warningPopup("All textures in this directory should be '.png'")
                    return

                # Processing the valid texture filename
                strippedFilename = textureFilename[2:]
                baseName = strippedFilename.split("_")[0]
                textureSetList.append(baseName)
                fullTexturePath = "{}/{}".format(texturePath, textureFilename)
                textureList.append(fullTexturePath)

        return textureSetList, textureList

    def buildNetwork(self):
        presetName = self.shaderPresetComboBox.currentText()
        texturePath = self.getFilePathTextures.text()
        textureSetList, textureList = self.getTextureSetList(texturePath)

        print(
            "found {} texture sets in the output directory.......".format(
                len((set(textureSetList)))
            )
        )

        for texSet in set(textureSetList):
            print("Processing Texture set ........M_" + texSet)

            existingShader, connected_shapes = self.findExistingShadersInScene(texSet)

            if not existingShader:
                print(
                    "No shader or connected shapes found for this material, please connect the shader manually"
                )
                shader = self.createShader("M_{0}".format(texSet))
                print(shader)
            else:
                pm.delete(existingShader)
                print("Existing shader found attempting to connect to existing objects")
                if not connected_shapes:
                    print("Shader found but cannot find any connected shapes")
                shader = self.createShader("M_{0}".format(texSet))
                shadingGroup = mc.listConnections(shader, type="shadingEngine")
                pm.sets(shadingGroup[0], e=True, forceElement=connected_shapes)
                print(shader)

            # Create and connect textures
            for texPath in textureList:
                fileName = texPath.split("/")[-1]
                if texSet in fileName:
                    try:
                        print(fileName)
                        fileNameOnly = fileName.split(".1001.png")[0]
                        fileNameParameter = fileName.split(".1001.png")[0].split("_")[-1]
                        shaderConnectionAttr = (
                            parameterList.get("USDPreviewMaterial")
                            .get(fileNameParameter.lower())
                            .get("mayaParameter")
                        )
                        fileNodeConnectionAttr = (
                            parameterList.get("USDPreviewMaterial")
                            .get(fileNameParameter.lower())
                            .get("fileNodeParameter")
                        )
                        fileNode = pm.shadingNode("file", asTexture=True)
                        fileNode.rename("{}".format(fileNameOnly))
                        pm.setAttr("{}.fileTextureName".format(fileNode), texPath, type="string")
                        pm.connectAttr(
                            "{}.{}".format(fileNode, fileNodeConnectionAttr),
                            "{}.{}".format(shader, shaderConnectionAttr),
                            force=True,
                        )
                    except:
                        pass


# definition to open UI


def launch():
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()


launch()
