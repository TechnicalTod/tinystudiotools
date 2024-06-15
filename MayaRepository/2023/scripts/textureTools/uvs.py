import math, operator

from typeUtils import fi, li, asList
from dag import getShapesOfType as getMeshShapes
from typeUtils import flattenListOfLists

import maya.cmds as mc
import maya.mel as mm

'''
def __getShaderPerMeshDetails__(nodes=None, returnLambert1=False):

    from mo.wm.utils.shader import getShaders

    meshShapes = getMeshShapes(nodes)
    out = {}
    badShapes = []

    for mesh in meshShapes:
        material = getShaders(nodes=mesh)
        if not returnLambert1:
            if 'lambert1' in material:
                material.remove('lambert1')
        if len(material) > 1:
            badShapes.append(str(mesh))
        if not material:
            continue
        material = material[0]
        if not material in out:
            out[material] = []
        out[material].append(mesh)

    if badShapes:
        raise RuntimeError('There are more than one materials assigned to ' + str(badShapes).strip('[]'))

    return out
'''

def normalizeUvs(nodes=None):

    nodes = getMeshShapes(nodes)
    uMin, uMax, vMin, vMax = getMeshUVBoundingBox(meshToQuery=nodes)

    # uv scale values
    su = 1 / abs(uMin - uMax)
    sv = 1 / abs(vMin - vMax)
    ou = uMin * su * -1
    ov = vMin * sv * -1

    # 2d node values
    osu = abs(uMin - uMax)
    osv = abs(vMin - vMax)
    oou = uMin * -1
    oov = vMin * -1

    # normalize uvs
    moveUv(nodes=nodes, offSetU=ou, offSetV=ov, scaleU=su, scaleV=sv)

    # return the offsets
    return oou, oov, osu, osv


def normalizeUvsPerMaterial(nodes=None):

    nodes = getMeshShapes(nodes)

    for mat, shapes in __getShaderPerMeshDetails__(nodes, True).items():

        print (mat, shapes
)
        if getMeshUvTile(meshToQuery=shapes, validateUvs=True, tolerance=3, errorWhenInvalid=False):
            moveNodesToUvTile(nodes=shapes, tile=1001)
            continue

        fileNodes = mc.listConnections(mat, type='file', source=True)

        place2dTextures = []

        if fileNodes:
            for fileNode in fileNodes:
                place2dTexture = mc.listConnections(fileNodes, type='place2dTexture', source=True)
                if not place2dTexture:
                    print ('WARNING: missing place2dTexture node on', fileNode)
                    continue

                place2dTextures += place2dTexture

        place2dTextures = list(set(place2dTextures))

        ou, ov, su, sv = normalizeUvs(shapes)

        for texture in place2dTextures:
            mc.setAttr(texture + ".repeatU", su)
            mc.setAttr(texture + ".repeatV", sv)
            mc.setAttr(texture + ".offsetU", 1 - ou)
            mc.setAttr(texture + ".offsetV", 1 - ov)


def moveUv(nodes=None, offSetU=0, offSetV=0, scaleU=0, scaleV=0):

    from mo.wm.utils.openMaya.mesh import getUVs

    meshShapes = getMeshShapes(nodes)
    for mesh in meshShapes:

        uvLen = len(getUVs(mesh)) - 1
        uvs = '{shape}.map[0:{maxUv}]'
        uvs = uvs.format(shape=mesh, maxUv=uvLen)
        mc.polyEditUV(uvs, u=offSetU, v=offSetV, scaleU=scaleU, scaleV=scaleV)


