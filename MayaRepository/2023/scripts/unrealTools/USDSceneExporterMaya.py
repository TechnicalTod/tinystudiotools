import os
import pymel.core as pm
import pxr.UsdGeom as UsdGeom
import pxr.Usd as Usd
import pxr.Gf as Gf

import warnings

#from conversionUtilites import *
# this function is in the conv utils but cbf adding the import functions while testing
def complete_path(file_path, variant, version, asset_name, ext):
    path_ext = None
    if ext == 'maya':
        path_ext = '.ma'
    elif ext == 'usd':
        path_ext = '.usda'
    else:
        path_ext = '.' + ext
    file_path = file_path.replace("\\", "/")
    final_path = file_path + asset_name + '/' + variant + '/' + version + '/'  + ext + '/' + asset_name + '_' + version + path_ext
    return final_path.strip()

def get_env_actor_info():
    root_name = "ENV"

    # Find the root object
    if pm.objExists(root_name):
        root_null = pm.PyNode(root_name)
    else:
        warnings.warn(f"Actor named 'ENV' not found.")
        return

    # Get all descendants of the null object
    all_descendants = pm.listRelatives(root_null, allDescendents=True, type='transform')

    # Include ENV root
    all_objects = [root_null] + all_descendants

    badShapeList = []
    assets_data = []
    # Print the result or use it as needed
    for obj in all_objects:
        if obj.getShape() and obj.getShape().nodeType() == 'mesh':
            if obj.hasAttr('published'):
                if obj.published.get() == True:
                    #print (f"{obj} is published")
                    # This is where we get the asset data for the shape
                    asset_data = {
                        'asset_name': obj.assetName.get(),
                        'path': obj.basePath.get(),
                        'version': obj.version.get(),
                        'variant': obj.variantName.get(),
                        'hierarchy_path': obj.longName().replace('|', '/'),
                        'transform_mat': obj.getMatrix(worldSpace=False),
                    }
                    assets_data.append(asset_data)
                else:
                    badShapeList.append(obj.name())
                    #print (f"{obj} is NOT published")
            else:
                    badShapeList.append(obj.name())
                    #print (f"{obj} is NOT published / is NOT Kosher")
        else:
            #print (f"{obj} is a null GRP")
            # This is where we get the asset data for the null
            asset_data = {
                'asset_name': obj.name(),
                'path': None,
                'hierarchy_path': obj.longName().replace('|', '/'),
                'transform_mat': obj.getMatrix(worldSpace=False),
            }
            assets_data.append(asset_data)

    return assets_data

def ExportScene(file_path):
    if not file_path.lower().endswith(('.usd', '.usda')):
        #warnings.warn(f"The path {file_path} is not a valid usd or usda path. Please add a valid path")
        #return
        file_path = file_path + '.usda'

    usd_data = get_env_actor_info()
    if not usd_data:
        return

     # Open or create the USD file for editing, overwriting if it exists
    if os.path.exists(file_path):
        warnings.warn(f"The usd path at {file_path} already exists. Please remove it or change the path")
        return
    else:
        stage = Usd.Stage.CreateNew(file_path)

    for asset in usd_data:
        hierarchy_path = asset['hierarchy_path'].split('/')
        parent_path = '/'
        for node_name in hierarchy_path:
            if node_name:  # Skip if node_name is empty
                current_path = parent_path + node_name
                if not stage.GetPrimAtPath(current_path):
                    prim = stage.DefinePrim(current_path, 'Xform')
                parent_path = current_path + '/'

        # Moved outside the inner loop to prevent repeated referencing
        prim = stage.GetPrimAtPath(parent_path[:-1])  # Adjust path for trailing '/'

        if asset.get('path') and asset['path'].strip():

            prim.GetReferences().AddReference(complete_path(asset['path'], asset['variant'], asset['version'], asset['asset_name'], 'usd'))

            # Use 'SetInfo' to attach the structured metadata to the prim - This is readable in both unreal and houdini
            prim.SetAssetInfoByKey('name', asset['asset_name'])
            prim.SetAssetInfoByKey('path', asset['path'])
            prim.SetAssetInfoByKey('version', asset['version'])
            prim.SetAssetInfoByKey('variant', asset['variant'])
        
        xform = UsdGeom.Xformable(prim)
        # Check if a transform operation already exists
        xformOps = xform.GetOrderedXformOps()
        transformOpExists = any(op.GetOpType() == UsdGeom.XformOp.TypeTransform for op in xformOps)

        if not transformOpExists:
            xformOp = xform.AddTransformOp()
        else:
            # If a transform operation exists, find it
            xformOp = next((op for op in xformOps if op.GetOpType() == UsdGeom.XformOp.TypeTransform), None)

        if xformOp:
            mat = asset['transform_mat']
            scale_factor = 1  # Define your scaling factor
            # Apply scaling to the translation components
            mat[3, :3] *= scale_factor
            transform_matrix = Gf.Matrix4d(mat)
            xformOp.Set(transform_matrix)

    stage.GetRootLayer().Save()

    print ("Exporting . . . . ")
    print (file_path)
