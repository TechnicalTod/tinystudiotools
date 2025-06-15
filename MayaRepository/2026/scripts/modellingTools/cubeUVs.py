'''
Automatically UV map selected objects based on the ideal mapping of a simple cube. 
The closer the original object shape is to the cube, the better the result.
'''

import sys
import operator

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om
import pymel.core as pm

import genTools.dag
from genTools.typeUtils import asList, flattenListOfLists
from textureTools.uvs import getShellsBoundingBoxes, convertToUVs, getFaceShells, getUvTransformsUvSpace, getUVWorldTransforms, alignUVShells, rotateUVShells


class CubeUVs():
    def __init__(self, objectName):
        self.objectName = objectName
        self.verticesTransforms = self.getVerticesWorldTransform(self.objectName)
        self.edgeLengths = self.getEdgeLengths(self.objectName)
        self.allEdges = self.getAllEdges(self.objectName)

    def getEdgeLengths(self, node):
        '''
        Description:
            Get dictionary where key is a name of edge and value it's length
        Parameters:
            [in] node: name of the geo from which we use the edges
        Returns:
            Dictionary where key is a name of edge and value it's length
        '''

        edgeLengths = {}

        geoSelection = om.MSelectionList()
        geoSelection.add(node)
        geoDag = om.MDagPath()
        geoSelection.getDagPath(0, geoDag)

        iterSel = om.MItSelectionList(geoSelection, om.MFn.kMesh)
        edgeIterator = om.MItMeshEdge(geoDag)

        edgeId = -1
        while not edgeIterator.isDone():
            util = om.MScriptUtil()
            doublePtr = util.asDoublePtr()
            edgeIterator.getLength(doublePtr, om.MSpace.kWorld)
            length = om.MScriptUtil.getDouble(doublePtr)
            index = edgeIterator.index()
            edgeLengths[node + ".e[" + str(index) + "]"] = length
            edgeIterator.next()

        return edgeLengths

    def getAllEdges(self, object_name):
        '''
        input: object name (can be long or short), input could be also selection of components
        output: list of all edges for the object, i.e. ["object.e[1]", "object.e[2]",...]
        '''
        all_edges = []
        edge_count = mc.polyEvaluate(object_name, edge=True)
        i = 0
        while i < edge_count:
            edge = object_name + ".e[%d]" % i
            all_edges.append(edge)
            i = i + 1

        return all_edges

    def getAllUVs(self, object_name):
        '''
        Description: Get list of all UVs of the input object with their full name.
        Parameters:
            [In] objects_name:  maya object/mesh
        Returns:
            List of all UVs
        Example:
            Result for default maya cube:
            [u'|pCube1.map[0]', u'|pCube1.map[1]', u'|pCube1.map[2]', u'|pCube1.map[3]', u'|pCube1.map[4]', 
            u'|pCube1.map[5]', u'|pCube1.map[6]', u'|pCube1.map[7]', u'|pCube1.map[8]', u'|pCube1.map[9]', 
            u'|pCube1.map[10]', u'|pCube1.map[11]', u'|pCube1.map[12]', u'|pCube1.map[13]']
        '''

        all_uvs = []
        uvs_count = mc.polyEvaluate(object_name, uv=True)
        i = 0
        while i < uvs_count:
            uv = object_name + ".map[%d]" % i
            all_uvs.append(uv)
            i = i + 1

        return all_uvs

    def getAllVertices(self, object_name):
        '''
        input: object name (can be long or short), input could be also selection of components
        output: list of all vertices for the object, i.e. ["object.vtx[1]", "object.vtx[2]",...]
        '''

        all_vertices = []
        vertex_count = mc.polyEvaluate(object_name, v=True)
        i = 0
        while i < vertex_count:
            vertex = object_name + ".vtx[%d]" % i
            all_vertices.append(vertex)
            i = i + 1

        return all_vertices

    def getVerticesWorldTransform(self, node):
        '''Output: dictionary where key is a vertex name and value is a tuple with transforms in a world space
        '''

        vertices_world_transform_dict = {}
        verticesTransforms = self.getAllVerticesWorldTransforms(node)
        i = 0
        for vertex in self.getAllVertices(node):
            vertices_world_transform_dict[vertex] = verticesTransforms[i]
            i = i + 1

        return vertices_world_transform_dict

    def getAllVerticesWorldTransforms(self, node):
        '''
        Description:
            Get a list of all vertices positions. Each vertex position is a list of 3 floats.
            This is faster than previous getVerticesWorldTransform function
        '''
        mc.select(node, r=True)
        # get the active selection - node
        selection = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(selection)
        iterSel = om.MItSelectionList(selection, om.MFn.kMesh)

        # go througt selection
        while not iterSel.isDone():

            # get dagPath
            dagPath = om.MDagPath()
            iterSel.getDagPath(dagPath)

            # create empty point array
            inMeshMPointArray = om.MPointArray()

            # create function set and get points in world space
            currentInMeshMFnMesh = om.MFnMesh(dagPath)
            currentInMeshMFnMesh.getPoints(inMeshMPointArray, om.MSpace.kWorld)

            # put each point to a list
            pointList = []

            for i in range(inMeshMPointArray.length()):
                pointList.append(
                    [inMeshMPointArray[i][0], inMeshMPointArray[i][1], inMeshMPointArray[i][2]])

            return pointList

    def getClosestVertex(self, sourcePoint, targetGeo):
        '''
        Description:
            Get a vertex from target geo that is closest to source point in space

        Parameters:
            [in] sourcePoint: tuple of three floats representing arbitrary position in space
            [in] targetGeo: string with a name of maya geo object.

        Returns:
            String with a name of vertex that is the closest to the specified sourcePoint
        '''

        sourcePt = om.MPoint(sourcePoint[0], sourcePoint[1], sourcePoint[2])
        selObj = om.MSelectionList()
        selObj.add(targetGeo)

        targetGeoDag = om.MDagPath()
        selObj.getDagPath(0, targetGeoDag)

        vtxIt = om.MItMeshVertex(targetGeoDag)
        mindist = 10000
        closestPt = om.MPoint()
        vtxId = -1
        while not vtxIt.isDone():
            vtxPt = vtxIt.position(om.MSpace.kWorld)
            dist = vtxPt.distanceTo(sourcePt)
            if dist < mindist:
                mindist = dist
                closestPt = vtxPt
                vtxId = vtxIt.index()
            vtxIt.next()

        return targetGeo + ".vtx[" + str(vtxId) + "]"

    def getClosestCornerVerts(self, cubeCornerVerticesTransforms):
        '''
        Parameters:
            [in] cubeCornerVertqicesTransforms: dictionary where key is a name of vertex and value is a tuple with transforms

        Returns:
            Dictionary where key is a name of a cube corner vertex 
            and value is a name of the vertex from the original object that is the closest.
        '''

        closestCornerVerts = {}
        for cubeVertex in cubeCornerVerticesTransforms:
            closestCornerVerts[cubeVertex] = self.getClosestVertex(
                cubeCornerVerticesTransforms[cubeVertex], self.objectName)

        return closestCornerVerts

    def getComponentNumber(self, component):
        '''
        Description:
            Given a full name of component, return only number of the indice, i.e pSphere1.map[345] will return 345 as integer

        Parameters:
            [in] component: a string with a full name of a component.

        Returns:
            Integer with a number of the component
        '''

        return int(component.rsplit("[", 1)[1].rstrip("]"))

    def extendCuts(self, cutEdges, cornerEdges, indices):
        '''
        Extend the list of cutEdges by a list of edges for all corner edges based on indices of corner edges
        '''

        for i in indices:
            cutEdges.extend(cornerEdges[i])

        return cutEdges

    def removeLongestEdge(self, cornerEdgesLengths, indices):
        '''
        Description:
            Given list of edges (cornerEdges) and a set of indices, get a new set of indices without the index of the longest edge.
        '''

        edgesLengths = [cornerEdgesLengths[i] for i in indices]
        maxLength = max(edgesLengths)
        maxLengthIndex = [i for i, j in enumerate(edgesLengths) if j == maxLength][0]
        indices.remove(indices[maxLengthIndex])

        return indices

    def uvMap(self):

        # apply automatic mapping
        mc.polyAutoProjection(self.objectName, ch=False, lm=0, cm=False, layout=2, scaleMode=1,
                              optimize=1, p=12, ps=0.2)
        # cubinate object
        cubeGeo = cubinate(self.objectName, subdWidth=3, subdHeight=3, subdDepth=3)

        # locate 8 corner vertices based on cubinated object
        cubeVerticesTransforms = self.getVerticesWorldTransform(cubeGeo)

        # the following cube vertex numbers are the corner verts: 0, 1, 2, 3, 4, 5, 6, 7
        cubeCornerVertices = []
        i = 0
        while i < 8:
            cubeCornerVertices.append(cubeGeo + '.vtx[' + str(i) + ']')
            i = i + 1

        # find the closest vertices to corresponding _cube corner vertices
        cubeCornerVerticesTransforms = {}
        for vertex in cubeCornerVertices:
            cubeCornerVerticesTransforms[vertex] = cubeVerticesTransforms[vertex]

        closestCornerVerts = self.getClosestCornerVerts(
            cubeCornerVerticesTransforms)  # dictionary with key a name of cube corner vert and value a name of orig object corner vert that corresponds.

        # get shortest paths between the corner vertices
        # consider the following pairs of corner vertices that form unique edge: 
        cubeEdgeIndices = [(0, 1), (0, 2), (0, 6), (1, 3), (1, 7), (2, 3), (2, 4), (3, 5), (4, 5),
                           (4, 6), (5, 7), (6, 7)]
        cornerEdges = []  # this will store lists of edges that represent shortest paths between closestCornerVerts
        for cubeEdge in cubeEdgeIndices:
            mc.select(self.objectName)
            mc.delete(ch=True)
            cubeVert1 = cubeCornerVertices[cubeEdge[0]]
            cubeVert2 = cubeCornerVertices[cubeEdge[1]]
            cornerVert1 = closestCornerVerts[cubeVert1]
            cornerVert2 = closestCornerVerts[cubeVert2]
            mc.polySelect(shortestEdgePath=[self.getComponentNumber(cornerVert1),
                                            self.getComponentNumber(cornerVert2)])
            path = mc.ls(sl=True, fl=True, l=True)
            if self.objectName in path:
                path.remove(self.objectName)
            cornerEdges.append(path)

        # find the longest of corner edges, that will be the pivotal cut
        cornerEdgesLengths = []
        for cornerEdge in cornerEdges:
            length = sum(self.edgeLengths[edge] for edge in cornerEdge)
            cornerEdgesLengths.append(length)
        # get the index of the longest corner edge
        maxLength = max(cornerEdgesLengths)
        maxLengthIndex = [i for i, j in enumerate(cornerEdgesLengths) if j == maxLength][0]
        mc.select(self.objectName)

        # the longest edge will be the main cutting point, then cut the short edges on both sides according to ideal cube UVs
        cutEdges = cornerEdges[maxLengthIndex]
        # manually add options of cuts based on the index of the longest corner edge
        # on each side of the first long edge we cut only 3 shortest edges. Keep the longest sewn. 
        # This will avoid some thin faces to poke far out from the main shell
        if maxLengthIndex == 0:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [1, 2, 9, 6])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [3, 4, 10, 7])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 1:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [0, 2, 11, 4])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [5, 6, 8, 7])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 2:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [0, 1, 5, 3])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [9, 8, 11, 10])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 3:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [0, 4, 11, 2])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [5, 7, 8, 6])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 4:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [0, 3, 5, 1])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [10, 11, 8, 9])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 5:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [1, 6, 2, 9])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [3, 7, 4, 10])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 6:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [1, 5, 0, 3])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [8, 9, 11, 10])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 7:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [3, 5, 0, 1])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [8, 10, 11, 9])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 8:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [6, 9, 2, 1])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [7, 10, 4, 3])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 9:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [6, 8, 7, 5])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [2, 11, 4, 0])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 10:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [7, 8, 6, 5])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [4, 11, 2, 0])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        elif maxLengthIndex == 11:
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [2, 9, 6, 1])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)
            shortestCornerEdgesIndices = self.removeLongestEdge(cornerEdgesLengths, [4, 10, 7, 3])
            cutEdges = self.extendCuts(cutEdges, cornerEdges, shortestCornerEdgesIndices)

        # template[(0, 1)0, (0, 2)1, (0, 6)2, (1, 3)3, (1, 7)4, (2, 3)5, (2, 4)6, (3, 5)7, (4, 5)8, (4, 6)9, (5, 7)10, (6, 7)11]

        # sew all edges except the cut paths
        edgesToSew = list(set(self.allEdges) - set(cutEdges))
        if edgesToSew:
            mc.polyMapSewMove(edgesToSew, ch=False)

        # cut the UVs that should be cut
        if cutEdges:
            mc.polyMapCut(cutEdges, ch=False)

        # unfold the UVs
        # for some funky reason it's better to run unfold multiple times with lower iteration than once with high iteration
        i = 0
        allUVs = self.getAllUVs(self.objectName)
        while i < 2:
            mc.select(allUVs, r=True)
            #mm.eval('unfold -i 500 -ss 0.001 -gb 0 -gmb 0.5 -pub 0 -ps  0 -oa  0 -us off;')  # for some reason MEL version works better
            mm.eval('u3dUnfold -ite 1 -p 0 -bi 1 -tf 1 -ms 2048 -rs 0')
            #mm.eval('u3dLayout -res 2048 -scl 1 -box 0 1 0 1;')
            mc.select(self.objectName)
            i = i + 1

        # align UVs
        #alignUVShells()

        # rotate UVs in right direction
        #rotateUVShells()

        # delete cube geo
        mc.delete(cubeGeo)

        # layout UVs
        mm.eval("performPolyLayoutUV 0")