def moveNodesToUvTile(nodes=None, tile=1001):

    def __moveUvs__(fromTile, toTile, shapes):

        # - Move Uvs-----------------------------------------------
        fromTile = float(fromTile) - 1000
        toTile = float(toTile) - 1000
        offSetV = int((toTile - fromTile) / 10)
        offSetU = (((toTile - fromTile) / 10) - offSetV) * 10
        moveUv(nodes=shapes, offSetU=offSetU, offSetV=offSetV)

        # - Place 2d textures -------------------------------------
        place2dTextures = []
        for mat in __getShaderPerMeshDetails__(nodes=shapes).keys():
            fileNodes = mc.listConnections(mat, type='file', source=True)
            if fileNodes:
                for fileNode in fileNodes:
                    place2dTexture = mc.listConnections(fileNodes, type='place2dTexture', source=True)
                    place2dTextures += place2dTexture
            else:
                place2dTexture = []
            place2dTextures = list(set(place2dTextures))
        for tex in place2dTextures:
            ru = mc.getAttr(tex + ".repeatU")
            rv = mc.getAttr(tex + ".repeatV")
            ou = mc.getAttr(tex + ".offsetU")
            ov = mc.getAttr(tex + ".offsetV")
            newOu = ou + ((1 - ru) * offSetU)
            newOv = ov + ((1 - rv) * offSetV)
            mc.setAttr(tex + ".offsetU", newOu)
            mc.setAttr(tex + ".offsetV", newOv)

    nodes = getMeshShapes(nodes)
    info = getMeshUVTileInfo(meshToQuery=nodes, validateUvs=False)

    for fromTile, shapes in info.items():
        __moveUvs__(fromTile, 1001, shapes)
        __moveUvs__(1001, tile, shapes)


def moveNodesToNextTile(nodes=None):

    nodes = getMeshShapes(nodes)
    info = getMeshUVTileInfo(meshToQuery=nodes, validateUvs=False)

    for fromTile, shapes in info.items():
        nextTile = fromTile + 1
        moveNodesToUvTile(shapes, nextTile)


def moveNodesToPreviousTile(nodes=None):

    nodes = getMeshShapes(nodes)
    info = getMeshUVTileInfo(meshToQuery=nodes, validateUvs=False)

    for fromTile, shapes in info.items():
        nextTile = fromTile - 1
        moveNodesToUvTile(shapes, nextTile)


def moveUvsToTilePerMaterial(nodes=None):

    nodes = getMeshShapes(nodes)
    matInfo = __getShaderPerMeshDetails__(nodes)
    tile = 1000
    for mat, shapes in matInfo.items():
        tile += 1
        moveNodesToUvTile(shapes, tile)


def collapseUvsByDistance(maxDist):

    def returnAvarage(listOfUvs):

        u = 0
        v = 0
        divisor = len(listOfUvs)
        for uv in listOfUvs:
            u += uv[1]
            v += uv[2]
        u = u / divisor
        v = v / divisor
        return u, v

    def getDistance(pointA, pointB):
        x1, y1 = pointA
        x2, y2 = pointB
        return abs(x2 - x1) + abs(y2 - y1)

    def __rfi__(itemList):

        ritem = []
        for item in itemList:
            ritem.append(item[0])
        return ritem

    sel = mc.ls(sl=True)
    newSel = mc.polyListComponentConversion(sel, fv=True, fe=True, ff=True, tuv=True)
    if newSel:
        mc.select(newSel)

    uvs = mc.filterExpand(fp=True, ex=True, sm=35)

    uvsList = []
    for uv in uvs:
        uvValue = mc.polyEditUV(uv, q=True)
        uvsList.append([uv] + uvValue)

    matches = []
    keys = 0
    for uvA in uvsList:
        tempList = []
        for uvB in uvsList:
            if uvA != uvB:
                if getDistance(uvA[1:], uvB[1:]) < maxDist:

                    if not uvA[0] in tempList:
                        tempList.append(uvA)
                    if not uvB[0] in tempList:
                        tempList.append(uvB)

        tempList.sort()
        if not tempList in matches:
            if tempList:
                matches.append(tempList)

    for item in matches:
        uValue, vValue = returnAvarage(item)
        mc.polyEditUV(__rfi__(item), relative=False, u=uValue, v=vValue)


