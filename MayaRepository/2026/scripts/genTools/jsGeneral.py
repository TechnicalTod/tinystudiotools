''' This module contains general higher level methods for Maya and some methods outside of Maya'''

import re
import math
import maya.cmds as mc
import maya.mel as mm

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
        a = testVolume(axis, k-((abs(k-j))/2.0), node)
        b = testVolume(axis, k+((abs(k-j))/2.0), node)
        if a < b:
            tmp = j
            j = k
            k = (k-((abs(k-tmp))/2.0))  
        else:
            tmp = j
            j = k
            k = (k+((abs(k-tmp))/2.0))
    if axis == 'x':
        mc.rotate(k, 0, 0, node, r=True, os=False)
    elif axis == 'y':
        mc.rotate(0, k, 0, node, r=True, os=False)
    elif axis == 'z':
        mc.rotate(0, 0, k, node, r=True, os=False)
    mc.makeIdentity(node, apply=True, r=True, n=False)

    return k


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

    #don't do this to assets as their transforms can't be frozen
    if isAsset(node):
        return

    #freeze transforms except scale
    mc.makeIdentity(node, apply=True, t=True, r=True, n=False)
    #apply negative values of the target translate and rotation.
    mc.xform(node, t=[-tx, -ty, -tz])    
    mc.xform(node, ro=[-rx, -ry, -rz])

    #freeze translate and rotate again
    mc.makeIdentity(node, apply=True, t=True, r=True, n=False)
    #apply target transforms
    mc.xform(node, t=[tx, ty, tz])
    mc.rotate(0, 0, rz, node, r=True, os=False)
    mc.rotate(0, ry, 0, node, r=True, os=False)
    mc.rotate(rx, 0, 0, node, r=True, os=False)
    
    

def cubinate(objectName, subdWidth=1, subdHeight=1, subdDepth=1, doShrinkWrap=True, precision = 20):
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

    #get the original transforms before unfreezing so we can get back to them
    origTranslate = mc.xform(objectName, q=True, t=True)
    origRotate = mc.xform(objectName, q=True, ro=True)

    #freeze the original object for better result of possible
    mc.makeIdentity(objectName, apply=True, t=True, r=True, n=False)
    
    rotationToDo = unfreeze(objectName, precision)  #align the original object with axis for creation of the cube
    #do another unfreeze for better precision. It helps in some corner scenarios
    rotationToDo2 = unfreeze(objectName, precision)

    origPivot = mc.xform(objectName, q=True, piv=True, ws=True)

    bbox = mc.polyEvaluate(objectName, b=True)  #((xmin, xmax), (ymin, ymax), (zmin, zmax))
    xmin = bbox[0][0]
    xmax = bbox[0][1]
    ymin = bbox[1][0]
    ymax = bbox[1][1]
    zmin = bbox[2][0]
    zmax = bbox[2][1]

    #create cube and align vertices with bounding boc of the source object
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

    #cleanup
    mc.select(cube, r=True)
    mc.delete(ch=True)
    
    #subdivision
    if not (subdWidth == 1 and subdHeight == 1 and subdDepth == 1):
        subdWidth = subdWidth - 1
        subdHeight = subdHeight - 1
        subdDepth = subdDepth - 1
        #subdivide width
        if subdWidth > 0:
            mc.select(cube + '.e[2]', r=True)
            mm.eval('SelectEdgeRing')
            mc.polySplitRing(ch=False, splitType=2, divisions = subdWidth, smoothingAngle=30)
        #subdivide height
        if subdHeight > 0:
            mc.select(cube + '.e[8]', r=True)
            mm.eval('SelectEdgeRing')
            mc.polySplitRing(ch=False, splitType=2, divisions = subdHeight, smoothingAngle=30)
        #subdivide depth
        if subdDepth > 0:
            mc.select(cube + '.e[6]', r=True)
            mm.eval('SelectEdgeRing')
            mc.polySplitRing(ch=False, splitType=2, divisions = subdDepth, smoothingAngle=30)

    #shrink wrap
    if doShrinkWrap:
        mc.select(cube, r=True)
        mc.select(objectName, add=True)
        mm.eval('{source \"/weta/prod/models/scripts/publicDomain/xyShrinkWrap.mel\";\nxyShrinkWrap;}')

    #rotate the original object and the new cube back
    mc.rotate(-rotationToDo2[0], -rotationToDo2[1], -rotationToDo2[2], objectName, r=True, os=False, eu=True)#
    mc.rotate(-rotationToDo2[0], -rotationToDo2[1], -rotationToDo2[2], cube, r=True, os=False, eu=True)#
    mc.makeIdentity(objectName, apply=True, r=True, n=False)
    mc.makeIdentity(cube, apply=True, r=True, n=False)
    mc.rotate(-rotationToDo[0], -rotationToDo[1], -rotationToDo[2], objectName, r=True, os=False, eu=True)#
    mc.rotate(-rotationToDo[0], -rotationToDo[1], -rotationToDo[2], cube, r=True, os=False, eu=True)#

    #get back to the original transforms
    mc.makeIdentity(objectName, apply=True, t=True, r=True, n=False)
    applyStaticTransforms(objectName, tx=origTranslate[0], ty=origTranslate[1], tz=origTranslate[2], rx=origRotate[0], ry=origRotate[1], rz=origRotate[2])

    mc.select(selection, r=True)

    return cube


