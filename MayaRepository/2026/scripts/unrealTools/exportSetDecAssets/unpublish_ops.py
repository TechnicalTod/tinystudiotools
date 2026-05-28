import pymel.core as pm


def unpublish_set_dec_object(set_dec_object):
    try:
        if not set_dec_object.published.get():
            return

        published_set_dec_object_shape_node = set_dec_object.getShape()
        published_set_dec_shading_groups = published_set_dec_object_shape_node.shadingGroups()
        published_set_dec_object_shaders = pm.ls(
            pm.listConnections(published_set_dec_shading_groups), materials=True
        )
        for shader in published_set_dec_object_shaders:
            imported_shader_object = pm.PyNode(shader)
            imported_shading_groups = imported_shader_object.shadingGroups()
            published_shader_name = imported_shader_object.shaderName.get()
            try:
                published_shader_object = pm.PyNode(published_shader_name)
                published_shading_groups = published_shader_object.shadingGroups()
                if pm.objExists(published_shader_object):
                    print(
                        "Found Original Shader name in scene re-applying this to imported asset"
                    )
                    face_assignments = pm.sets(imported_shading_groups[0], q=True)
                    print(face_assignments)
                    pm.sets(
                        published_shading_groups[0], e=True, forceElement=face_assignments
                    )
            except Exception:
                print(
                    "Could not find original shader renaming current shader to original published name"
                )
                imported_shader_object.rename(published_shader_name)

        set_dec_object.useOutlinerColor.set(False)
        custom_shape_attrs = [
            "assetName",
            "fbxExportPath",
            "usdExportPath",
            "mayaExportPath",
            "textureDir",
            "version",
            "published",
            "variantName",
            "basePath",
            "publishedShaderList",
        ]
        for attr in custom_shape_attrs:
            if set_dec_object.hasAttr(attr):
                pm.deleteAttr(set_dec_object.attr(attr))
    except Exception:
        pass