def getObjectsWithIdenticalUvs(meshNodes=None):

    from mo.wm.utils.openMaya.mesh import getUVs

    meshNodes = getMeshShapes(meshNodes)
    meshDic = {}

    for mesh in meshNodes:

        meshUVs = getUVs(mesh)
        meshUVs = list(set(meshUVs))
        meshUVs.sort()

        uvString = str(meshUVs)

        if not uvString in meshDic:
            meshDic[uvString] = []
        meshDic[uvString].append(mesh)

    return meshDic.values()


def groupByMatchingUvs(meshNodes=None, newName='match'):

    groups = []

    for shapeNodes in getObjectsWithIdenticalUvs(meshNodes):

        if len(shapeNodes) > 1:  # objects with matching friends

            # parent the item to the world
            parents = mc.listRelatives(shapeNodes, p=True)
            if mc.listRelatives(parents, p=True):  # stupid maya errors when already a child of the world
                mc.parent(parents, w=True)

            # group the matching items
            groups.append(mc.group(parents, n=newName + '_uvMatch1'))

    # put all the matches in a group
    if groups:
        mc.group(groups, n='items_with_matching_uvs')


def hideObjectsWithDouplicatedUvs(meshNodes=None):

    meshNodes = getMeshShapes(meshNodes)

    for shapeNodes in getObjectsWithIdenticalUvs(meshNodes):

        if len(shapeNodes) > 1:  # objects with matching friends

            masterShapeNode = shapeNodes[0]
            otherShapeNodes = shapeNodes[1:]

            parentTransforms = mc.listRelatives(otherShapeNodes, p=True)

            print (parentTransforms)

            mc.hide(parentTransforms)


def linkIdenticalUvs(meshNodes=None, templateNonRoots=True):

    meshNodes = getMeshShapes(meshNodes)

    # delete history, stacking history nodes when linking uvs will cause maya to crash
    mc.delete(meshNodes, ch=True)

    historyRemovedNodes = []
    for node in meshNodes:

        if mc.objExists(node):
            parent = mc.listRelatives(node, p=True, f=True)
            mc.toggle(parent, state=False, template=True)
            mc.delete(parent, ch=True)
            historyRemovedNodes.append(node)

    shortList = []
    for shapeNodes in getObjectsWithIdenticalUvs(historyRemovedNodes):

        if len(shapeNodes) > 1:  # objects with matching friends

            masterShapeNode = shapeNodes[0]
            otherShapeNodes = shapeNodes[1:]

            for other in otherShapeNodes:
                mc.polyTransfer(other, alternateObject=masterShapeNode, constructionHistory=True)

            otherParents = mc.listRelatives(otherShapeNodes, p=True, f=True)
            masterParent = mc.listRelatives(masterShapeNode, p=True, f=True)

            if templateNonRoots:
                mc.toggle(otherParents, state=True, template=True)
                mc.toggle(masterParent, state=True, template=False)

            #mc.group(otherParents, n='COPIES')
            #mc.group(masterParent, n='MASTERS')

            shortList.append(masterShapeNode)

        else:
            if shapeNodes:
                shortList.append(shapeNodes[0])

    return shortList


def packKeeptingMatchingUvs(meshNodes=None, preScale=0, seperateOverlapping=True, uvSet='map1'):

    meshNodes = getMeshShapes(meshNodes)
    shortList = linkIdenticalUvs(meshNodes)

    if seperateOverlapping:
        for shape in shortList:

            mc.polyLayoutUV(
                shape,
                caching=False,
                constructionHistory=False,
                flipReversed=True,
                layout=2,
                layoutMethod=0,  # 0 = Block Stacking,  1 = Shape Stacking
                nodeState=0,
                rotateForBestFit=2,
                scale=1,
                separate=2,     # 0 = No cuts, 1 = Cut only along folds, 2 = Make all cuts
                uvSetName=uvSet,
                worldSpace=True,
                )

    mc.polyMultiLayoutUV(shortList,
        layout=2,
        layoutMethod=1,
        prescale=preScale,  # 0 = None, 1 = object space, 2 = world space
        rotateForBestFit=2,
        scale=1,
        uvSetName=uvSet,
        )

    mc.select(shortList)


