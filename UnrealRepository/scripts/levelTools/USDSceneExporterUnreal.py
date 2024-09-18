import os
import pxr.UsdGeom as UsdGeom
import pxr.Usd as Usd
import pxr.Gf as Gf
import numpy as np
import unreal
import warnings

from genTools.conversionUtilites import *

np.set_printoptions(precision=3)
np.set_printoptions(suppress=True)

def get_env_actor_info():
    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = editor_actor_subsystem.get_all_level_actors()

    def collect_actor_info(actor, path='', assets_data=[]):
        actor_name = actor.get_actor_label()
        full_path = f'{path}/{actor_name}' if path else actor_name

        translation = None
        rotation = None
        scale = None
        parent_actor = actor.get_attach_parent_actor()
        if parent_actor != None:
            local_actor_transform = actor.get_actor_transform().make_relative(parent_actor.get_actor_transform())
            t = local_actor_transform.translation
            r = local_actor_transform.rotation
            s = local_actor_transform.scale3d
        else:
            actor_transform = actor.get_actor_transform()
            t = actor_transform.translation
            r = actor_transform.rotation
            s = actor_transform.scale3d
            
        translation = np.array([t.x, t.y, t.z])
        rotation = euler_from_quaternion(r.x, r.y, r.z, r.w)
        scale = np.array([s.x, s.y, s.z])

        usd_translation, usd_rotation, usd_scale = from_to_rotation_conversion(translation, rotation, scale, 1)

        mesh_path = None
        importfilePath = None

        if isinstance(actor, unreal.StaticMeshActor):
            static_mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
            if static_mesh_component:
                static_mesh = static_mesh_component.static_mesh
                if static_mesh:
                    mesh_path = static_mesh.get_path_name()
        
        core_path = None
        version = None
        assetname = None
        variant = None 

        if mesh_path:
            asset_path = mesh_path.split('.')[0]
            #print('asset_path', asset_path)
            meshasset = unreal.EditorAssetLibrary.find_asset_data(asset_path).get_asset()
            assetname = unreal.EditorAssetLibrary.get_metadata_tag(meshasset, "FBX.assetName")
            core_path = unreal.EditorAssetLibrary.get_metadata_tag(meshasset, "FBX.basePath")
            version = unreal.EditorAssetLibrary.get_metadata_tag(meshasset, "FBX.version")
            variant = unreal.EditorAssetLibrary.get_metadata_tag(meshasset, "FBX.variantName")
        # Create a dictionary for the current actor's data
        asset_data = {
            'translation': usd_translation,
            'rotation': usd_rotation,
            'scale': usd_scale,
            'hierarchy_path': full_path,
            'asset_name': assetname,
            'path': core_path,
            'version': version,
            'variant': variant,
            # Any Extra data goes here
        }
        assets_data.append(asset_data)
        
        for child_actor in actor.get_attached_actors():
            collect_actor_info(child_actor, full_path, assets_data)

        return assets_data

    env_actor = next((actor for actor in all_actors if actor.get_actor_label() == 'ENV'), None)

    if env_actor:
        return collect_actor_info(env_actor)
    else:
        warnings.warn(f"Actor named 'ENV' not found.")
        return []


def ExportScene(file_path):
    if not file_path.lower().endswith(('.usd', '.usda')):
        #warnings.warn(f"The path {file_path} is not a valid usd or usda path. Please add a valid path")
        file_path = file_path + '.usda'
        #return

    env_actor_info = get_env_actor_info()
    if not env_actor_info:
        return

    # Open or create the USD file for editing, overwriting if it exists
    if os.path.exists(file_path):
        warnings.warn(f"The usd path at {file_path} already exists. Please remove it or change the path")
        return
    else:
        stage = Usd.Stage.CreateNew(file_path)

    for asset in env_actor_info:
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
        if asset['path'] != None:
            prim.GetReferences().AddReference(complete_path(asset['path'], 'base', asset['version'], asset['asset_name'], 'usd'))

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
            matrix = compose_matrix(asset['translation'], asset['rotation'], asset['scale'])
            usd_matrix = np.transpose(matrix)
            # Ensure the matrix is correctly formatted for USD
            xformOp.Set(Gf.Matrix4d(usd_matrix))

    stage.GetRootLayer().Save()
    
    print ("Exporting . . . . ")
    print (file_path)