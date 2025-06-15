import os
import sys
import pymel.core as pm
import maya.cmds as mc
import subprocess
from genTools.genUtils import warningPopup
from PySide6 import QtGui, QtWidgets, QtCore
from importlib import reload
import shutil
import json
import mayaFilepaths

IMPATH = '"C:\Program Files\Autodesk\Maya2023\bin\magick.exe"'

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


def ConvertTextures():
    shapeList = pm.ls(sl=1)
    for shape in shapeList:
        shaderDict = getTextureDictFromSelected(shape)
        processTextures(shaderDict)
        # self.buildUSDPreviewMat(shape, assetName, newTexturePaths, "Standard")


def getTextureDictFromSelected(shape):
    selObject = pm.PyNode(shape)
    shaderList = []
    # get a list of all shaders attached to shape
    selObjectShapeNode = selObject.getShape()
    getShadingGroups = selObjectShapeNode.shadingGroups()
    selObjectShaders = pm.ls(pm.listConnections(getShadingGroups), materials=True)
    for shader in selObjectShaders:
        shaderList.append(shader)
    pubTexturedict = {}
    # loop through attached shaders and get all textures connected to materials
    for shader in set(shaderList):
        pubTexturedict[shader] = {}
        for parameter in parameterList.get("USDPreviewMaterial"):
            try:
                mayaParameterName = (
                    parameterList.get("USDPreviewMaterial").get(parameter).get("mayaParameter")
                )
                fileNode = pm.listConnections("{}.{}".format(shader, mayaParameterName))
                texturePath = fileNode[0].fileTextureName.get()
                texturePath = texturePath.replace("\\", "/")
                fileName = texturePath.split("/")[-1]
                fileNameSplit = fileName.split(".<UDIM>.png")[0]
                texturePath = texturePath.split(fileName)[0]
                for tex in os.listdir(texturePath):
                    if tex.endswith(".png"):
                        if fileNameSplit in tex:
                            print(texturePath + tex)
                            pubTexturedict[shader][parameter] = texturePath + tex
            except:
                print("No texture found for " + parameter)
    print(pubTexturedict)
    return pubTexturedict


def processTextures(shaderDict):
    for shaderName in shaderDict:
        print("Processing textures for shader . . . {}".format(shaderName))
        for parameter in shaderDict.get(shaderName):
            origTexPath = shaderDict.get(shaderName).get(parameter)
            texBaseDir = os.path.dirname(origTexPath)

            newParamString = parameter.capitalize()
            if parameter == "ao":
                newParamString = parameter.upper()
            newTexturePath = "{}/T_{}_{}.1001.png".format(texBaseDir, shaderName, newParamString)

            newTexturePathcmd = '{} "{}" "{}"'.format(IMPATH, origTexPath, newTexturePath)
            print(newTexturePathcmd)
            subprocess.check_output(newTexturePathcmd, shell=True)

            mayaParameterName = (
                parameterList.get("USDPreviewMaterial").get(parameter).get("mayaParameter")
            )
            fileNode = pm.listConnections("{}.{}".format(shaderName, mayaParameterName))
            print(fileNode)
            pm.setAttr("{}.fileTextureName".format(fileNode[0]), newTexturePath, type="string")