def applyCubeUVs():
    selection = mc.ls(sl=True, l=True)
    if not selection:
        raise RuntimeError("Please select at least one object.")
    if '.' in selection[0]:
        raise RuntimeError("Please select objects, not components..")

    # get flat selection of meshes..this will allow user to select groups of meshes as well
    flatSelection = getFlatSelection(selection)

    for sel in flatSelection:
        if isMesh(sel):
            mc.select(sel, r=True)
            # freeze the transforms first - better for cubination
            # mc.makeIdentity(sel, apply=True, t=True, r=True, n=False)
            cubeuv = CubeUVs(sel)
            cubeuv.uvMap()
        else:
            sys.stdout.write("Object %s is not a mesh. Skipping.." % sel)

    mc.select(selection, r=True)


def cubinate(objectName, subdWidth=1, subdHeight=1, subdDepth=1, doShrinkWrap=True, precision=20):
    '''
    Description:
     1. 'Unfreeze' rotation on selected objects and align them with world axis.
     2. Create cube and snap it's vertices to the bounding box of the aligned object.
     3. Align pivot of the cube to the pivot of the original object
     4. Subdivide cube as per users input.
     5. Shrink wrap cube if activated.
     5. Rotate both original object and the newly created cube to it's original position

    Parameters:
        [in] objectName:  name of maya transform node (of a mesh)
        [in] subdWidth:  integer number denoting number of subdivisions in X axis
        [in] subdHeight:  integer number denoting number of subdivisions in Y axis
        [in] subdDepth:  integer number denoting number of subdivisions in Z axis
        [in] doShrinkWrap:  boolean value. if false, no shrinkWrap is performed and the cube will match object's bounding box only 
        [in] precision: integer value with number of iterations to be run when unfreezing rotation on the object

    Returns:
        String with a name of the new cube object
    '''

    selection = mc.ls(sl=True, fl=True, l=True)
    shortName = getShortName(objectName)
    mc.select(objectName, r=True)

    # get the original transforms before unfreezing so we can get back to them
    origTranslate = mc.xform(objectName, q=True, t=True)
    origRotate = mc.xform(objectName, q=True, ro=True)

    # freeze the original object for better result of possible
    mc.makeIdentity(objectName, apply=True, t=True, r=True, n=False)

    rotationToDo = unfreeze(objectName,
                            precision)  # align the original object with axis for creation of the cube
    # do another unfreeze for better precision. It helps in some corner scenarios
    rotationToDo2 = unfreeze(objectName, precision)

    origPivot = mc.xform(objectName, q=True, piv=True, ws=True)

    bbox = mc.polyEvaluate(objectName, b=True)  # ((xmin, xmax), (ymin, ymax), (zmin, zmax))
    xmin = bbox[0][0]
    xmax = bbox[0][1]
    ymin = bbox[1][0]
    ymax = bbox[1][1]
    zmin = bbox[2][0]
    zmax = bbox[2][1]

    # create cube and align vertices with bounding boc of the source object
    cube = mc.polyCube(name=shortName + '_cube')[0]
    mc.polyMoveVertex(cube + '.vtx[0]', ws=True, t=[xmin, ymin, zmax])
    mc.polyMoveVertex(cube + '.vtx[1]', ws=True, t=[xmax, ymin, zmax])
    mc.polyMoveVertex(cube + '.vtx[2]', ws=True, t=[xmin, ymax, zmax])
    mc.polyMoveVertex(cube + '.vtx[3]', ws=True, t=[xmax, ymax, zmax])
    mc.polyMoveVertex(cube + '.vtx[4]', ws=True, t=[xmin, ymax, zmin])
    mc.polyMoveVertex(cube + '.vtx[5]', ws=True, t=[xmax, ymax, zmin])
    mc.polyMoveVertex(cube + '.vtx[6]', ws=True, t=[xmin, ymin, zmin])
    mc.polyMoveVertex(cube + '.vtx[7]', ws=True, t=[xmax, ymin, zmin])

    mc.xform(cube, piv=(origPivot[0], origPivot[1], origPivot[2]), ws=True)

    # cleanup
    mc.select(cube, r=True)
    mc.delete(ch=True)

    # subdivision
    if not (subdWidth == 1 and subdHeight == 1 and subdDepth == 1):
        subdWidth = subdWidth - 1
        subdHeight = subdHeight - 1
        subdDepth = subdDepth - 1
        # subdivide width
        if subdWidth > 0:
            mc.select(cube + '.e[2]', r=True)
            mm.eval('SelectEdgeRing')
            mc.polySplitRing(ch=False, splitType=2, divisions=subdWidth, smoothingAngle=30)
        # subdivide height
        if subdHeight > 0:
            mc.select(cube + '.e[8]', r=True)
            mm.eval('SelectEdgeRing')
            mc.polySplitRing(ch=False, splitType=2, divisions=subdHeight, smoothingAngle=30)
        # subdivide depth
        if subdDepth > 0:
            mc.select(cube + '.e[6]', r=True)
            mm.eval('SelectEdgeRing')
            mc.polySplitRing(ch=False, splitType=2, divisions=subdDepth, smoothingAngle=30)

    # shrink wrap
    if doShrinkWrap:        
        shrinkWrapNode = pm.deformer(cube, type='shrinkWrap')[0]
        pm.PyNode(objectName).worldMesh[0] >> shrinkWrapNode.targetGeom
        shrinkWrapNode.closestIfNoIntersection.set(True)
        shrinkWrapNode.projection.set(3)

    # rotate the original object and the new cube back
    mc.rotate(-rotationToDo2[0], -rotationToDo2[1], -rotationToDo2[2], objectName, r=True, os=False,
              eu=True)  #
    mc.rotate(-rotationToDo2[0], -rotationToDo2[1], -rotationToDo2[2], cube, r=True, os=False,
              eu=True)  #
    mc.makeIdentity(objectName, apply=True, r=True, n=False)
    mc.makeIdentity(cube, apply=True, r=True, n=False)
    mc.rotate(-rotationToDo[0], -rotationToDo[1], -rotationToDo[2], objectName, r=True, os=False,
              eu=True)  #
    mc.rotate(-rotationToDo[0], -rotationToDo[1], -rotationToDo[2], cube, r=True, os=False,
              eu=True)  #

    # get back to the original transforms
    mc.makeIdentity(objectName, apply=True, t=True, r=True, n=False)
    applyStaticTransforms(objectName, tx=origTranslate[0], ty=origTranslate[1], tz=origTranslate[2],
                          rx=origRotate[0], ry=origRotate[1], rz=origRotate[2])

    mc.select(selection, r=True)

    return cube


