import os
import sys
import pymel.core as pm
import maya.cmds as mc
import subprocess
from genTools.genUtils import warningPopup
from PySide2 import QtGui, QtWidgets, QtCore
from importlib import reload
import shutil
import json
import filePaths

SHOWDRIVE = filePaths.libDir + "megascansLib/convertedSetDec/"
IMPATH = '"C:\\Program Files\\Autodesk\Maya2023\\bin\\magick.exe"'

parameterList = {
    'USDPreviewMaterial': {
        'diffuse': {'suffix': 'Diffuse', 'mayaParameter': 'diffuseColor', 'fileNodeParameter': 'outColor'},
        'emissive': {'suffix': 'Emissive', 'mayaParameter': 'emissiveColor', 'fileNodeParameter': 'outColor'},
        'ao': {'suffix': 'AO', 'mayaParameter': 'occlusion', 'fileNodeParameter': 'outAlpha'},
        'opacity': {'suffix': 'Opacity.', 'mayaParameter': 'opacity', 'fileNodeParameter': 'outAlpha'},
        'metallic': {'suffix': 'Metallic', 'mayaParameter': 'metallic', 'fileNodeParameter': 'outAlpha'},
        'roughness': {'suffix': 'Roughness', 'mayaParameter': 'roughness', 'fileNodeParameter': 'outAlpha'},
        'normal': {'suffix': 'Normal', 'mayaParameter': 'normal', 'fileNodeParameter': 'outColor'},
        'subsurface': {'suffix': 'Translucency', 'mayaParameter': 'clearcoat', 'fileNodeParameter': 'outAlpha'},
        'displacement': {'suffix': 'Displacement', 'mayaParameter': 'displacement', 'fileNodeParameter': 'outAlpha'}
    },
    'MegascansStandardSurface': {
        'diffuse': {'suffix': 'Albedo', 'mayaParameter': 'baseColor'},
        'emissive': {'suffix': 'Emissive', 'mayaParameter': 'emissionColor'},
        'ao': {'suffix': 'AO', 'mayaParameter': 'baseColor'},
        'opacity': {'suffix': 'Opacity', 'mayaParameter': 'opacity'},
        'metallic': {'suffix': 'Metallic', 'mayaParameter': 'metalness'},
        'roughness': {'suffix': 'Roughness', 'mayaParameter': 'specularRoughness'},
        'normal': {'suffix': 'Normal', 'mayaParameter': 'normalCamera'},
        'subsurface': {'suffix': 'Translucency', 'mayaParameter': 'subsurfaceColor'}
    }
}

