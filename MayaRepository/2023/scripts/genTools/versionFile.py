import os
import shutil
import glob
import maya.cmds as mc
from genTools.genUtils import warningPopup, viewportMessage
from pymel.core import saveAs

def CopyExistingFile(saveDir, fileName, fileExtension):

    LatestVersion, newVersion = GetVersionNumber(saveDir, fileName, fileExtension)

    existing_file = '{}{}_V{:03d}{}'.format(saveDir, fileName, LatestVersion, fileExtension)
    new_file = '{}{}_V{:03d}{}'.format(saveDir, fileName, newVersion, fileExtension)

    if not os.path.isfile(new_file):
        shutil.copy(existing_file, new_file)

    print (existing_file, new_file)

def VersionExistingFilePath(saveDir, fileName, fileExtension):

    LatestVersion, newVersion = GetVersionNumber(saveDir, fileName, fileExtension)

    existing_file = '{}{}_V{:03d}{}'.format(saveDir, fileName, LatestVersion, fileExtension)
    new_file = '{}{}_V{:03d}{}'.format(saveDir, fileName, newVersion, fileExtension)

    return existing_file, new_file

def GetVersionNumber(saveDir, fileName, fileExtension):

    versionNumList = []
    getAllMatching = glob.glob('{}\\{}_*{}'.format(saveDir,fileName, fileExtension), recursive=True)

    for filePath in getAllMatching:
        fileName, extension = os.path.splitext(filePath)
        fileNameStripped = fileName.rstrip('0123456789')
        VersionNumber = fileName[len(fileNameStripped):]

        # Is VersionNumber an integer?
        try:
                num = int(VersionNumber)
                versionNumList.append(num)
        except ValueError:
                print ("Input file path not correctly versioned, must follow nameV001 with 3 numbers")
    if len(versionNumList) == 0:
        LatestVersion = 1
        newVersion = 1
    else:
        LatestVersion = max(versionNumList)
        newVersion = LatestVersion + 1

    return LatestVersion, newVersion

def versionOpenMayaFile():
    maya_file = mc.file(sceneName=True, q=True)

    if not maya_file:
        warningPopup('Maya scene not currently saved')
    else:
        filePath, extension = os.path.splitext(maya_file)
        fileName = filePath.split("/")[-1]
        filePath = filePath.removesuffix(fileName)
        fileName = fileName.rsplit("_", 1)[0]

        existing_file, new_file = VersionExistingFilePath(filePath, fileName, extension)
        
        print ('Saving file.......{}'.format(new_file))

        viewportMessage('Saving file.......', new_file, '#00ff00')

        saveAs(new_file, f=True)