def getDistance(p1, q1):
    '''
    get distance between point1 and point 2. Each point is an array of x, y and z coordinates
    '''

    return math.sqrt((math.pow(p1[0] - q1[0], 2) + math.pow(p1[1] - q1[1], 2) + math.pow(p1[2] - q1[2], 2)))


def fixShapeNodes(nodes):
    '''
    Description:
        Fix Shape nodes so that any characters after the word 'Shape' will be before

    Parameters:
        [in] nodes: Either string with a shape name or list of strings with shape names

    Returns: None
    '''

    basestring = str

    #case of string as input
    if isinstance(nodes, basestring):
        node_short = getShortName(nodes)
        if 'Shape' in node_short:
            prefix, suffix = node_short.rsplit("Shape", 1)
            if suffix:
                new_shape = prefix + suffix + 'Shape'
                mc.rename(nodes, new_shape)
                print ("Renamed %s to %s" %(nodes, new_shape))

    #case of list as input
    else:
        for node in nodes:
            node_short = getShortName(node)
            if 'Shape' in node_short:
                prefix, suffix = node_short.rsplit("Shape", 1)
                if suffix:
                    new_shape = prefix + suffix + 'Shape'
                    mc.rename(node, new_shape)
                    print ("Renamed %s to %s" %(node, new_shape))


def getFlatSelection(nodes):
    '''
    input: list of maya objects
    output: flat list of objects where all children will be listed separately
    Only transform nodes will be outputed
    '''
    nodes_flat = []
    nodes = list(nodes)

    for node in nodes:
        nodes_flat.append(node)
        children = mc.ls(mc.listRelatives(node, fullPath = True, allDescendents = True, type = 'transform'), long=True)
        if children:
            for child in children:
                nodes_flat.append(child)

    nodes_flat = list(set(nodes_flat))
    return nodes_flat
        

def getFlatSelectionBreadthFirst(nodes):
    '''
    Description:
        Given a list of maya nodes, return flat list of all objects in the hierarchy, with breadth first search - parents first
    Parameters:
        [in] nodes: maya nodes - name of objects
    Returns:
        flat list of objects where all children all listed separately, parents first and then children
    '''

    return sorted(getFlatSelection(nodes), key = lambda x: x.count("|"))


def getShapeNodes(nodes):
    '''input: list of maya objects
    output: flat list of all shape nodes associated with input objects
    '''
    shape_nodes = []
    basestring = str

    #make it work if the input is a single object as a string
    if isinstance(nodes, basestring):
        node = nodes
        shape_node = mc.listRelatives(node, allDescendents=False, type = 'shape', f=True)
        if shape_node:
            for shape in shape_node:
                shape_nodes.append(shape)
    
    #case where input is a list
    else:
        for node in nodes:
            shape_node = mc.listRelatives(node, allDescendents=False, type = 'shape', f=True)
            if shape_node:
                for shape in shape_node:
                    shape_nodes.append(shape)

    shape_nodes = list(set(shape_nodes))
    return shape_nodes