def makeNormalizedUvSetCopy(nodes=None, gazeboUvSet='NormalizedUvSet'):

    item = getMeshShapes(nodes)

    # Remove the uv set if it exists
    if gazeboUvSet in mc.polyUVSet(item, auv=True, q=True):
        mc.polyUVSet(item, d=True, uvSet=gazeboUvSet)

    # create the new uv set
    newSet = []
    for i in item:
        newSet.append(mc.polyCopyUV(i, uvSetNameInput="map1", uvSetName=gazeboUvSet, createNewMap=True, ch=1))
        mc.polyUVSet(i, currentUVSet=True, uvSet=gazeboUvSet)

    # pack the new uv set
    return normalizeUvs(nodes=item)


def getMeshUVBoundingBox(meshToQuery=None, error=True):
    '''

    Description
        This function will get the collective uv bounding box of all mesh specified.
        If no mesh is spfecified the function will query based on the users selection.

    Parameters
        [in] meshToQuery: Mesh(es) to query uv bounding box

    Returns

    Examples

    '''
    meshToQuery = asList(meshToQuery)

    # Validate meshToQuery
    if not meshToQuery:
        meshToQuery = mc.ls(sl=True, dag=True, type='mesh', noIntermediate=True, long=True)
    if not meshToQuery:
        raise RuntimeError('Please provide or select a mesh to query')

    meshUVs = []

    for meshNode in meshToQuery:
        # Quickly validate the meshToQuery is a mesh
        if not mc.objectType(meshNode, isAType='mesh'):
            meshNode = fi(mc.ls(meshNode, dag=True, noIntermediate=True, type='mesh', long=True))
            if not meshNode:
                continue

        # Get the meshes U and U Min/Max to determine which tiles it lives on
        meshUVs += mo.wm.utils.openMaya.mesh.getUVs(meshNode)

        # Error if we stumble on an object with no uvs
        if not meshUVs:
            raise RuntimeError('This object seems to have no UVs: %s' % meshNode)

    # Get min/max U,V
    uMin = fi(min(meshUVs))
    uMax = fi(max(meshUVs))
    vMin = li(min(meshUVs, key=lambda x: x[1]))
    vMax = li(max(meshUVs, key=lambda x: x[1]))

    return (uMin, uMax, vMin, vMax)


def getMeshUvTile(meshToQuery=None, validateUvs=True, tolerance=3, errorWhenInvalid=True):
    '''

    Description
        Return the current uvTile for the given or seleccted mesh
        If it lies on more than 1 uvTile error

    Parameters
        [in] meshToQuery: Which meshes to query, if none is given it works on selection
        [in] validateUvs: Boolean

    Returns
        [out] uvTile: The uvTile number of the current meshes uvs

    Examples

    '''
    # Validate meshToQuery
    if not meshToQuery:
        meshToQuery = fi(mc.ls(sl=True, dag=True, type='mesh', noIntermediate=True, long=True))
    if not meshToQuery:
        raise RuntimeError('Please provide or select a mesh to query')
    meshToQuery = fi(asList(meshToQuery))

    # Get the mesh uv bounding box
    uMin, uMax, vMin, vMax = getMeshUVBoundingBox(meshToQuery)

    # Allow the result to be rounded by a set tolerance
    if tolerance:
        uMin = round(uMin, tolerance)
        uMax = round(uMax, tolerance)
        vMin = round(vMin, tolerance)
        vMax = round(vMax, tolerance)

    # Get the uDim value
    if 'rmanF__mapUDim' in mc.listAttr(meshToQuery):
        uDim = mc.getAttr(meshToQuery + '.rmanF__mapUDim')
    else:
        uDim = 10

    if validateUvs:
        if uMax - math.floor(uMin) > 1 or vMax - math.floor(vMin) > 1:
            if errorWhenInvalid:
                print ('uMin:', uMin, 'uMax:', uMax)
                raise RuntimeError('The following mesh(s) are not using tiles: %s' % meshToQuery)
            else:
                return None

    # Get the center of the uv bounding box
    uCenter = (uMin + uMax) / 2
    vCenter = (vMin + vMax) / 2

    # Calculate the uvTile for the center
    uCenter = math.ceil(uCenter)
    vCenter = math.ceil(vCenter)
    uvTile = int((vCenter - 1) * uDim + uCenter + 1000)

    return uvTile


