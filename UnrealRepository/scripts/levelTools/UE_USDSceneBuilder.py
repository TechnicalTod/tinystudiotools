import os
import pxr.Usd, pxr.UsdGeom
import numpy as np
import unreal
import warnings

from genTools.conversionUtilites import *

# Reference USD Asset - This will be replaced when turned into a UI
#usd_file_path = "D:/CFXDemoProject/MayaNewAttrPub_v01.usda"
#usd_file_path = "D:/CFXDemoProject/TableAndChairDemo_dres_v002.usda"

# Process USD, extract relevant data
def parse_usd(usd_file_path):
    stage = pxr.Usd.Stage.Open(usd_file_path)
    assets_data = []

    # Traverse Stage
    for prim in stage.Traverse():
        if prim.IsA(pxr.UsdGeom.Xform):
            xform = pxr.UsdGeom.Xformable(prim)
            local_transformation = xform.GetLocalTransformation()

            t, r, s = decompose_matrix(np.transpose(np.array(local_transformation)))
            translation, rotation, scale = from_to_rotation_conversion(t, r, s, 1) # This magic number is for scale

            asset_name = None
            path = None
            version = None
            variant = None
            if prim.HasMetadata("assetInfo"):
                asset_info = prim.GetMetadata("assetInfo")
                asset_name = asset_info["name"]
                path = asset_info["path"]
                version = asset_info["version"]
                variant = asset_info["variant"]

            asset_data = {
                    'usd_hierarchy': prim.GetPath().pathString,
                    'translation': translation,
                    'rotation': rotation,
                    'scale': scale,
                    # Meta Data Handling - For empty actors these are None
                    'asset_name': asset_name,
                    'path': path,
                    'version': version,
                    'variant': variant,
                }
            assets_data.append(asset_data)
    return assets_data

# Create / Get Unreal Hierarchy for placing assets in scene - Sets Parenting
def get_or_create_actor_hierarchy(usd_hierarchy, actor_class=unreal.Actor, asset=None):
    parts = usd_hierarchy.strip('/').split('/')
    parent_actor = None
    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    for i, part in enumerate(parts):
        actor_name = part
        # Look for an existing actor with the given name that also has the correct parent
        existing_actor = None
        potential_actors = [actor for actor in editor_actor_subsystem.get_all_level_actors() if actor.get_actor_label() == actor_name]
        for actor in potential_actors:
            if actor.get_attach_parent_actor() == parent_actor:  # Correct position in the hierarchy
                existing_actor = actor
                break

        if not existing_actor:
            # Spawn actor
            if i < len(parts) - 1 or not asset:  # Intermediate node or no specific asset
                existing_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
            else:
                existing_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
                if existing_actor and existing_actor.root_component:
                    existing_actor.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            existing_actor.set_actor_label(actor_name)  # Set label for readability

        if parent_actor and existing_actor:
            # Only attach if not already attached, to avoid unnecessary operations
            if existing_actor.get_attach_parent_actor() != parent_actor:
                existing_actor.attach_to_actor(parent_actor, unreal.Name(""), unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)

        parent_actor = existing_actor  # Update parent_actor for the next iteration

    return parent_actor

# Apply the converter transforms to the place unreal actors
def apply_transform(actor, translation, rotation, scale):
    # Translation
    translation = unreal.Vector(translation[0], translation[1], translation[2])
    actor.set_actor_relative_location(translation, sweep=False, teleport=True)
   
    # Scale
    # Directly using the list for scale. Unreal's Vector can handle both lists and tuples.
    ue_scale = unreal.Vector(*scale)
    actor.set_actor_relative_scale3d(ue_scale)
    
    # Unreal Engine uses the convention Pitch (X), Yaw (Y), Roll (Z) for rotations
    ue_rotation = unreal.Rotator(-rotation[0], -rotation[1], rotation[2])
    actor.set_actor_relative_rotation(ue_rotation, False, True)

# Build Level using Uassets
def BuildScene(file_path):
    if not file_path.lower().endswith(('.usd', '.usda')):
        warnings.warn(f"The path {file_path} is not a valid usd or usda path. Please add a valid path")
        return

    if not os.path.exists(file_path):
        warnings.warn(f"The path {file_path} does not exist. Please enter an existing .usd or .usda")
        return

    assets_data = parse_usd(file_path)  

    #Place Actors in Unreal Scene
    for item in assets_data:
        if item['path']:
            ue_path = complete_path(item['path'], item['variant'], item['version'], item['asset_name'], 'ue')
        else:
            ue_path = 'ActorGroup'
        
        usd_hierarchy = item['usd_hierarchy']
        translation = item['translation']
        rotation = item['rotation']
        scale = item['scale']

        if ue_path != "ActorGroup":
            asset = unreal.load_asset(ue_path)
            if asset:
                # Spawn or find the actor based on the asset and USD path
                actor = get_or_create_actor_hierarchy(usd_hierarchy, asset=asset)
            else:
                unreal.log_warning(f"Asset not found for path: {ue_path}") 
                #Add some stuff here to run the asset loader script and load the missing asset
        else:
            # For 'ActorGroup', no asset is involved
            actor = get_or_create_actor_hierarchy(usd_hierarchy)
        
        apply_transform(actor, translation, rotation, scale)

    # Access the Editor Actor Utilities Subsystem
    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Get all actors in the current level
    all_actors = editor_actor_subsystem.get_all_level_actors()

    # Filter for Static Mesh Components
    static_mesh_components = [actor for actor in all_actors if isinstance(actor, unreal.StaticMeshActor)]

    # Find All static mesh actors and convert them from MOVABLE to STATIC
    for sm_actor in static_mesh_components:
        # Access the StaticMeshComponent of each StaticMeshActor
        sm_component = sm_actor.get_component_by_class(unreal.StaticMeshComponent)
        if sm_component and sm_component.mobility != unreal.ComponentMobility.STATIC:
            # Set the component's mobility to STATIC
            sm_component.set_editor_property('mobility', unreal.ComponentMobility.STATIC)

    print ("Importing . . . . ")
    print (file_path)