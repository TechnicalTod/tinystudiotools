import maya.cmds as mc
import maya.mel as mm

def separateFaces():
    selection = mc.ls(sl=True, fl=True, l=True)
    base_name = selection[0].rsplit(".", 1)[0]
    short_base_name = base_name.rsplit("|", 1)[1]

    # delete history
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

def splitShapesPerUDIM():
    sel = mc.ls(sl=1, o=1)
    shape = mc.listRelatives(sel)
    try:
        mc.addAttr(shape[0], ln='rmanF__mapUDim', dv=10, at='short')
    except:
        print ('shape already has attribute')

    mm.eval('textureWindowSelectConvert 4;')
    tileNumber = mm.eval('findTileNumber();')

    for udim in tileNumber:
        print ('Splitting shape for udim #' + udim)
        mc.select(sel)

        maxV, multiplier, V, U = udim

        multiplier = multiplier + '0'

        if int(V) == 0:
            maxV = 1+int(multiplier)
            minV = 0+int(multiplier)
        else:
            maxV = int(V)+int(multiplier)+1
            minV = int(V)+int(multiplier)

        if int(U) == 0:
            maxU = 10
            minU = 9
            maxV = int(V)+int(multiplier)
            minV = int(V)+int(multiplier)-1
        else:
            maxU = int(U)
            minU = int(U)-int(1)

        tmpBuffer = []

        print (maxV, minV)

        if sel:
            for i in sel:
                uvNum = mc.polyEvaluate(i, uv=1)
                # Find how many UVs in the object
                if uvNum:
                    # and if there is UV on the object
                    for u in range(uvNum):
                        # For each UV
                        # Find their position in UV Layout
                        uvPos = mc.polyEditUV("%s.map[%d]" % (i, u), q=1)
                        # and if it is sitting in the UV range given above
                        #print minU,minV,maxU,maxV
                        if uvPos[0] > minU and uvPos[0] < maxU and uvPos[1] > minV and uvPos[1] < maxV:
                            # Store their name in the variable we set earlier
                            tmpBuffer.append("%s.map[%d]" % (i, u))

            mc.select(tmpBuffer)
            mc.ConvertSelectionToContainedFaces()

            separateFaces()
            mc.rename(sel[0]+"_"+str(udim))

        else:
            mc.warning("Nothing Selected....")
