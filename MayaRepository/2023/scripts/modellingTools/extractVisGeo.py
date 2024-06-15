import maya.cmds as mc

def createGroupAtPivot(name, selOrient):
    sel = mc.ls(sl=1)

    for obj in sel:
        newGroup = mc.group(n=name, em=1, w=1)
        newCon = mc.parentConstraint(selOrient[0], newGroup, mo=0)
        mc.delete(newCon)

    return newGroup

def extractVisGeo():
    selOrient = mc.ls(sl=1)
    selMeshes = mc.ls(sl=1, type='geometryShape', dag=1, ni=1)

    pupMeshes = []
    for shape in selMeshes:
        nodeType = mc.nodeType(shape)
        if nodeType == 'mesh':
            pupMeshes.append(shape)
        else:
            pass

    newGroup = createGroupAtPivot('{0}_visgeo'.format(selOrient), selOrient)

    for shape in pupMeshes:
        dupeShape = mc.duplicate(shape, n='{0}'.format(shape))
        attrs = mc.listAttr(dupeShape)
        for attr in attrs:
            try:
                if mc.getAttr("{0}.{1}".format(dupeShape[0], attr), lock=True) == True:
                    mc.setAttr("{0}.{1}".format(
                        dupeShape[0], attr), lock=False)
            except ValueError:
                pass
        mc.parent(dupeShape, newGroup)

def extractSelected():
    sel = mc.ls(sl=1)
    for i in sel:
        mc.select(i)
        extractVisGeo()

