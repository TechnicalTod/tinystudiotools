import os
import unreal

def exportSelectedAssets(exportLocation):
    """
    Export selected assets.
    """
    # Get selected assets from content browser
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
    
    for selected_asset in selected_assets:
        asset_name = selected_asset.get_name()
        
        # Define the export directory and filename
        export_dir = exportLocation
        filename = os.path.join(export_dir, asset_name + '.usda')
        
        # Define the texture directory one level deeper
        texture_dir = os.path.join(export_dir, 'textures')
        
        # Ensure the texture directory exists
        os.makedirs(texture_dir, exist_ok=True)
        
        # Create asset export task
        export_task = unreal.AssetExportTask()
        export_task.automated = True
        export_task.filename = filename
        export_task.object = selected_asset
        export_task.prompt = False
        export_task.replace_identical = True  # Replace identical files
        
        # Create USD export options
        options = unreal.StaticMeshExporterUSDOptions()
        
        # Access the mesh_asset_options struct
        mesh_asset_options = options.get_editor_property('mesh_asset_options')
        mesh_asset_options.use_payload = False
        mesh_asset_options.bake_materials = True  # Enable baking materials
        mesh_asset_options.lowest_mesh_lod = 0  # Set to use only LOD0
        mesh_asset_options.highest_mesh_lod = 0  # Set to use only LOD0
        
        # Set texture baking options
        material_baking_options = mesh_asset_options.get_editor_property('material_baking_options')
        material_baking_options.set_editor_property('textures_dir', unreal.DirectoryPath(texture_dir))
        material_baking_options.set_editor_property('default_texture_size', unreal.IntPoint(1024, 1024))
        material_baking_options.set_editor_property('constant_color_as_single_value', True)

        # Update the properties list if needed
        properties = material_baking_options.get_editor_property('properties')
        for prop in properties:
            prop.set_editor_property('use_custom_size', True)
            prop.set_editor_property('custom_size', unreal.IntPoint(1024, 1024))
        material_baking_options.set_editor_property('properties', properties)
        
        mesh_asset_options.set_editor_property('material_baking_options', material_baking_options)
        
        # Set the updated mesh_asset_options back to the options
        options.set_editor_property('mesh_asset_options', mesh_asset_options)
        
        # Access and set stage options
        stage_options = options.get_editor_property('stage_options')
        stage_options.set_editor_property('meters_per_unit', 0.1)  # Set the scale to 0.1 meter per unit
        stage_options.set_editor_property('up_axis', unreal.UsdUpAxis.Y_AXIS)  # Set the up axis to Y
        options.set_editor_property('stage_options', stage_options)
        
        export_task.options = options  # Assign the USD export options to the export task
        
        # Create class specific exporter
        usd_exporter = unreal.StaticMeshExporterUsd()  # Instantiate the USD exporter
        export_task.exporter = usd_exporter
        
        # Run the export task
        success = usd_exporter.run_asset_export_task(export_task)
        
        # Logging the result
        if success:
            unreal.log("Exported {} to {}".format(export_task.object.get_name(), export_task.filename))
        else:
            unreal.log_error("Failed to export {}".format(export_task.object.get_name()))

# Call the function to export selected assets
#exportSelectedAssets('D:/Exports/')