def getMeshes(nodes):
    '''input: list of maya objects
    output: flat list of all meshes within the input nodes or their children
    '''

    meshes = []
    nodes_flat = []
    for node in nodes:
        nodes_flat.extend(getFlatSelection(node))
    for node in nodes_flat:
        shape_nodes = getShapeNodes(node)
        if shape_nodes:
            if mc.nodeType(shape_nodes[0]) == 'mesh':
                meshes.append(node)

    return meshes


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


def incrementString(incrString):
    '''
    Description:
        Increment an arbitrary string. If there was a number at the end of the string, increment it by one.
        If there was no number at the end, suffix the string with "_2".
    Parameters:
        [in] incrString:  any string
    Returns:
        Incremented string, for example incrementString("abc123") == "abc124", incrementString("abc") == "abc_2"
    '''

    m = re.search('(_\d+)$', incrString)
    #case where we found number at the end of te filename
    if m:
        return incrString[0:-len(m.group(0))] + '_' + str(int(m.group(0)[1:]) + 1)
    #case where there is no number at the end of the filename
    else:
        return incrString + '_2'


def incrementImagePath(imagePath):
    '''
    Description:
        Given input image path, return output path that is incremented by one. If the input path had a number at the end (before the suffix), just increment the number.
        Otherwise create new increment by suffixing '_2'.
    Input:
        [in] imagePath:  string with complete image path including file extension
    Output:
        Same as input but incremented by one.
    '''

    filename, extension = os.path.splitext(imagePath)
    m = re.search('(\d+)$', filename)
    #case where we found number at the end of te filename
    if m:
        number = int(m.group(0))
        padding = len(str(m.group(0))) - len(str(number))
        filename = filename[0:-len(m.group(0))] + (padding * '0') + str(number + 1)
        imagePath = filename + extension
    #case where there is no number at the end of the filename
    else:
        imagePath = filename + '_2' + extension
    print ("Incremented image path: {0}".format(imagePath))

    #check the new imagePath doesn't exist yet. If it does, try incrementing again, until the imagePath is unique
    if os.path.isfile(imagePath):
        print ("File already exists on disk, incrementing again..")
        imagePath = incrementImagePath(imagePath)

    return imagePath


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

    children = mc.listRelatives(node, children = True)
    for child in children:
        if child.endswith("Info") or child.endswith("Expand"):
            return True

    return False


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

    shapeNodes = getShapeNodes(node)
    if shapeNodes:
        if mc.nodeType(shapeNodes[0]) == 'mesh':
            return True
    else:
        return False 


def isTexturePublished(texturePath):
    '''
    Description:
        Return True if the input texture is published (i.e. lives in publish directory), False otherwise
    Parameters:
        [in] texturePath:  string containing full path to the texture
    Returns:
        bool
    '''

    if ('/textures/hero' in texturePath) or ('/textures/previs' in texturePath):
        return True
    else:
        return False


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
    volume = abs(bbox[3]-bbox[0])*abs(bbox[4]-bbox[1])*abs(bbox[5]-bbox[2])
    
    if axis == 'x':
        mc.rotate(-value, 0, 0, r=True, os=False)
    elif axis == 'y':
        mc.rotate(0, -value, 0, r=True, os=False)
    elif axis == 'z':
        mc.rotate(0, 0, -value, r=True, os=False)   
    mc.makeIdentity(apply=True, r=True, n=False)
    
    return volume


def unfreeze(node, precision):
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

    mc.delete(node, ch=True)  #delete history first, otherwise would get a lot of extra transforms
    mc.makeIdentity(node, apply=True, r=True, n=False)
    bbox = mc.exactWorldBoundingBox(node)
    rotationToDo = [0,0,0]  #this will hold final calculated rotation values
    initialVolume = abs(bbox[3]-bbox[0])*abs(bbox[4]-bbox[1])*abs(bbox[5]-bbox[2])
    
    rotationToDo[2] = align(node, precision, 'z')
    rotationToDo[1] = align(node, precision, 'y')
    rotationToDo[0] = align(node, precision, 'x')
    
    return rotationToDo


