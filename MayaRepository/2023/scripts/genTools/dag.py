from typeUtils import fi, li, asList
import maya.cmds as mc
from maya import OpenMaya

def getParentOfType(node, validTypes, invalidTypes=None, allParents=True, topParent=True):

    results = None

    validTypes = asList(validTypes)
    invalidTypes = asList(invalidTypes)

    parent = node
    while parent:
        parent = fi(mc.listRelatives(parent, fullPath=True, parent=True))
        if parent:
            for shape in asList(mc.listRelatives(parent, fullPath=True, shapes=True)):

                if mc.objectType(shape) in validTypes:  # The parent node is a valid type
                    results = parent
                    break

                elif mc.objectType(shape) in invalidTypes:
                    # They are trying to convert a child of a invalid node
                    print ('The parent node is invalid:', parent)

        # If we only want to look immediate parent then look no further
        if not allParents:
            break

        # If we found a results and were only intersted in the first match then look no further
        if results and not topParent:
            break

    return results


def getAncestors(nodes):
    '''
    Description:
        Gets ancestors (all parents up to assembly level) of a node or list of nodes.

    Parameters:
        [in] node list for which to get ancestors

    Returns:
        List of ancestors or empty list if none
    '''

    nodes = asList(nodes)
    results = []

    for node in nodes:
        parent = node
        while parent:
            parent = fi(mc.listRelatives(parent, fullPath=True, parent=True))
            if parent and parent not in results:
                results.append(parent)

    return results

def hasSelectedAncestor(node):
    '''
    Description:
        Return True if the specified node is selected, or has any selected ancestors.
        Otherwise return False.

    Returns:
        Boolean
    '''
    for ancestor in ([node] + getAncestors(node)):
        if mc.ls(ancestor, selection=True):
            return True
    return False

def getTransformsAndShapes(nodes, shapeType=None, exactShapeType=None):
    '''
    Description:
        Return the transforms and shapes from the given nodes

        Useful when operating on something where the connection could be
        applied to either the transform or the shape. i.e. shader assignments

    Parameters:
        [in] nodes: nodes to get transforms and shapes for
        [in] shapeType: only shapes with this type will be returned
        [in] exactShapeType: only shapes with this exact type will be returned

    Returns:
        A list of trasnforms and shapes
    '''

    results = []

    for node in asList(nodes):
        # Get the full path to node
        node = fi(mc.ls(node, long=True))

        # Get the transform if a shape was given
        if mc.objectType(node, isAType='shape'):
            node = fi(mc.listRelatives(node, fullPath=True, parent=True))

        # If the node exists throw it into the results
        if mc.objExists(node):
            if node not in results:
                results.append(node)

            # Add any shapes to the results if the node is a transform
            if mc.objectType(node, isAType='transform'):
                for shape in asList(mc.listRelatives(node, fullPath=True, shapes=True)):
                    if (shapeType is None or mc.objectType(shape, isAType=shapeType)) and (exactShapeType is None or mc.objectType(shape, isAType=exactShapeType)):
                        if shape not in results:
                            results.append(shape)

    return results


def getNearestNode(nodes, nodeType='wmAssetModel'):
    '''
        Description:
            used to find a node of a particular type in the current objects tree

            It first searches the children for a node matching nodeType
            if that fails it searches the children of each of the items
            parents in order for a node of type nodeType

            This is most useful when searching for a node in the hierarchy
            based on an artists selection

        Parameters:
            [in] nodes: object to search from

        Returns:
            Maya node found of type 'nodeType'
    '''
    def __getParents__(obj, _otherParents=[]):
        '''
        returns all the parents of a given dag object node

        obj = the object to check for parents
        otherParents = should be an empty list
        '''
        parent = mc.listRelatives(obj, ap=True, f=True)
        if not parent:
            return _otherParents
        else:
            _otherParents += parent
            return __getParents__(parent, _otherParents)

    nodes = asList(nodes)[0]

    if not mc.objExists(nodes):
        print ('object does not exist %s' % nodes)
        return None

    # check object selected if it is the model node return it
    if mc.objectType(nodes, isType=nodeType):
        return nodes

    # check children for model node, returns the first one found
    objSearchDown = mc.listRelatives(nodes, allDescendents=True, type=nodeType, f=True, ni=True)
    if objSearchDown:
        return objSearchDown[0]

    # check parents, then parents children for model node
    parents = __getParents__(nodes)
    if parents:
        objSearchDown = mc.listRelatives(parents, allDescendents=True, type=nodeType, f=True)
        if objSearchDown:
            return objSearchDown[0]