def applyStaticTransforms(node, tx=0, ty=0, tz=0, rx=0, ry=0, rz=0):
    '''
    Description:
        Apply arbitrary input transforms (translate and rotate only) onto a node (maya transform node) 
        without actually moving or rotating the object in any way.
        NOT FINISHED FUNCTION, ROTATION SOMETIMES DOESN'T WORK AS EXPECTED
    Parameters:
        [in] node:  name of Maya transform node
        [in] tx: target value for translate X
        [in] ty: target value for translate Y
        [in] tz: target value for translate Z
        [in] rx: target value for rotate X
        [in] ry: target value for rotate Y
        [in] rz: target value for rotate Z

    Returns:
        None
    '''

    # don't do this to assets as their transforms can't be frozen
    if isAsset(node):
        return

    # freeze transforms except scale
    mc.makeIdentity(node, apply=True, t=True, r=True, n=False)
    # apply negative values of the target translate and rotation.
    mc.xform(node, t=[-tx, -ty, -tz])
    mc.xform(node, ro=[-rx, -ry, -rz])

    # freeze translate and rotate again
    mc.makeIdentity(node, apply=True, t=True, r=True, n=False)
    # apply target transforms
    mc.xform(node, t=[tx, ty, tz])
    mc.rotate(0, 0, rz, node, r=True, os=False)
    mc.rotate(0, ry, 0, node, r=True, os=False)
    mc.rotate(rx, 0, 0, node, r=True, os=False)