class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(filePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.resize(400, 50)
        self.setWindowTitle('Convert Megascans Assets to Set Dec')
        self.setFocus()
        self.center()
        self.show()

        # button widget
        self.convertStandarAssetButton = QtWidgets.QPushButton('Convert Standard Asset(s)', self)
        self.convertStandarAssetButton.clicked.connect(self.ConvertStandard)

        # button widget
        self.convertPlantAssetButton = QtWidgets.QPushButton('Convert Plant Asset(s)', self)
        self.convertPlantAssetButton.clicked.connect(self.convertPlant)

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.convertStandarAssetButton, 0, 0)
        self.grid.addWidget(self.convertPlantAssetButton, 1, 0)
        self.setLayout(self.grid)

    def showFileDialog(self):
        initialDir = filePaths.downloadsFolder
        options = QtWidgets.QFileDialog.Options()
        fileFilter = "USD Files (*.usd *.usda *.usdz);;All Files (*)"
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                "Open USD File",
                                                initialDir,
                                                fileFilter,
                                                options=options)
        if filePath:
            # Set the selected file path in the QLineEdit
            self.USDFilePath.setText(filePath)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when import button is pressed
    def ConvertStandard(self):
        shapeList = pm.ls(sl=1)
        for shape in shapeList:
            shaderDict = self.getTextureDictFromMegascans(shape)
            assetName, newTexturePaths = self.processTextures(shaderDict, "Standard")
            self.buildUSDPreviewMat(shape, assetName, newTexturePaths, "Standard")

    # definition called when export button is pressed
    def convertPlant(self):
        shapeList = pm.ls(sl=1)
        for shape in shapeList:
            shaderDict = self.getTextureDictFromMegascans(shape)
            assetName, newTexturePaths = self.processTextures(shaderDict, "Plant")
            self.buildUSDPreviewMat(shape, assetName, newTexturePaths, "Plant")

    def getTextureDictFromMegascans(self, megascanAsset):
        megascansObject = pm.PyNode(megascanAsset)
        shaderList = []
        #get a list of all shaders attached to shape
        megascansObjectShapeNode = megascansObject.getShape()
        getShadingGroups = megascansObjectShapeNode.shadingGroups()
        megascansObjectShaders = pm.ls(pm.listConnections(getShadingGroups), materials=True)
        for shader in megascansObjectShaders:
            shaderList.append(shader)
        pubTexturedict = {}
        #loop through attached shaders and get all textures connected to materials
        for shader in set(shaderList):
            pubTexturedict[shader] = {}
            for parameter in parameterList.get('MegascansStandardSurface'):
                pubTexturedict[shader][parameter] = {}
                try:
                    mayaParameterName = (parameterList.get('MegascansStandardSurface').get(parameter).get('mayaParameter'))
                    megascansSuffixName = (parameterList.get('MegascansStandardSurface').get(parameter).get('suffix'))
                    fileNode = pm.listConnections('{}.{}'.format(shader, mayaParameterName))
                    if parameter in ('diffuse', 'ao'):
                        fileNode = pm.listConnections('{}.{}'.format(shader, 'baseColor'))
                        if fileNode[0].nodeType() == 'layeredTexture':
                            secondaryNodes = pm.listConnections(fileNode[0])
                            for node in secondaryNodes:
                                if node.nodeType() == 'file':
                                    if node.endswith("{}".format(megascansSuffixName.title())):
                                        texturePath = node.fileTextureName.get()
                                        pubTexturedict[shader][parameter] = texturePath
                        else:
                            if parameter == 'diffuse':
                                texturePath = fileNode[0].fileTextureName.get()
                                pubTexturedict[shader][parameter] = texturePath
                            if parameter == 'ao':
                                texturePath = None
                                pubTexturedict[shader][parameter] = texturePath

                    if parameter in ('roughness', 'normal'):
                        secondaryNode = pm.listConnections('{}.{}'.format(fileNode[0], 'input'))
                        texturePath = secondaryNode[0].fileTextureName.get()
                        pubTexturedict[shader][parameter] = texturePath
                    if parameter in ('emissive', 'opacity', 'metallic', 'subsurface'):
                        texturePath = fileNode[0].fileTextureName.get()
                        pubTexturedict[shader][parameter] = texturePath
                except:
                    texturePath = None
                    pubTexturedict[shader][parameter] = texturePath
            return pubTexturedict

    def processTextures(self, shaderDict, assetType):
            origTexList = [texture for params in shaderDict.values() for texture in params.values() if texture]
            if assetType == "Standard":
                texBaseDir = os.path.dirname(origTexList[0])
                assetName, jsonPath = self.getAssetNameFromJson(texBaseDir)
            if assetType == "Plant":
                texBaseDir = os.path.dirname(os.path.dirname(os.path.dirname(origTexList[0])))
                print (texBaseDir)
                assetName, jsonPath = self.getAssetNameFromJson(texBaseDir)
                print (assetName, jsonPath)
            newMegascanDir = "{}/{}".format(SHOWDRIVE, assetName)
            self.createDir(newMegascanDir)

            shutil.copy(jsonPath, newMegascanDir)

            newTexturePaths = []
            for parameter in parameterList.get('MegascansStandardSurface'):
                mayaParameterName = (parameterList.get('MegascansStandardSurface').get(parameter).get('mayaParameter'))
                megascansSuffixName = (parameterList.get('MegascansStandardSurface').get(parameter).get('suffix'))
                for origTexPath in origTexList:
                    if megascansSuffixName in origTexPath:
                        parameterName = parameter.capitalize()
                        if parameter == 'ao':
                            parameterName = parameter.upper()
                        newTexturePath = "{}/T_M_{}_{}.1001.png".format(newMegascanDir, assetName, parameterName)
                        newTexturePaths.append(newTexturePath)
                        newTexturePathcmd = '{} "{}" "{}"'.format(IMPATH, origTexPath, newTexturePath)
                        print (newTexturePathcmd)
                        subprocess.check_output(newTexturePathcmd, shell=True)

            return assetName, newTexturePaths

    def buildUSDPreviewMat(self, shape, assetName, texPaths, assetType):
        shapeObject = pm.PyNode(shape)

        material_name = "M_{}".format(assetName)
        if not pm.objExists(material_name):
            material_shader = pm.shadingNode('usdPreviewSurface', asShader=True, name=material_name)
            material_sg = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name="{}_SG".format(material_name))
            pm.connectAttr("{}.outColor".format(material_name), "{}.surfaceShader".format(material_sg), force=True)

            # Create and connect textures
            for texPath in texPaths:
                fileName = texPath.split("/")[-1]
                fileNameOnly = fileName.split(".1001.png")[0]
                fileNameParameter = fileName.split(".1001.png")[0].split("_")[-1]
                shaderConnectionAttr = parameterList.get('USDPreviewMaterial').get(fileNameParameter.lower()).get('mayaParameter')
                fileNodeConnectionAttr = parameterList.get('USDPreviewMaterial').get(fileNameParameter.lower()).get('fileNodeParameter')
                fileNode = pm.shadingNode('file', asTexture=True)
                fileNode.rename("{}".format(fileNameOnly))
                pm.setAttr("{}.fileTextureName".format(fileNode), texPath, type="string")
                pm.connectAttr("{}.{}".format(fileNode, fileNodeConnectionAttr), "{}.{}".format(material_shader, shaderConnectionAttr), force=True)

            # Assign the material to shape
            pm.sets(material_sg, edit=True, forceElement=shapeObject)
        else:
            print ("Found a material with the same name {} please change this before running".format(material_name))
        #try to rename the shape to the newly converted megascans name
        if assetType == "Standard":
            shapeObject.rename(assetName)
        if assetType == "Plant":
            if shapeObject.endswith("_LOD0"):
                shapeObject.rename(shapeObject[:-5])

    def getAssetNameFromJson(self, megascansDir):
        for file in os.listdir(megascansDir):
            if file.endswith('.json'):
                jsonPath = megascansDir + '\\' + file
                print ('json found reading data.. {0}'.format(jsonPath))
                with open(r'{0}'.format(jsonPath)) as json_file:
                    data = json.load(json_file)
                    try:
                        assetName = data['name']
                        assetName = assetName.replace(" ", "")
                        assetName = assetName.replace("-", "")
                        ID = data['id']
                        return "{}_{}".format(assetName, ID), jsonPath
                    except:
                        continue

    #funtion to check if folder exists, if not create it
    def createDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory '{path}' created.")
        else:
            print(f"Directory '{path}' already exists.")

# definition to open UI

def launch():
     global win
     win = MainWindow()
     win.raise_()
     win.activateWindow()
     win.show()