def getShapesOfType(nodes=None, type='mesh', defaultToAllShapesOfType=False):
    '''
    from getMeshShapes

    returns the selected nodes shape or shapes under meshShapes and all decendants
    ported over from patricks wmAssetBakingModelingTools
    '''
    if not nodes:
        sel = mc.ls(type=type, dag=True, l=True, ni=True, sl=True)
        if sel:
            return sel
        else:
            if defaultToAllShapesOfType:
                mc.warning('Nothing Selected, Using all ' + str(type) + ' nodes')
                return mc.ls(type=type, dag=True, l=True, ni=True)
            else:
                return []
    else:
        return mc.ls(nodes, type=type, dag=True, l=True, ni=True)


def isMesh(node):
    '''
    Description:
        Return true if the input node is mesh, false otherwise. This is found by checking nodeType of the shape node

    Parameters:
        [in] node: string with a name of any maya node

    Returns:
        True if input node is a mesh or transform node of a mesh, False otherwise
    '''

    if mc.nodeType(node) == 'mesh':
        return True

    transformAndShapes = getTransformsAndShapes(node)
    if len(transformAndShapes) < 2:
        return False

    if mc.nodeType(transformAndShapes[1]) == 'mesh':
        return True

    return False


def makeShapeNamesUnique(transformNodes=None):
    ''' ported over from patricks wmAssetBakingModelingTools '''
    # remove underworld nodes & dodgy shape nodes
    removeUnderworldNodes()
    removeDodgyShapeNodes()

    # get a list of all shape names
    shapes = getShapesOfType(transformNodes)

    # get a list of things to number
    doneList = {}

    # cycle all shape nodes
    for shapeLongName in shapes:

        # get the shape short name and basename
        shapePath, shapeName = shapeLongName.rsplit("|", 1)
        stripedName = shapeName.strip('1234567890')
        stripedName = stripedName.replace('Shape', '')
        stripedName = stripedName.strip('1234567890')
        stripedName = stripedName.replace('Shape', '')

        # get unique number and newShapeName
        doneList.setdefault(stripedName, 0)
        doneList[stripedName] += 1
        num = str(doneList[stripedName])
        newShapeName = stripedName + num + 'Shape'

        # rename the shapes to the newShapeName
        print ('renaming:', shapeLongName, 'to', newShapeName)
        # renamedShape = mc.rename(shapeLongName, newShapeName)

    # reget the shapes with the new names so we can rename the transform nodes
    shapes = getShapesOfType(transformNodes)

    # cycle through the shapes in reversed order to change the transform nodes
    for shapeLongName in reversed(shapes):

        # get the parent of the shape
        transform = mc.listRelatives(shapeLongName, p=True, f=True)

        # if the parent of the shape is a transform node
        # rename the transform to the name of the shape node
        if mc.nodeType(transform) == 'transform':

            shapePath, shapeName = shapeLongName.rsplit("|", 1)
            # newTransformName = shapeName.replace('Shape', '')
            # renamedTransform = mc.rename(transform, newTransformName, ignoreShape=True)


def removeDodgyShapeNodes(remove=True):
    '''
    Function from Patricks utils to remove dodgy shape nodes
    '''
    selPatch = mc.ls(type='nurbsSurface', io=True)
    selMesh = mc.ls(type='mesh', io=True)

    dodgyShapes = []
    for sel in selPatch:
        if not mc.connectionInfo(sel + '.worldSpace', isSource=True) and not mc.connectionInfo(sel + '.local', isSource=True):
            dodgyShapes.append(sel)

    for sel in selMesh:
        if not mc.connectionInfo(sel + '.worldMesh', isSource=True) and not mc.connectionInfo(sel + '.outMesh', isSource=True):
            dodgyShapes.append(sel)

    if dodgyShapes:
        print ('Found dodgy shapes ', dodgyShapes)
        if remove:

            print ('Removing dodgy shapes')
            mc.delete(dodgyShapes)

        return dodgyShapes


def removeUnderworldNodes():
    '''
    Function from Patricks utils to rename remove underworld nodes
    '''
    for node in sorted(mc.ls(long=True), reverse=True):
        if '->' in node:
            mc.delete(node)