def getMeshUVTileInfo(meshToQuery=None, validateUvs=True):
    '''

    Description

        Get UV tile information from a mesh, which tile, and if more than one tile is assigned which faces are assigned to which tile.
        {tileNumber: [meshFaces]}

    Parameters
        [in] meshToQuery: Which meshes to query, if none is given it works on selection

    Returns
        [out] uvTileInfo: A dictionary containing the tile number and shapes assigned
                          {tileNumber: [meshFaces]}

    Examples

    '''
    meshToQuery = asList(meshToQuery)

    # Validate meshToQuery
    if not meshToQuery:
        meshToQuery = mc.ls(sl=True, dag=True, type='mesh', long=True)
    if not meshToQuery:
        raise RuntimeError('Please provide or select a mesh to query... Thank You.')

    # Quickly validate the meshToQuery is a mesh
    for mesh in meshToQuery:
        if not mc.objectType(mesh, isAType='mesh'):
            meshToQuery = mc.ls(meshToQuery, dag=True, type='mesh', noIntermediate=True, long=True)
            break

    # Finally if there is no meshToQuesrty at this point error
    if not meshToQuery:
        raise RuntimeError('Please provide or select a mesh to query')

    uvTileInfo = {}

    # Iterate over the mesh and get its uvTile
    for mesh in meshToQuery:
        uvTile = getMeshUvTile(meshToQuery=mesh, validateUvs=validateUvs)
        uvTileInfo.setdefault(uvTile, []).append(mesh)

    # Return the UV tile info
    return uvTileInfo


def getUvSetInfo(meshesToQuery=None):
    '''
    Return a list of dicts, formatted for the palette
    If there is only 1 uvSet dont add the information
    '''
    # Validate meshToQuery
    meshesToQuery = getMeshShapes(meshesToQuery)

    if not meshesToQuery:
        raise RuntimeError('Please provide or select a mesh to query')
    meshesToQuery = asList(meshesToQuery)

    attributeDetails = []
    for meshToQuery in meshesToQuery:
        uvSets = mc.polyUVSet(meshToQuery, allUVSets=True, query=True)

        if uvSets and len(uvSets) > 1:
            uvSet = mo.wm.utils.openMaya.attribute.getAttr(node=meshToQuery, attr='currentUVSet')
            attributeDetails.append({'name': 'uvset', 'type': 'string', 'shape': meshToQuery, 'value': uvSet})

    return attributeDetails


def closeUVifNeeded(maxObjects=200):
    '''
    Description:
        If you have more than 200 object selected, close the UV Texture Editor

    Parameters:
        None

    Returns:
        None
    '''

    selectionShortAll = mc.filterExpand(fullPath=True, sm=(12, 9, 10, 22))

    if len(selectionShortAll) > maxObjects:
        if mc.window('polyTexturePlacementPanel1Window', exists=True):
            mc.deleteUI('polyTexturePlacementPanel1Window')


def getUvSetIndexes(meshNodes=None):
    '''
    returns a dictonary of uv set indexes for for each uv set name by object

    example:
    {u'|object|objectShape1': {u'map1': 0, u'uvSet1': 1}}
    '''

    meshNodes = getMeshShapes(meshNodes)

    nodeDic = {}
    for node in meshNodes:
        uvSetsIndices = mc.polyUVSet(node, query=True, allUVSetsIndices=True)
        uvSetNames = mc.polyUVSet(node, query=True, allUVSets=True)
        uvSets = dict(zip(uvSetNames, uvSetsIndices))
        nodeDic[node] = uvSets
    return nodeDic