def unfreeze(node, precision=20):
    '''
    Description:
        Unfreeze rotation of an object (node) by finding a rotation of the object where the bounding box would have smallest volume.
        This happens only when the object is perfectly aligned in all axis. Find the smallest volume bbox with binary search tree.

    Parameers:
        [in] node: String with a name of the object to be unfrozen
        [in] precision:  integer value with number of iterations to be run when unfreezing rotation on the object

    Returns:
        Rotation values (tuple of three floats) that were performed to get the object into a position perfectly aligned with all axis
    '''

    mc.delete(node, ch=True)  # delete history first, otherwise would get a lot of extra transforms
    mc.makeIdentity(node, apply=True, r=True, n=False)
    bbox = mc.exactWorldBoundingBox(node)
    rotationToDo = [0, 0, 0]  # this will hold final calculated rotation values
    initialVolume = abs(bbox[3] - bbox[0]) * abs(bbox[4] - bbox[1]) * abs(bbox[5] - bbox[2])

    def testVolume(axis, value, node):
        '''
        This function is part of unfreeze function.
        Return volume of a node's bounding box after rotating it by 'value' in specified 'axis'
        '''

        if axis == 'x':
            mc.rotate(value, 0, 0, r=True, os=False)
        elif axis == 'y':
            mc.rotate(0, value, 0, r=True, os=False)
        elif axis == 'z':
            mc.rotate(0, 0, value, r=True, os=False)

        mc.makeIdentity(apply=True, r=True, n=False)
        bbox = mc.exactWorldBoundingBox(node)
        volume = abs(bbox[3] - bbox[0]) * abs(bbox[4] - bbox[1]) * abs(bbox[5] - bbox[2])

        if axis == 'x':
            mc.rotate(-value, 0, 0, r=True, os=False)
        elif axis == 'y':
            mc.rotate(0, -value, 0, r=True, os=False)
        elif axis == 'z':
            mc.rotate(0, 0, -value, r=True, os=False)
        mc.makeIdentity(apply=True, r=True, n=False)

        return volume

    def align(node, precision, axis):
        '''
        This function is part of unfreeze function.
        Use of binary search tree to guess the correct alignment by iteratively testing for bbox volumes and finding the smallest volumes.
        The value of precision represents the depth of the search tree.
        '''
        if testVolume(axis, 1.0, node) < testVolume(axis, -1.0, node):
            j = 45.0
            k = 22.5
        else:
            j = -45.0
            k = -22.5
        for v in range(0, precision):
            a = testVolume(axis, k - ((abs(k - j)) / 2.0), node)
            b = testVolume(axis, k + ((abs(k - j)) / 2.0), node)
            if a < b:
                tmp = j
                j = k
                k = (k - ((abs(k - tmp)) / 2.0))
            else:
                tmp = j
                j = k
                k = (k + ((abs(k - tmp)) / 2.0))
        if axis == 'x':
            mc.rotate(k, 0, 0, node, r=True, os=False)
        elif axis == 'y':
            mc.rotate(0, k, 0, node, r=True, os=False)
        elif axis == 'z':
            mc.rotate(0, 0, k, node, r=True, os=False)
        mc.makeIdentity(node, apply=True, r=True, n=False)

        return k

    rotationToDo[2] = align(node, precision, 'z')
    rotationToDo[1] = align(node, precision, 'y')
    rotationToDo[0] = align(node, precision, 'x')

    return rotationToDo


