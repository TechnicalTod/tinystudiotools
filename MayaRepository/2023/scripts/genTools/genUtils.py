from PySide2 import QtGui, QtWidgets, QtCore
import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

def warningPopup(message):
    selectionWarningDialog = QtWidgets.QMessageBox()
    selectionWarningDialog.setText(message)
    selectionWarningDialog.setWindowTitle("Warning")
    selectionWarningDialog.exec_()
    print (message)

def viewportMessage(StandardMessage, BoldMessage, boldFontColor):
    fontColor = boldFontColor
    message = StandardMessage + '<span style=\"color:{};text-decoration:bold;\">'.format(fontColor) + BoldMessage + '</span>'
    mc.inViewMessage(amg=message, pos='midCenter', fade=True)

def switch_shelf(shelf_name):
    """
    Switch to the specified shelf in Maya.
    
    :param shelf_name: The name of the shelf to switch to.
    """
    shelf_layouts = mc.lsUI(type="shelfLayout")
    if shelf_name in shelf_layouts:
        mc.setParent("ShelfLayout")
        mc.shelfTabLayout("ShelfLayout", e=True, selectTab=shelf_name)
    else:
        print(f"Shelf '{shelf_name}' not found.")

def centerPivot():
    mc.CenterPivot()

def combineObjects(nodes=None):
    '''
    combines two objects while keeping the old name and hierarchy
    '''

    sel = mc.ls(sl=True, l=True)

    selShort = mc.ls(sel)
    children = mc.listRelatives(sel, ad=True, type='mesh')
    parent = mc.listRelatives(sel, f=True, parent=True)
    parentsParent = mc.listRelatives(parent, f=True, parent=True)

    newObj = mc.polyUnite(sel, caching=0, constructionHistory=1, name=selShort[0])

    if parent:
        if mc.objExists(parent[0]):
            mc.parent(newObj[0], parent)

    mc.DeleteHistory(newObj)

def createLocAtPivot():
    sel = mc.ls(sl = 1)

    for obj in sel:
        newLoc = mc.spaceLocator(n='{0}_LOC'.format(sel))
        newCon = mc.parentConstraint(obj, newLoc, mo = 0)
        mc.delete(newCon)

def deleteHistory():
    sel = mc.ls(sl=1)
    if len(sel) > 0:
        mc.DeleteHistory()
    else:
        mc.DeleteAllHistory()

def deleteAllNameSpaces():
    namespaces = []
    for ns in pm.listNamespaces( recursive  =True, internal =False):
        namespaces.append(ns)
        print ('Namespace ' + ns + ' added to list.')
    # Reverse Iterate through the contents of the list to remove the deepest layers first
    for ns in reversed(namespaces):
        currentSpace = ns
        pm.namespace(removeNamespace = ns, mergeNamespaceWithRoot = True)
        print (currentSpace + ' has been merged with Root!')
    # Empty the List
    namespaces[:] = []

def deleteAllDisplayLayers():
    dispLayers = mc.ls(type = 'displayLayer')
    for layer in dispLayers:
        try:
            mc.delete(layer)
        except:
            pass

def deleteUnconnectedShapes():
    targets = mc.ls(type = 'transform' )
    for target in targets:
        #get all the transforms in hierarchy
        children = mc.ls(target, mc.listRelatives(target, ad=1, type='transform'))
        for child in children:
            #get the shapes of child
            shapes = mc.listRelatives(child, s=1)
            #do not delete if there is only one shape node
            if len(shapes) > 1 :
                for shape in shapes:
                    #if nothing is connected to the shape node, delete it
                    connections = mc.listConnections(shape)
                    if not connections:
                        mc.delete(shape)

def deleteUnknownNodes():
    #delete all unknown nodes
    allNodes = mc.ls()
    unknownNodeList = []

    for node in allNodes:
        if mc.nodeType(node) == 'unknown':
            unknownNodeList.append(node)

    if len(unknownNodeList) == 0:
        print ('No unknown nodes found')
    else:
        for i in unknownNodeList:
            print ('{0}.....Deleted'.format(i))
            mc.delete(i)