def applyDefultUvSetNetwork(meshNodes=None):

    '''
    applies a uv set shader network to meshNodes
    '''
    meshNodes = getMeshShapes(meshNodes)
    uvSetInfo = getUvSetIndexes(meshNodes)

    for node in meshNodes:
        currentUVSet = mc.polyUVSet(node, query=True, currentUVSet=True)

        if currentUVSet:
            currentUVSet = currentUVSet[0]
        else:
            mc.warning('no uvs')
            return

        currentUVIndex = uvSetInfo[node][currentUVSet]
        cur = '{meshNode}.uvSet[{uvIndex}].uvSetName'.format(meshNode=node, uvIndex=currentUVIndex)

        for texture in mo.wm.utils.shader.getFileNodes(node):
            mc.uvLink(uvSet=cur, texture=texture)


def convertToUVs(*args):
    '''
    Input: object name , list of components or list of lists of components
    Output: list of UVs with full name obtained by converting the input object/components to UVs,
            output can be also list of lists if that was the input
    '''
    selection = mc.ls(sl=True, l=True)
    uvs_all = []
    for arg in args:
        try:
            uvs = mc.polyListComponentConversion(arg, tuv=True)
            mc.select(uvs, r=True)
            uvs = mc.ls(sl=True, fl=True, l=True)
            uvs_all.append(uvs)

        except:
            for item in arg:
                uvs = mc.polyListComponentConversion(item, tuv=True)
                mc.select(uvs, r=True)
                uvs = mc.ls(sl=True, fl=True, l=True)
                uvs_all.append(uvs)

    if selection:
        mc.select(selection, r=True)

    return uvs_all


def getShellsBoundingBoxes(shellsUvs):
    '''
    Description:
        Get bounding box values of all input UV shells.

    Parameters:
        [in] shellsUVs:  List of UV shells, each UV shell is a list of individual UVs

    Returns:
        List of bounding boxes of selected components shells, each bounding box as ((uMin, uMax), (vMin, vMax))
    '''
    selection = mc.ls(sl=True, fl=True, l=True)
    shellsBboxes = []
    for uvs in shellsUvs:
        mc.select(uvs, r=True)
        bbox = mc.polyEvaluate(uvs, bc2=True)
        shellsBboxes.append(bbox)
    if selection:
        mc.select(selection, r=True)

    return shellsBboxes


def getFaceShells(*args):
    '''
    Output: list that consists of a list of faces that form a UV shell
    *args may contain any number of objects or components or a single list of components that are selectable in maya
    '''
    selection = mc.ls(sl=True, fl=True, l=True)
    shells = []
    faces_all = []
    faces = mc.polyListComponentConversion(args[0], tf=True, internal=True)
    mc.select(faces, r=True)
    mm.eval("SelectUVShell")
    faces = mc.ls(sl=True, fl=True, l=True)
    while len(faces) > 0:
        mc.select(faces[0], r=True)
        mm.eval("SelectUVShell")
        shell = mc.ls(sl=True, fl=True, l=True)
        shells.append(shell)
        for item in shell:
            faces.remove(item)

    if selection:
        mc.select(selection, r=True)
    return shells


def getUvTransformsUvSpace(components=None):
    '''
    Description:
        Get transformation values for input/selected UVs in UV space

    Parameters:
        [in] components: Any number of maya components of any type or mesh objects.
                         These objects/components need to be convertible to UVs with polyListComponentConversion command.

    Returns:
        Dictionary where key is a uv name and value is a tuple with UV transform in UV space
    '''

    uvsTransUvDict = {}
    selection = components or mc.ls(sl=True, fl=True, l=True)
    selectionUVs = flattenListOfLists(convertToUVs(selection))
    for uv in selectionUVs:
        uvsTransUvDict[uv] = tuple(mc.polyEditUV(uv, q=True, u=True))

    return uvsTransUvDict


