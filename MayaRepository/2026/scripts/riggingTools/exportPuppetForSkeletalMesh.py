import pymel.core as pm
import maya.cmds as mc
import os
import shutil

exportNodeNames = ['root_joint', 'visGeo']

#Function to extract and clean up puppet based in groupings for export to Unreal
def exportRigForUnreal(assetPath):
    versionNumber = assetPath.split("/")[-1]
    assetName = assetPath.split("/")[-2]
    #These group names are strictly required for export task to complete
    parentList = []
    #loop through nodes and parent to world
    for node in exportNodeNames:
        nodeParent = pm.listRelatives(node, p=1)[0]
        parentList.append(nodeParent)
        pm.parent(node, world=1)
    #delete all constraints in scene
    allConstraints = pm.ls(type="constraint")
    pm.delete(allConstraints, parentList)
    #Select remaining top nodes for export
    pm.select(exportNodeNames)
    #debugging log
    print (assetPath.split("/"))
    print ("assetPath", assetPath)
    print ("assetName", assetName)
    print ("versionNumber", versionNumber)
    #Build fbx export directory
    fbxDestinationBasePath = assetPath + "/UnrealExport"
    createDir(fbxDestinationBasePath)
    fbxDestinationPath = fbxDestinationBasePath + "/{}_ExportedRigForUnreal_{}".format(assetName, versionNumber)
    #FBX export with settings
    pm.mel.FBXResetExport()
    pm.mel.FBXExportSmoothingGroups(v=True)
    pm.mel.FBXExport(file=fbxDestinationPath, s=True)

def exportTextureForUnreal(assetPath):
    shaderList = []
    #get a list of all shaders attached to visGeo
    for shape in pm.listRelatives('visGeo'):
        getShapeNode = shape.getShape()
        getShadingGroups = getShapeNode.shadingGroups()
        getShader = pm.ls(pm.listConnections(getShadingGroups), materials=True)
        for shader in getShader:
            shaderList.append(shader)
    pubTextureList = []
    #loop through attached shaders and get all textures connected to materials
    for shader in set(shaderList):
        fileNodes = pm.listConnections(shader, type="file")
        for fileNode in fileNodes:
            texturePath = pm.getAttr(fileNode + ".fileTextureName")
            fileName = texturePath.split("/")[-1]
            fileNameSplit = fileName.split(".<UDIM>.png")[0]
            texturePath = texturePath.split(fileName)[0]
            for pubTex in os.listdir(texturePath):
                if fileNameSplit in pubTex:
                    pubTextureList.append(texturePath + pubTex)
    #build export directory
    textureDestinationPath = assetPath + "/tex"
    createDir(textureDestinationPath)
    #copy all textures into the publish folder
    for texture in pubTextureList:
        shutil.copy(texture, textureDestinationPath)

#funtion to check if folder exists, if not create it
def createDir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' created.")
    else:
        print(f"Directory '{path}' already exists.")

def checkNodesExist(nodeList):
    return all(pm.objExists(node_name) for node_name in nodeList)

def main():
    #do a quick check to see if the export groups exist, if not stop running
    if checkNodesExist(exportNodeNames):
        print("All export nodes exist. Exporting.")
        #Run puppet export and texture localisation for Unreal import process
        currentFilePath = mc.file(sceneName=True, q=True)
        currentFileName = mc.file(sceneName=True, q=True, shortName=True)
        exportRigForUnreal(currentFilePath.split(currentFileName)[0][:-1])
        exportTextureForUnreal(currentFilePath.split(currentFileName)[0][:-1])
    else:
        print("One or more export nodes do not exist. Aborting. . . ")