def filterbyType(objectList=None, selectionMask=[9, 68], fullPath=True):
    '''
    Description:
    Filter a list by type, So simple it hurts

    Parameters:
        [in]    objectList:         A list Of object to filter
        [in]    selectionMask:      A list of types to filter the object List by

        Possible Object Types
        Handle                      0
        Nurbes Curves               9
        Nurbs Surfaces              10
        Nurbs Curves On a Surfaces  11
        Polygons                    12
        LocatorXYZ                  22
        Orientation Locator         23
        Locator UV                  24
        Control Vertices            28
        Edit Points                 30
        Polygon Vertices            31
        Polygon Edges               32
        Polygon Face                34
        Polygon UV's                35
        Subdivision Mesh Points     36
        Subdivision Mesh Edges      37
        Subdivision Mesh Faces      38
        Curve Parameter Points      39
        Curve Knot                  40
        Surface Parameter Points    41
        Surface Knot                42
        Surface Range               43
        Trim Surface Edge           44
        Surface Isoparms            45
        Lattice Points              46
        Particles                   47
        Scale Pivots                49
        Rotate Pivots               49
        Select Handles              51
        Subdivision Surface         68
        Polygon Vertex Face         70
        Nurbs Surface Face          72
        Subdivision Mesh UV's       73

    Returns:
        [out]   filteredObjs:           A list containing only the types requested

    Examples:
    import mo.wm.utils.model
    test = mo.wm.utils.model.filterbyType(selectedObjs, selectionMask=[9,68])

    '''

    # Get the users selection
    usersSelection = mc.ls(sl=True, flatten=True)

    # If objectList was not provided, use what is currentyl selected
    if not objectList:
        objectList = usersSelection[:]
    else:
        mc.select(objectList, replace=True)

    # Filter what is selected based on functions arguments
    filteredObjs = mc.filterExpand(sm=(selectionMask), fp=True)

    # Return the users selection
    if usersSelection:
        mc.select(usersSelection, replace=True)
    else:
        mc.select(clear=True)

    return filteredObjs


def removeObjFromLayer(myObj):
    '''
    Description:
        Remove given Objs from displayLayers

    Parameters:
        [in] myObj: The objects you want to remove from display lyaers

    Returns:
        None

    Examples:
        import mo.wm.utils.model
        mo.wm.utils.model.removeObjFromLayer(selected)

    '''
    mc.editDisplayLayerMembers('defaultLayer', myObj)


def delSetsFromScene():
    '''
    Description:
        Delete all sets from the scene, dont even try to delete the default
        Parameters:

    Returns:
    [out]   setsDeleted:    The sets which were deleted

    Examples:
        import mo.wm.utils.model
        mo.wm.utils.model.delSetsFromScene()
    '''
    sceneObjSets = mc.ls(type='objectSet')
    sceneShadingSets = mc.ls(type='shadingEngine')
    removeMe = ['defaultLightSet', 'defaultObjectSet', 'initialParticleSE', 'initialShadingGroup']

    setsDeleted = []
    objSets = sceneObjSets + sceneShadingSets

    for item in range(len(objSets)):
        if not objSets[item] in removeMe:
            mc.delete(objSets[item])
            setsDeleted.append(objSets[item])

    return setsDeleted


def renameShapeNodes(assetName, rootNodes=None, renameLogPath=None):
    '''
    Function from Patricks utils to rename shape nodes
    '''
    # get a list of everything, dag will return the shapes in scene order
    shapes = mc.ls(type=['mesh', 'nurbsCurve'], l=True, dag=True)
    if rootNodes:
        # get the nodes under rootnodes to rename
        selShapes = mc.listRelatives(rootNodes, ad=True, type=['mesh', 'nurbsCurve'], f=True)
        # using the shapes above ensures that the nodes will be numbered in scene order
        shapes = [i for i in shapes if i in selShapes]

    outList = []

    # cycle all shape nodes
    for i, shapeLongName in enumerate(shapes):

        # get the shape short name
        shapeName = li(shapeLongName.rsplit('|', 1))

        # if the asset name has a number put an underscore in the new name
        if assetName[-1:].isdigit():
            newShapeName = assetName + '_' + str(i + 1) + 'Shape'
        # else name it without the underscore Shape
        else:
            newShapeName = assetName + str(i + 1) + 'Shape'

        # rename the shapes to the newShapeName
        renamedShape = mc.rename(shapeLongName, newShapeName)

        # append the named shapes to the output log
        outList.append(str([shapeLongName, renamedShape]) + '\n')

    # reget the shapes with the new names so we can rename the transform nodes
    shapes = mc.ls(type=['mesh', 'nurbsCurve'], l=True, dag=True)
    if rootNodes:
        selShapes = mc.listRelatives(rootNodes, ad=True, type=['mesh', 'nurbsCurve'], f=True)
        shapes = [i for i in shapes if i in selShapes]

    # cycle through the shapes in reversed order to change the transorm nodes
    for shapeLongName in reversed(shapes):

        # get the parent of the shape
        transform = mc.listRelatives(shapeLongName, p=True, f=True)

        # if the parent of the shape is a transform node
        # rename the transform to the name of the shape node
        if mc.nodeType(transform) == 'transform':

            shapeName = li(shapeLongName.rsplit('|', 1))
            newTransformName = shapeName.replace('Shape', '')
            mc.rename(transform, newTransformName)

    # save the log file if output specified
    if renameLogPath:
        f = open(renameLogPath, 'w')
        f.writelines(outList)
        f.close()


def setDagPath(dagPath, node):
    """
    Description:
        sets a dag path to the given node

    input:
        [string] dagPath: The dag path to set
        [string] node:    The node to use
    """
    mSelectionList = OpenMaya.MSelectionList()
    mSelectionList.add(node)
    mSelectionList.getDagPath(0, dagPath)

