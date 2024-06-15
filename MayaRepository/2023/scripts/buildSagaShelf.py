import shelfCreate
import maya.cmds as mc
import maya.mel as mm
import genTools.genUtils as genUtils

from importlib import reload
import filePaths

def blankCMD():
    return

def centerPivotCMD():
    genUtils.centerPivot()

def freezeTransformsCMD():
    genUtils.freezeTransforms()

def deleteHistoryCMD():
    genUtils.deleteHistory()

def deleteUnconnectedShapesCMD():
    genUtils.deleteUnconnectedShapes()

def moveBACMD():
    genUtils.moveBA()

def moveToOriginCMD():
    import genTools.moveToOrigin
    genTools.moveToOrigin.moveToOrigin()

def movePivotBACMD():
    mm.eval('movePivotBA();')

def movePivotToOriginCMD():
    mm.eval('movePivotToOrigin();')

def combineObjectsCMD():
    genUtils.combineObjects()

def separateObjectsCMD():
    genUtils.separateObjects()

def UVEditorCMD():
    for panel in mc.getPanel(sty="polyTexturePlacementPanel") or []:
        mc.scriptedPanel(panel, e=True, to=True)

def cubeUVsCMD():
    import modellingTools.cubeUVs
    modellingTools.cubeUVs.applyCubeUVs()

def convertTextureUICMD():
    import textureTools.convertTextureUI
    textureTools.convertTextureUI.launch()

def cardGeneratorCMD():
    import modellingTools.cardGenerator
    modellingTools.cardGenerator.launch()

def cubinateCMD():
    import modellingTools.cubinate
    modellingTools.cubinate.cubinate()

def deleteUnknownNodesCMD():
    genUtils.deleteUnknownNodes()

def renameShaderToShapeNameCMD():
    import shadingTools.genShaderUtils
    shadingTools.genShaderUtils.renameShaderToShapeName()

def detachComponentsCMD():
    genUtils.detachComponents()

def detachDuplicateComponentsCMD():
    mm.eval('detachDuplicateComponents();')

def selectByPolycountCMD():
    genUtils.selectSame()

def selectByAngleCMD():
    if not mc.polySelectConstraint(query=True, ap=True) is True:
        mc.polySelectConstraint(ap=True, at=38)
    else:
        mc.polySelectConstraint(ap=False, at=0)

def separateByShadingGroupsCMD():
    import shadingTools.separateByShadingGroups
    shadingTools.separateByShadingGroups.main()

def splitShapesPerUDIMCMD():
    import textureTools.splitShapesPerUDIM
    textureTools.splitShapesPerUDIM.splitShapesPerUDIM()

def cometRenameCMD():
    mm.eval('cometRename();')

def selectNthEdgeCMD():
    mm.eval('polySelectEdgesEveryN "edgeRing" 2;')

def copyCurrentScenePathCMD():
    from PySide2 import QtGui
    maya_file = mc.file(sceneName=True, q=True)
    clip = QtGui.QClipboard()
    clip.setText(str(maya_file))

def randomVertColCMD():
    mm.eval('randomVertCol();')

def sortOutlinerCMD():
    mm.eval('sortOutliner();')

def toggleVertexColorDisplayCMD():
    import shadingTools.genShaderUtils
    reload(shadingTools.genShaderUtils)
    shadingTools.genShaderUtils.toggleVertexColorDisplay()

def createBlinnPerShapeCMD():
    import shadingTools.genShaderUtils
    reload(shadingTools.genShaderUtils)
    shadingTools.genShaderUtils.createBlinnPerShape()

def convertTextureUICMD():
    import textureTools.convertTextureUI
    textureTools.convertTextureUI.launch()

def createAssetDirUICMD():
    import assetTools.createAssetDirUI
    assetTools.createAssetDirUI.launch()

def createLocAtPivotCMD():
    genUtils.createLocAtPivot()

def extractVisGeoCMD():
    import modellingTools.extractVisGeo
    modellingTools.extractVisGeo.extractSelected()

def deleteDisplayLayersCMD():
    genUtils.deleteAllDisplayLayers()

def importMayaCMD():
    import genTools.importExportMaya
    genTools.importExportMaya.importAsset()

def exportMayaCMD():
    import genTools.importExportMaya
    genTools.importExportMaya.exportAsset()

def deleteAllNameSpacesCMD():
    genUtils.deleteAllNameSpaces()

def exportOBJCMD():
    import modellingTools.exportOBJ
    modellingTools.exportOBJ.launch()

def takeSnapshotCMD():
    import cameraTools.takeSnapshot
    cameraTools.takeSnapshot.snap(clipboard=True)

