import maya.cmds as mc
import maya.mel as mm

def fastRetopoMultiple():
    sel = mc.ls(sl=1)

    for each in sel:
        mc.select(clear=True)
        mc.select(each)
        mc.polyRemesh()
        mc.DeleteAllHistory()
        mc.select(clear=True)
        mc.select(each)
        mc.polyRetopo()

        history = mc.listHistory(each)
        for item in history:
            if 'polyRetopo' in item:
                mc.setAttr('{0}.targetFaceCount'.format(item), 1000)