def isMesh(node):
    '''
    Description:
        Return true if the input node is mesh, otherwise return false. This is found by checking nodeType of the shape node

    Parameters:
        [in] node: string with a name of any maya node

    Returns:
        True if input node is a mesh or transform node of a mesh, False otherwise
    '''

    if mc.nodeType(node) == 'mesh':
        return True

    shapeNodes = dag.getShapesOfType(node)
    if shapeNodes:
        if mc.nodeType(shapeNodes[0]) == 'mesh':
            return True
    else:
        return False


def isAsset(node):
    '''
    Description:
        If the input node is assetModel, layout, expanded layout return True, 
        otherwise return False.

    Parameters:
        [in] node: string with a name of the transform node of maya objectName

    Returns:
        True if input node is asset, False otherwise
    '''

    children = mc.listRelatives(node, children=True)
    for child in children:
        if child.endswith("Info") or child.endswith("Expand"):
            return True

    return False


def getFlatSelection(nodes):
    '''
    input: list of maya objects
    output: flat list of objects where all children will be listed separately
    Only transform nodes will be outputed
    '''
    nodes_flat = []
    # sometimes the input might be single object
    if isinstance(nodes, str):
        node = nodes
        nodes_flat.append(node)
        children = mc.ls(
            mc.listRelatives(node, fullPath=True, allDescendents=True, type='transform'), long=True)
        if children:
            for child in children:
                nodes_flat.append(child)
    else:
        # case where input is list of objects
        for node in nodes:
            nodes_flat.append(node)
            children = mc.ls(
                mc.listRelatives(node, fullPath=True, allDescendents=True, type='transform'),
                long=True)
            if children:
                for child in children:
                    nodes_flat.append(child)

    nodes_flat = list(set(nodes_flat))
    return nodes_flat


def getShortName(name):
    '''
    Description: 
        Return a short name of maya node, i.e the last part of the name after the last '|' character.
    Parameters:
        [in] name:  string with either short or long maya name
    Returns:
        String with a short name
    '''

    if '|' in name:
        short_name = name.rsplit("|", 1)[1]
        return short_name
    else:
        return name