def DoraSkinWeightCMD():
    mm.eval('DoraSkinWeightImpExp();')

def mzCtrlCreatorCMD():
    import riggingTools.mz_ctrlCreator
    riggingTools.mz_ctrlCreator.buildWindow()

def copyShaderToObjectsCMD():
    import shadingTools.genShaderUtils
    reload(shadingTools.genShaderUtils)
    shadingTools.genShaderUtils.copyShaderToObjects()

def versionUpCurrentFileCMD():
    import genTools.versionFile
    genTools.versionFile.versionOpenMayaFile()

def pluginManagerCMD():
    import genTools.pluginManager
    genTools.pluginManager.launch()

def unlockAllNodesCMD():
    genUtils.unlockAllNodes()

def measureToolsCMD():
    mm.eval('source "measureTool.mel";')
    mm.eval('loadMeasureTool();')

def fastRetopoCMD():
    import modellingTools.retopoMultiple
    modellingTools.retopoMultiple.fastRetopoMultiple()

def setCurrentUVsToMap1CMD():
    genUtils.setCurrentUVsToMap1()

'''
BUILD SHELF
'''

def makeShelfAndButtons():
    iconPath = filePaths.mayaShelfIconPath
    slapFactoryShelf = shelfCreate.ShelfTool('STACK_SHELF', iconPath)

    slapFactoryShelf.createShelf()

    try:
        shelfSpacer01 = slapFactoryShelf.addShelfSpacer(iconImage='spacer.png')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        versionUpCurrentFileButton = slapFactoryShelf.shelfButton(versionUpCurrentFileCMD, 'VersionUp.png', 'Version up open Maya file')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        centerPivotButton = slapFactoryShelf.shelfButton(centerPivotCMD, 'centerPivot.png', 'Center Pivot')
        slapFactoryShelf.addMenu(centerPivotButton, 'Create Locator at selection', createLocAtPivotCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        freezeTransformsButton = slapFactoryShelf.shelfButton(freezeTransformsCMD, 'freezeTransforms.png', 'Freeze Transforms')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        deleteHistoryButton = slapFactoryShelf.shelfButton(deleteHistoryCMD, 'deleteHistory.png', 'Delete History')
        slapFactoryShelf.addMenu(deleteHistoryButton, 'Delete all unconnected shapes', deleteUnconnectedShapesCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        shelfSpacer02 = slapFactoryShelf.addShelfSpacer(iconImage='spacer.png')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        moveBAButton = slapFactoryShelf.shelfButton(moveBACMD, 'moveBA.png', 'Move B to A')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        moveToOriginButton = slapFactoryShelf.shelfButton(moveToOriginCMD, 'moveToOrigin.png', 'Move To Origin')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        shelfSpacer03 = slapFactoryShelf.addShelfSpacer(iconImage='spacer.png')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        movePivotBAButton = slapFactoryShelf.shelfButton(movePivotBACMD, 'movePivotBA.png', 'Move Pivot B to A')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        movePivotToOriginButton = slapFactoryShelf.shelfButton(movePivotToOriginCMD, 'movePivotToOrigin.png', 'Move Pivot To Origin')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        shelfSpacer04 = slapFactoryShelf.addShelfSpacer(iconImage='spacer.png')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        modellingButton = slapFactoryShelf.shelfButton(combineObjectsCMD, 'modelling.png', 'Modelling Tools')
        slapFactoryShelf.addMenu(modellingButton, '', blankCMD)
        slapFactoryShelf.addMenuSpacer(modellingButton, label='Commands')
        slapFactoryShelf.addMenu(modellingButton, 'Separate objects', separateObjectsCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Select Nth edge', selectNthEdgeCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Select by angle', selectByAngleCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Select same Obj by polycount', selectByPolycountCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Separate selected faces', detachComponentsCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Dulicate selected faces', detachDuplicateComponentsCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Separate shapes by shading groups', separateByShadingGroupsCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Separate shapes by UDIM', splitShapesPerUDIMCMD)
        slapFactoryShelf.addMenuSpacer(modellingButton, label='Tools')
        slapFactoryShelf.addMenu(modellingButton, 'Cubinate', cubinateCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Card generator', cardGeneratorCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Extract Vis Geo', extractVisGeoCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Fast Retopo Geo', fastRetopoCMD)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        riggingButton = slapFactoryShelf.shelfButton(blankCMD, 'rigging.png', 'Rigging Tools')
        slapFactoryShelf.addMenu(riggingButton, '', blankCMD)
        slapFactoryShelf.addMenuSpacer(riggingButton, label='Commands')
        slapFactoryShelf.addMenu(riggingButton, 'Dora Skin Weight Importer', DoraSkinWeightCMD)
        slapFactoryShelf.addMenu(riggingButton, 'MZ Ctrl Creator', mzCtrlCreatorCMD)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        UVToolsButton = slapFactoryShelf.shelfButton(UVEditorCMD, 'UVTools.png', 'UV Tools')
        slapFactoryShelf.addMenu(UVToolsButton, 'Cube UVs', cubeUVsCMD)
        slapFactoryShelf.addMenu(UVToolsButton, 'Set Current UVs to map1', setCurrentUVsToMap1CMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        textureToolsButton = slapFactoryShelf.shelfButton(convertTextureUICMD, 'textureTools.png', 'Texture Tools')
        slapFactoryShelf.addMenu(textureToolsButton, 'Convert texture UI', convertTextureUICMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        shaderToolsButton = slapFactoryShelf.shelfButton(blankCMD, 'shaderTools.png', 'Shader Tools')
        slapFactoryShelf.addMenu(shaderToolsButton, '', blankCMD)
        slapFactoryShelf.addMenuSpacer(shaderToolsButton, label='Commands')
        slapFactoryShelf.addMenu(shaderToolsButton, 'Rename shader to shape name', renameShaderToShapeNameCMD)
        slapFactoryShelf.addMenu(shaderToolsButton, 'Apply random vertex colour to selection', randomVertColCMD)
        slapFactoryShelf.addMenu(shaderToolsButton, 'Toggle vertex color display', toggleVertexColorDisplayCMD)
        slapFactoryShelf.addMenu(shaderToolsButton, 'Create Blinn for substance export', createBlinnPerShapeCMD)
        slapFactoryShelf.addMenu(shaderToolsButton, 'Copy shader to objects', copyShaderToObjectsCMD)
        slapFactoryShelf.addMenuSpacer(shaderToolsButton, label='Tools')
        slapFactoryShelf.addMenu(shaderToolsButton, 'Create shader from Substance painter export', buildShaderNetworkCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        cameraButton = slapFactoryShelf.shelfButton(blankCMD, 'cameraTools.png', 'Shader Tools')
        slapFactoryShelf.addMenu(cameraButton, 'Change camera background colour', changeCameraBackgroundColCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        genToolsButton = slapFactoryShelf.shelfButton(blankCMD, 'genTools.png', 'Shader Tools')
        slapFactoryShelf.addMenu(genToolsButton, '', blankCMD)
        slapFactoryShelf.addMenuSpacer(genToolsButton, label='Commands')
        slapFactoryShelf.addMenu(genToolsButton, 'Delete all unknown nodes', deleteUnknownNodesCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Unlock all nodes', unlockAllNodesCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Copy current scene path', copyCurrentScenePathCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Delete All Display Layers', deleteDisplayLayersCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Delete All NameSpaces', deleteAllNameSpacesCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Sort outliner', sortOutlinerCMD)
        slapFactoryShelf.addMenuSpacer(genToolsButton, label='Tools')
        slapFactoryShelf.addMenu(genToolsButton, 'Comet rename', cometRenameCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Create Asset Directories', createAssetDirUICMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Export Selected as OBJs', exportOBJCMD)
        slapFactoryShelf.addMenu(genToolsButton, 'Plugin manager', pluginManagerCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        techvisToolsButton = slapFactoryShelf.shelfButton(blankCMD, 'techvis.png', 'Techvis Tools')
        slapFactoryShelf.addMenu(techvisToolsButton, 'Measurement Tools', measureToolsCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        importExportMayaButton = slapFactoryShelf.shelfButton(blankCMD, 'copyPaste.png', 'Copy/Paste Selection')
        slapFactoryShelf.addMenu(importExportMayaButton, 'Copy selected', exportMayaCMD)
        slapFactoryShelf.addMenu(importExportMayaButton, 'Paste selected', importMayaCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        snapshotToolsButton = slapFactoryShelf.shelfButton(takeSnapshotCMD, 'snapshotTools.png', 'Take snapshot of viewport')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        shelfSpacer05 = slapFactoryShelf.addShelfSpacer(iconImage='spacer.png')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        unrealToolsButton = slapFactoryShelf.shelfButton(blankCMD, 'unrealTools.png', 'Unreal Tools')
        slapFactoryShelf.addMenu(unrealToolsButton, 'Save Setdec Assets', blankCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        shelfSpacer06 = slapFactoryShelf.addShelfSpacer(iconImage='spacer.png')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)