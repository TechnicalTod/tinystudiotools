import maya.cmds as mc

def applyTransformToMayaNode(mayaNode, decomposedMatrix, attributes=None):
    """
    Applies a transform matrix from an atlas node to a maya node, ignores scale.

    Args:
        mayaNode (string): the maya node
        decomposedMatrix (dict): dictionary with the matrix info
    """

    targetPosition = mc.xform(mayaNode, worldSpace=True, rotatePivot=True, query=True)
    targetRotation = mc.xform(mayaNode, worldSpace=True, rotation=True, query=True)
    targetScale = mc.xform(mayaNode, worldSpace=True, scale=True, query=True)

    targetTransformData = dict(translate=targetPosition, rotate=targetRotation, scale=targetScale)

    if not attributes:
        attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']

    #attributes = mo.wm.utils.attribute.convertToShortName(attributes=attributes)

    for attribute in ['translate', 'rotate', 'scale']:
        decomposedMatrix[attribute] = list(decomposedMatrix[attribute])
        for index, axis in enumerate(['X', 'Y', 'Z']):
            if attribute+axis in attributes or attribute[0]+axis.lower() in attributes:
                continue

            decomposedMatrix[attribute][index] = targetTransformData[attribute][index]

    # move and rotate source to temp group position/rotation
    if any('t' in attr for attr in attributes):
        mc.move(decomposedMatrix['translate'][0], decomposedMatrix['translate'][1], decomposedMatrix['translate'][2],
                mayaNode, rotatePivotRelative=True)
    if any('r' in attr for attr in attributes):
        mc.rotate(decomposedMatrix['rotate'][0], decomposedMatrix['rotate'][1], decomposedMatrix['rotate'][2],
                  mayaNode, worldSpace=True, absolute=True)
    if any('s' in attr for attr in attributes):
        mc.xform(mayaNode, worldSpace=True, scale=decomposedMatrix['scale'])

def moveToOrigin():
    transformData = {
        'rotate': [0.0, 0.0, 0.0],
        'scale': [1.0, 1.0, 1.0],
        'translate': [0.0, 0.0, 0.0]}
    sel = mc.ls(sl=1, type='transform')

    if sel:
        for geo in sel:
            applyTransformToMayaNode(geo, transformData)