def getUVWorldTransforms(components=None):
    '''
    Description:
        Get transformation values for input/selected UVs in world space

    Parameters:
        [in] components: Any number of maya components of any type or mesh objects.
                         These objects/components need to be convertible to UVs with polyListComponentConversion command.

    Returns:
        Dictionary where key is a uv name and value is a tuple with UV transform in world space
    '''

    uvsWorldTransforms = {}
    selection = components or mc.ls(sl=True, fl=True, l=True)
    selectionUVs = flattenListOfLists(convertToUVs(selection))
    for uv in selectionUVs:
        uvsWorldTransforms[uv] = tuple(mc.xform(uv, q=True, t=True, ws=True))

    return uvsWorldTransforms


def alignUVShells(components=None):
    '''
    Description:
        Rotate UV shells of selected components based on assumption that
        best rotation configuration has the bounding box with smallest area.

    Parameters:
        [in] components: Any number of maya components of any type or mesh objects.
                         These objects/components need to be convertible to UVs with polyListComponentConversion command.
    Returns:
        None
    '''

    selection = components or mc.ls(sl=True, fl=True, l=True)
    #expand selection to UV shells
    shells = getFaceShells(selection)
    shellsUVs = convertToUVs(shells)
    shellsBboxes = getShellsBoundingBoxes(shellsUVs)
    i = 0
    for uvs in shellsUVs:
        mc.select(uvs, r=True)
        bbox = shellsBboxes[i]
        pivotU = bbox[0][0] + ((bbox[0][1] - bbox[0][0]) / 2.0)
        pivotV = bbox[1][0] + ((bbox[1][1] - bbox[1][0]) / 2.0)
        final_rotation_todo = 0

        #test what is the area of bounding box if we rotate by x
        def testArea(x):
            mc.polyEditUV(uvs, pu=pivotU, pv=pivotV, a=x)
            bboxX = mc.polyEvaluate(uvs, bc2=True)
            areaX = abs(bboxX[0][1] - bboxX[0][0]) * abs(bboxX[1][1] - bboxX[1][0])
            mc.polyEditUV(uvs, pu=pivotU, pv=pivotV, a=-x)
            return areaX

        #determine direction of rotation first (based on volumes on rotation of +1 -1 values)
        if testArea(1.0) < testArea(-1.0):
            j = 45.0
            k = 22.5
        else:
            j = -45.0
            k = -22.5
        #binary tree to refine the value.
        for v in range(0, 15):
            a = testArea(k - ((abs(k - j)) / 2.0))
            b = testArea(k + ((abs(k - j)) / 2.0))

            if a < b:
                tmp = j
                j = k
                k = (k - ((abs(k - tmp)) / 2.0))
            else:
                tmp = j
                j = k
                k = (k + ((abs(k - tmp)) / 2.0))

            final_rotation_todo = k
        mc.polyEditUV(uvs, pu=pivotU, pv=pivotV, a=final_rotation_todo)
        i = i + 1

    if selection:
        mc.select(selection, r=True)


