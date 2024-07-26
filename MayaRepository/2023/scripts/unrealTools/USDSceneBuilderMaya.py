import os
import pxr.Usd, pxr.UsdGeom
import pymel.core as pm

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

# Process USD, extract relevant data
def parse_usd(usd_file_path):
    stage = pxr.Usd.Stage.Open(usd_file_path)
    assets_data = []

    # Traverse Stage
    for prim in stage.Traverse():
        if prim.IsA(pxr.UsdGeom.Xform):
            xform = pxr.UsdGeom.Xformable(prim)
            local_transformation = xform.GetLocalTransformation()

            path = None
            # Asset name and metadata handling - This might be ommitted at some point depending
            asset_name = 'GRP-' + prim.GetPath().name
            if prim.HasMetadata("assetInfo"):
                asset_info = prim.GetMetadata("assetInfo")
                asset_name = asset_info["name"]
                basepath = asset_info["path"]
                version = asset_info["version"]
                variant = asset_info["variant"]
                path = complete_path(basepath, variant, version, asset_name, 'maya')
            else:
                path = 'ActorGroup'

            asset_data = {
                'usd_hierarchy': prim.GetPath().pathString,
                'ma_path': path,
                'transform_mat': local_transformation,
                'asset_name': asset_name,
            }
            assets_data.append(asset_data)

    return assets_data

# Function to flatten the transformation matrix from a tuple of tuples to a single tuple
def flatten_transform_matrix(matrix):
    return tuple(element for row in matrix for element in row)

def find_or_create_transform(path):
    # Early return if the path is empty or None
    if not path:
        print("Received an empty path, skipping creation.")
        return None

    parts = path.strip("/").split("/")
    current_node = None

    for part in parts:
        if current_node:
            # Working below the root level
            full_path = current_node + '|' + part
        else:
            # At the root level, paths should start with '|'
            full_path = '|' + part

        if pm.objExists(full_path):
            current_node = pm.PyNode(full_path)
        else:
            if current_node:
                current_node = pm.group(em=True, name=part, parent=current_node)
            else:
                current_node = pm.group(em=True, name=part)

    return current_node

# Main function to load assets and create hierarchy
def load_assets_and_create_hierarchy(data):
    for item in data:
        name = item["asset_name"]
        transform_mat = item["transform_mat"]
        usd_hierarchy = item["usd_hierarchy"]
        ma_path = item['ma_path']

        # Flatten the transformation matrix
        flat_transform_mat = flatten_transform_matrix(transform_mat)

        # Create or find the node based on USD path
        node_path = usd_hierarchy.rsplit('/', 1)[0] if '/' in usd_hierarchy else ""
        parent_node = find_or_create_transform(node_path)

        if ma_path != "ActorGroup":
            if os.path.exists(ma_path):
                # Load the asset
                loaded_nodes = pm.importFile(ma_path, returnNewNodes=True)
                asset_node = [node for node in loaded_nodes if pm.nodeType(node) == 'transform'][0]
                asset_node.rename(name)
                # Reparent the loaded asset under the correct parent and apply transformation as it is in realative space
                pm.parent(asset_node, parent_node)
                pm.xform(asset_node, matrix=flat_transform_mat, relative=False)
            else:
                print(f"File not found: {ma_path}")
        else:
            # If it's an ActorGroup, create or get the group node and set its transformation
            group_node = find_or_create_transform(usd_hierarchy)
            pm.xform(group_node, matrix=flat_transform_mat, relative=False)

def BuildScene(file_path):
    if not file_path.lower().endswith(('.usd', '.usda')):
        warnings.warn(f"The path {file_path} is not a valid usd or usda path. Please add a valid path")
        return
    
    if not os.path.exists(file_path):
        warnings.warn(f"The path {file_path} does not exist. Please enter an existing .usd or .usda")
        return

    ma_data = parse_usd(file_path)
    # Call the main function with the data
    load_assets_and_create_hierarchy(ma_data)

    print ("Importing . . . . ")
    print (file_path)
