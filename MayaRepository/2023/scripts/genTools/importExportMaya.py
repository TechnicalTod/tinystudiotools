import maya.cmds as mc

from importlib import reload
import mayaFilePaths
reload(mayaFilePaths)

tempFilePath = mayaFilePaths.downloadsFolder + 'tempExportImport.ma'

print (tempFilePath)

def importAsset():
    mc.file(tempFilePath, i=True, type="mayaAscii", mergeNamespacesOnClash=False)

def exportAsset():
    mc.file(tempFilePath, force=True, options="v=0;", type="mayaAscii", pr=True, es=True)