def rotateUVShells(components=None):
    '''
    Description:
        Rotate UV shells so that each shell faces same direction.
        This is done by finding 4 corner UVs of each shell and then comparing UV values of opposite uvs to respective y values in world transformation
        To find 4 corner UVs, compare the distance of UVs to the 4 corners of the shells bounding box

    Parameters:
        [in] components: Any number of maya components of any type or mesh objects.
                         These objects/components need to be convertible to UVs with polyListComponentConversion command.

    Returns:
        None
    '''

    selection = components or mc.ls(sl=True, fl=True, l=True)
    selectionUVs = convertToUVs(selection)
    uvsTransUvDict = getUvTransformsUvSpace(selectionUVs)  # dictionary where key is uv and value is a tuple with transforms in UV space
    uvsVertTrans = getUVWorldTransforms(selectionUVs)  # dictionary where key is uv and value is a tuple with transforms in world space
    shellsUVs = convertToUVs(getFaceShells(selection))
    shellsBboxes = getShellsBoundingBoxes(shellsUVs)
    i = 0
    for uvs in shellsUVs:
        #find 4 cornermost UVs
        bbox = shellsBboxes[i]  # ((uMin, uMax), (vMin, vMax))
        #check which uv is umin_vmin
        umin_vmin_dict = {}
        for uv in uvs:
            u_delta = abs(uvsTransUvDict[uv][0] - bbox[0][0])
            v_delta = abs(uvsTransUvDict[uv][1] - bbox[1][0])
            uv_delta = u_delta + v_delta
            umin_vmin_dict[uv] = uv_delta
        umin_vmin_sorted = sorted(umin_vmin_dict.iteritems(), key=operator.itemgetter(1))
        umin_vmin = umin_vmin_sorted[0][0]
        umin_vmin_y = uvsVertTrans[umin_vmin][1]  # y value of a vertex corresponding to umin_vmin uv

        #check which uv is umin_vmax
        umin_vmax_dict = {}
        for uv in uvs:
            u_delta = abs(uvsTransUvDict[uv][0] - bbox[0][0])
            v_delta = abs(uvsTransUvDict[uv][1] - bbox[1][1])
            uv_delta = u_delta + v_delta
            umin_vmax_dict[uv] = uv_delta
        umin_vmax_sorted = sorted(umin_vmax_dict.iteritems(), key=operator.itemgetter(1))
        umin_vmax = umin_vmax_sorted[0][0]
        umin_vmax_y = uvsVertTrans[umin_vmax][1]

        #check which uv is umax_vmin
        umax_vmin_dict = {}
        for uv in uvs:
            u_delta = abs(uvsTransUvDict[uv][0] - bbox[0][1])
            v_delta = abs(uvsTransUvDict[uv][1] - bbox[1][0])
            uv_delta = u_delta + v_delta
            umax_vmin_dict[uv] = uv_delta
        umax_vmin_sorted = sorted(umax_vmin_dict.iteritems(), key=operator.itemgetter(1))
        umax_vmin = umax_vmin_sorted[0][0]
        umax_vmin_y = uvsVertTrans[umax_vmin][1]

        #check which uv is umax_vmax
        umax_vmax_dict = {}
        for uv in uvs:
            u_delta = abs(uvsTransUvDict[uv][0] - bbox[0][1])
            v_delta = abs(uvsTransUvDict[uv][1] - bbox[1][1])
            uv_delta = u_delta + v_delta
            umax_vmax_dict[uv] = uv_delta
        umax_vmax_sorted = sorted(umax_vmax_dict.iteritems(), key=operator.itemgetter(1))
        umax_vmax = umax_vmax_sorted[0][0]
        umax_vmax_y = uvsVertTrans[umax_vmax][1]

        #get pivots that we use to rotate each shell around, trying the pivot to be right in the middle of 4 corner uvs
        pivotU = uvsTransUvDict[umin_vmin][0] + ((uvsTransUvDict[umax_vmax][0] - uvsTransUvDict[umin_vmin][0]) / 2)
        pivotV = uvsTransUvDict[umin_vmin][1] + ((uvsTransUvDict[umin_vmax][1] - uvsTransUvDict[umin_vmin][1]) / 2)

        #check the corner UVs position against their respective vertices world space position and rotate the shell if necessary
        #all we need is check two pairs of diagonally opposite corner UVs
        if umin_vmin_y < umax_vmax_y and umin_vmax_y < umax_vmin_y:
            mc.polyEditUV(uvs, pu=pivotU, pv=pivotV, a=90)

        elif umin_vmax_y < umax_vmin_y and umax_vmax_y < umin_vmin_y:
            mc.polyEditUV(uvs, pu=pivotU, pv=pivotV, a=180)

        elif umax_vmax_y < umin_vmin_y and umax_vmin_y < umin_vmax_y:
            mc.polyEditUV(uvs, pu=pivotU, pv=pivotV, a=-90)

        i = i + 1
