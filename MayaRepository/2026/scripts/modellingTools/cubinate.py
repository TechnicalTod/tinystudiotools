def cubinate(objects=None, doTransfer=True, deleteSourceMesh=False, keepHistory=True, smoothCube=0, preScale=0, subdivisionsX=3, subdivisionsY=3, subdivisionsZ=3):
    import maya.cmds as mc

    cubes = []

    objects = objects or mc.ls(sl=True, l=True)

    if not objects:
        raise RuntimeError('No Objects')

    for obj in objects:

        # record the pivot of the object for later
        oldPiv = mc.xform(obj, q=True, ws=True, piv=True)[:3]

        # center the pivot and record the position
        mc.xform(obj, cp=True)
        piv = mc.xform(obj, q=True, ws=True, piv=True)[:3]

        # add a cube at the centered location
        cube = mc.polyCube(n=obj + '_cube', subdivisionsX=subdivisionsX, subdivisionsY=subdivisionsY, subdivisionsZ=subdivisionsZ);
        mc.xform(cube,t = piv)

        # get the name of the transform created and add it to the return list
        cubeTransform = mc.ls(cube, transforms=True)[0]
        cubes.append(cubeTransform)

        # return the objects pivot
        mc.xform(obj, piv=oldPiv, ws=True)

        # record the bounding box of the object
        bounds = mc.xform(obj, bb=True, q=True, ws=True)

        # apply the bounding box to the cube
        sx = abs(bounds[0] - bounds[3])
        sy = abs(bounds[1] - bounds[4])
        sz = abs(bounds[2] - bounds[5])
        mc.setAttr(cubeTransform + ".scaleX", sx + preScale)
        mc.setAttr(cubeTransform + ".scaleY", sy + preScale)
        mc.setAttr(cubeTransform + ".scaleZ", sz + preScale)

        # add a smooth node to the mesh, good for spherical objects, True or False
        if smoothCube:
            mc.polySmooth(cube, dv=smoothCube, kb=False, ksb=False, ch=True)

        # transfer the vertex positions of the cube to the object below, True or False
        if doTransfer:
            mc.transferAttributes(obj, cubeTransform, uvs=0, pos=1, nml=0, spa=0)

        # keep construction history, True or False
        if not keepHistory:
            mc.delete(cube, ch=True)

        # remove the source mesh, True or False
        if deleteSourceMesh:
            if keepHistory and doTransfer:
                print ('WARNING: cannot keep history when deleting source mesh and transfering attributes')
                mc.delete(cube, ch=True)
            mc.delete(obj)

    # select and return the new cube meshes
    mc.select(cubes)
    return cubes
