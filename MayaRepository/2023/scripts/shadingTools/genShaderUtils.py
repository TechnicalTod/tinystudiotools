import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm
import os

def createBlinnPerShape():
    sel = mc.ls(sl=1)

    for node in sel:
        shaderName = "M_{0}".format(node)
        shd = mc.shadingNode('blinn', name=shaderName, asShader=True)
        shdSG = mc.sets(name='{0}_SG'.format(shd), empty=True, renderable=True, noSurfaceShader=True)
        mc.connectAttr('{0}.outColor'.format(shd), '{0}.surfaceShader'.format(shdSG))
        mc.sets(node, e=True, forceElement=shdSG)

def toggleVertexColorDisplay():
    sel = mc.ls(sl=1)

    for each in sel:
        vertexColorAttr = mc.getAttr("{0}.displayColors".format(each))
        if vertexColorAttr == True:
            mc.setAttr("{0}.displayColors".format(each), 0)
        else:
            mc.setAttr("{0}.displayColors".format(each), 1)

def copyShaderToObjects():
    sel = mc.ls(sl=1, type='geometryShape', dag=1, ni=1)

    def getShading(objectShape):
        shadingGroup = pm.listConnections(objectShape, type='shadingEngine')
        shader = pm.ls(mc.listConnections(shadingGroup), materials = 1)
        return shader, shadingGroup

    selShader = getShading(sel[0])[1]
    copyToMesh = sel[1:]

    print (copyToMesh)

    for i in copyToMesh:
        pm.sets(selShader[0], forceElement = i)

def renameShaderToShapeName():
    sel = mc.ls(sl=1)

    for each in sel:
        mc.select(each)
        selectedShape = mc.ls(sl = True, dag = True, s = True)
        shadeEng = mc.listConnections(selectedShape , type = "shadingEngine")
        materials = mc.ls(mc.listConnections(shadeEng ), materials = True)

        mc.rename(materials, "M_{}".format(each))

def forceConnect(fromAttr, toAttr):
    #Confirm the arguments are PyNodes
    if fromAttr is None:
        print(fromAttr)
        print("From attr does not exist")
        return None
    if toAttr is None:
        print(toAttr)
        print("To attr does not exist.")
        return None

    try:
        if not isinstance(fromAttr, pm.PyNode):
            fromAttr = pm.PyNode(fromAttr)
        if not isinstance(toAttr, pm.PyNode):
            toAttr = pm.PyNode(fromAttr)
        if not (isinstance(fromAttr, pm.general.Attribute) and isinstance(toAttr, pm.general.Attribute)):
            print("One or both of these are not attributes. Returning...")
            return None
    except pm.general.MayaNodeError:
        print("One of these nodes does not exist: {1, {}".format(
            str(fromAttr), str(toAttr)))
        return None

    # Disconnect toAttr
    toAttr.disconnect()
    try:
        for attr in toAttr.children():
            attr.disconnect()
    except RuntimeError:
        pass
    # Attempt simplest case
    try:
        fromAttr.connect(toAttr)
        return
    #If that doesn't work, try one to many and many to one
    except RuntimeError:
        if fromAttr.isCompound() and toAttr.isCompound():
            print("I'm confused. Both attrs are compound, but they can't connect.")
            return
        elif fromAttr.isCompound():
            fromAttr.children()[0].connect(toAttr)
        elif toAttr.isCompound():
            for child in toAttr.children():
                fromAttr.connect(child)
        else: print("I'm confused. Neither attr is compound, but they can't connect.")

def createNewFile(filePath='', fileNodeName='file', UVNodeName='place2DTexture', color_space="sRGB"):
    newFileNode = pm.shadingNode('file', asTexture=True, isColorManaged=True, name=fileNodeName)
    if filePath:
        newFileNode.fileTextureName.set(filePath)
    newFileNode.ignoreColorSpaceFileRules.set(True)
    newFileNode.colorSpace.set(color_space)
    placeTex = pm.shadingNode('place2dTexture', asUtility=True, name=UVNodeName)
    connectUVtoFile(placeTex, newFileNode)
    return newFileNode

def connectUVtoFile(placeTex, newFileNode):
    # Attributes to connect from place2dTexture to file node
    attributes = [
        'coverage', 'translateFrame', 'rotateFrame', 'mirrorU', 'mirrorV',
        'stagger', 'wrapU', 'wrapV', 'repeatUV', 'offset', 'rotateUV',
        'noiseUV', 'vertexUvOne', 'vertexUvTwo', 'vertexUvThree',
        'vertexCameraOne'
    ]

    # Connect standard attributes
    for attr in attributes:
        mc.connectAttr("{}.{}".format(placeTex, attr), "{}.{}".format(newFileNode, attr), f=True)

    # Connect specific UV attributes
    mc.connectAttr("{}.{}".format(placeTex, 'outUV'), "{}.{}".format(newFileNode, 'uvCoord'), f=True)
    mc.connectAttr("{}.{}".format(placeTex, 'outUvFilterSize'), "{}.{}".format(newFileNode, 'uvFilterSize'), f=True)