def detachComponents():
    selection = mc.ls(sl=True, fl=True, l=True)
    base_name = selection[0].rsplit(".", 1)[0]
    short_base_name = base_name.rsplit("|", 1)[1]

    #delete history
    mc.select(base_name, r=True)
    mc.delete(ch=True)
    mc.select(selection, r=True)

    try:
        mm.eval('source "detachSeparate"; detachSeparate()')
        mc.selectMode(object=True)
    except:
        print ("Object of a same name detected. Will do a workaround..")
        mc.rename(base_name, short_base_name + "_1")
        mm.eval('source "detachSeparate"; detachSeparate()')
        mc.rename(base_name + "_1", short_base_name)
        mc.selectMode(object=True)

def freezeTransforms():
    import maya.mel as mm
    mm.eval('FreezeTransformations;')

def moveBA():
    import maya.cmds as mc

    sel = mc.ls(sl=1)

    mc.parentConstraint(sel[0], sel[1])
    constraint = mc.listRelatives(sel[1])
    mc.delete(constraint[-1])

def selectSame():
    selection = mc.ls(sl=True, fl=True, l=True)[0]
    initial_polycount = mc.polyEvaluate(selection, f=True)

    all_mesh = mc.pickWalk(mc.ls(type='mesh'))

    objects_same_polycount = []
    for mesh in all_mesh:
        if mc.polyEvaluate(mesh, f=True) == initial_polycount:
            objects_same_polycount.append(mesh)

    mc.select(selection, r=True)
    if objects_same_polycount:
        mc.select(objects_same_polycount, add=True)
    else:
        mm.eval('print "No other objects with same polycount found."')

def separateObjects(nodes=None):
    '''
    separates two objects while keeping the old name and hierarchy
    '''

    sel = nodes or mc.ls(sl=True, l=True)
    selShort = mc.ls(sel)
    parent = mc.listRelatives(sel, f=True, parent=True)

    if not len(sel) == 1:
        print ("Select One Object")
        return

    objects = mc.polySeparate(constructionHistory=False, caching=False)

    if parent:
        mc.parent(objects, parent)
    else:
        mc.parent(objects, w=True)

    if mc.objExists(sel[0]):
        mc.delete(sel[0])

    newObjects = mc.ls(sl=True, l=True)

    for obj in newObjects:
        mc.rename(obj, selShort[0])

def unlockAllNodes():
    allNodes = mc.ls()
    for node in allNodes:
        mc.lockNode(node, l=False)

def setCurrentUVsToMap1():
    sel = mc.ls(sl=1)

    for each in sel:
        currentUV = mc.polyUVSet(query=True, currentUVSet=True)
        indices = mc.polyUVSet(query=True, allUVSetsIndices=True)

    for i in indices[:]:
        index = i
        name = mc.getAttr(sel[0]+".uvSet["+str(i)+"].uvSetName")

        if (name == 'map1' and index != 0):
            mc.polyUVSet(rename=True, newUVSet='map1_old', uvSet=name)

    for i in indices[:]:
        index = i
        name = mc.getAttr(sel[0]+".uvSet["+str(i)+"].uvSetName")

        if (index == 0 and name != 'map1'):
            mc.polyUVSet(rename=True, newUVSet='map1', uvSet=name)

    for i in indices[:]:
        index = i
        name = mc.getAttr(sel[0]+".uvSet["+str(i)+"].uvSetName")
        currentUV = mc.polyUVSet(query=True, currentUVSet=True)

        if (currentUV[0] == name and index != 0):
            print ('Current UVs not set to first slot, copying.......')
            mc.polyUVSet(copy=True, nuv='map1', uvSet=currentUV[0])

    allUVs = mc.polyUVSet(query=True, allUVSets=True)
    print (allUVs)
    for set in allUVs:
        if set == 'map1':
            pass
        else:
            mc.polyUVSet(delete=True, uvSet=set)