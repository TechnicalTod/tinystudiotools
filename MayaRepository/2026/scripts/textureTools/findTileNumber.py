import maya.cmds as mc
import maya.mel as mm

sel = mc.ls(sl=1, o=1)
shape = mc.listRelatives(sel)
try:
     mc.addAttr(shape[0], ln='rmanF__mapUDim', dv=10, at='short')
except:
     print ('shape already has attribute'    )

mm.eval('textureWindowSelectConvert 4')
tileNumber = mm.eval('findTileNumber()')
