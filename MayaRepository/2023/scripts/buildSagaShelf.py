import shelfCreate
import maya.cmds as mc
import maya.mel as mm
import genTools.genUtils as genUtils
import mayaFilePaths

def blankCMD():
    return

'''ASSET TOOLS'''

def createAssetDirUICMD():
    import assetTools.createAssetDirUI
    assetTools.createAssetDirUI.launch()

def loadTunnelCMD():
    import assetTools.TunnelUi
    assetTools.TunnelUi.openWindow()

'''CAMERA'''

def takeSnapshotCMD():
    import cameraTools.takeSnapshot
    cameraTools.takeSnapshot.snap(clipboard=True)

'''GEN TOOLS AND UTILS'''

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

def combineObjectsCMD():
    genUtils.combineObjects()

def separateObjectsCMD():
    genUtils.separateObjects()

def deleteUnknownNodesCMD():
    genUtils.deleteUnknownNodes()

def detachComponentsCMD():
    genUtils.detachComponents()

def selectByPolycountCMD():
    genUtils.selectSame()

def deleteAllNameSpacesCMD():
    genUtils.deleteAllNameSpaces()

def unlockAllNodesCMD():
    genUtils.unlockAllNodes()

def setCurrentUVsToMap1CMD():
    genUtils.setCurrentUVsToMap1()

def createLocAtPivotCMD():
    genUtils.createLocAtPivot()

def deleteDisplayLayersCMD():
    genUtils.deleteAllDisplayLayers()

def importMayaCMD():
    import genTools.importExportMaya
    genTools.importExportMaya.importAsset()

def exportMayaCMD():
    import genTools.importExportMaya
    genTools.importExportMaya.exportAsset()

def moveToOriginCMD():
    import genTools.moveToOrigin
    genTools.moveToOrigin.moveToOrigin()

def versionUpCurrentFileCMD():
    import genTools.versionFile
    genTools.versionFile.versionOpenMayaFile()

def pluginManagerCMD():
    import genTools.pluginManager
    genTools.pluginManager.launch()

def movePivotBACMD():
    mm.eval('movePivotBA();')

def movePivotToOriginCMD():
    mm.eval('movePivotToOrigin();')

def sortOutlinerCMD():
    mm.eval('sortOutliner();')

def UVEditorCMD():
    for panel in mc.getPanel(sty="polyTexturePlacementPanel") or []:
        mc.scriptedPanel(panel, e=True, to=True)

def cometRenameCMD():
    mm.eval('cometRename();')

def copyCurrentScenePathCMD():
    from PySide2 import QtGui
    maya_file = mc.file(sceneName=True, q=True)
    clip = QtGui.QClipboard()
    clip.setText(str(maya_file))

'''MODELLING TOOLS'''

def extractVisGeoCMD():
    import modellingTools.extractVisGeo
    modellingTools.extractVisGeo.extractSelected()

def exportOBJCMD():
    import modellingTools.exportOBJ
    modellingTools.exportOBJ.launch()

def fastRetopoCMD():
    import modellingTools.retopoMultiple
    modellingTools.retopoMultiple.fastRetopoMultiple()

def cubeUVsCMD():
    import modellingTools.cubeUVs
    modellingTools.cubeUVs.applyCubeUVs()

def cubinateCMD():
    import modellingTools.cubinate
    modellingTools.cubinate.cubinate()

def cardGeneratorCMD():
    import modellingTools.cardGenerator
    modellingTools.cardGenerator.launch()

def selectByAngleCMD():
    if not mc.polySelectConstraint(query=True, ap=True) is True:
        mc.polySelectConstraint(ap=True, at=38)
    else:
        mc.polySelectConstraint(ap=False, at=0)

def detachDuplicateComponentsCMD():
    mm.eval('detachDuplicateComponents();')

def selectNthEdgeCMD():
    mm.eval('polySelectEdgesEveryN "edgeRing" 2;')

'''RIGGING TOOLS'''

def exportPuppetForSkeletalMeshCMD():
    import riggingTools.exportPuppetForSkeletalMesh
    riggingTools.exportPuppetForSkeletalMesh.main()

def mzCtrlCreatorCMD():
    import riggingTools.mz_ctrlCreator
    riggingTools.mz_ctrlCreator.buildWindow()

def DoraSkinWeightCMD():
    mm.eval('DoraSkinWeightImpExp();')

def loadAdvancedSkeletonCMD():
    advancedSkeletonInstallPath = 'L:/SagaTools/GenTools/AdvancedSkeleton/install.mel'
    mm.eval(f'source "{advancedSkeletonInstallPath}"')

'''SHADER TOOLS'''

def renameShaderToShapeNameCMD():
    import shadingTools.genShaderUtils
    shadingTools.genShaderUtils.renameShaderToShapeName()

def separateByShadingGroupsCMD():
    import shadingTools.separateByShadingGroups
    shadingTools.separateByShadingGroups.main()

def toggleVertexColorDisplayCMD():
    import shadingTools.genShaderUtils
    shadingTools.genShaderUtils.toggleVertexColorDisplay()

def createBlinnPerShapeCMD():
    import shadingTools.genShaderUtils
    shadingTools.genShaderUtils.createBlinnPerShape()

def copyShaderToObjectsCMD():
    import shadingTools.genShaderUtils
    shadingTools.genShaderUtils.copyShaderToObjects()

def buildShaderNetworkFromSubstanceCMD():
    import shadingTools.buildShaderNetworkFromSubstance
    shadingTools.buildShaderNetworkFromSubstance.launch()

def randomVertColCMD():
    mm.eval('randomVertCol();')

'''TECHVIS TOOLS'''

def measurementToolsCMD():
    import techvisTools.measurementToolsUI
    techvisTools.measurementToolsUI.openWindow()

'''TEXTURE TOOLS'''

def splitShapesPerUDIMCMD():
    import textureTools.splitShapesPerUDIM
    textureTools.splitShapesPerUDIM.splitShapesPerUDIM()

def convertTextureUICMD():
    import textureTools.convertTextureUI
    textureTools.convertTextureUI.launch()

def convertDirtyTexturesToSetDecCMD():
    import unrealTools.convertDirtyTexturesToSetDec
    unrealTools.convertDirtyTexturesToSetDec.ConvertTextures()

def convertTextureUICMD():
    import textureTools.convertTextureUI
    textureTools.convertTextureUI.launch()

'''UNREAL TOOLS'''

def exportSetDecAssetsCMD():
    import unrealTools.exportSetDecAssets
    unrealTools.exportSetDecAssets.openWindow()

def convertMegascansAssetsCMD():
    import unrealTools.convertMegascansAssets
    unrealTools.convertMegascansAssets.launch()

def publishShotForUnrealCMD():
    import unrealTools.publishShotForUnreal
    unrealTools.publishShotForUnreal.launch()

def USDSceneImportExportUIMayaCMD():
    import unrealTools.USDSceneImportExportUIMaya
    unrealTools.USDSceneImportExportUIMaya.launch()


'''
BUILD SHELF
'''

def makeShelfAndButtons():
    iconPath = mayaFilePaths.mayaShelfIconPath
    slapFactoryShelf = shelfCreate.ShelfTool('SAGA_SHELF', iconPath)

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
        slapFactoryShelf.addMenu(modellingButton, 'Convert Megascans Assets', convertMegascansAssetsCMD)
        slapFactoryShelf.addMenu(modellingButton, 'Load Tunnel Asset Lib', loadTunnelCMD)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        riggingButton = slapFactoryShelf.shelfButton(blankCMD, 'rigging.png', 'Rigging Tools')
        slapFactoryShelf.addMenu(riggingButton, '', blankCMD)
        slapFactoryShelf.addMenuSpacer(riggingButton, label='Commands')
        slapFactoryShelf.addMenu(riggingButton, 'Export puppet for Skeletal Mesh', exportPuppetForSkeletalMeshCMD)
        slapFactoryShelf.addMenu(riggingButton, 'Dora Skin Weight Importer', DoraSkinWeightCMD)
        slapFactoryShelf.addMenu(riggingButton, 'MZ Ctrl Creator', mzCtrlCreatorCMD)
        slapFactoryShelf.addMenuSpacer(riggingButton, label='Tools')
        slapFactoryShelf.addMenu(riggingButton, 'Load Advanced Skelton Shelf', loadAdvancedSkeletonCMD)

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
        slapFactoryShelf.addMenu(shaderToolsButton, 'Build shader network from Substance', buildShaderNetworkFromSubstanceCMD)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed building rebuildButton", e)

    try:
        cameraButton = slapFactoryShelf.shelfButton(blankCMD, 'cameraTools.png', 'Shader Tools')
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
        slapFactoryShelf.addMenu(techvisToolsButton, 'Measurement Tools', measurementToolsCMD)
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
        slapFactoryShelf.addMenuSpacer(unrealToolsButton, label='Commands')
        slapFactoryShelf.addMenuSpacer(unrealToolsButton, label='Tools')
        slapFactoryShelf.addMenu(unrealToolsButton, 'Publish Setdec Assets', exportSetDecAssetsCMD)
        slapFactoryShelf.addMenu(unrealToolsButton, 'Publish Shot To Unreal', publishShotForUnrealCMD)
        slapFactoryShelf.addMenu(unrealToolsButton, 'Publish Layout Scene Description', USDSceneImportExportUIMayaCMD)

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