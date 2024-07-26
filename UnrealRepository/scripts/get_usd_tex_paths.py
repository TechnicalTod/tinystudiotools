from pxr import Usd, UsdShade

def get_connected_texture_file(shader_input):
    if shader_input.HasConnectedSource():
        source, sourceName, _ = shader_input.GetConnectedSource()
        if source:
            shader = UsdShade.Shader(source)
            # Check if the source shader is a UsdUVTexture type.
            if shader and shader.GetIdAttr().Get() == "UsdUVTexture":
                file_input = shader.GetInput("file")
                if file_input and file_input.Get():
                    return file_input.Get().path
            else:
                # Recursively check connected sources for other shader inputs.
                for input in shader.GetInputs():
                    result = get_connected_texture_file(shader.GetInput(input.GetBaseName()))
                    if result:
                        return result
    return None

def get_texture_paths_from_shader(shader):
    texture_paths = {}
    for input in shader.GetInputs():
        texture_path = get_connected_texture_file(input)
        if texture_path:
            # Convert TfToken to string for dictionary key, using GetName().
            input_name_str = input.GetBaseName()
            texture_paths[input_name_str] = texture_path
    return texture_paths

def get_material_texture_paths(material):
    all_texture_paths = {}
    # Check the surface shader connected to the material
    surface_output = material.GetSurfaceOutput()
    if surface_output.HasConnectedSource():
        surface_source, _, _ = surface_output.GetConnectedSource()
        surface_shader = UsdShade.Shader(surface_source)
        # Extract textures from the connected shader
        all_texture_paths.update(get_texture_paths_from_shader(surface_shader))
    return all_texture_paths

def find_materials_with_textures(stage):
    all_materials_textures = {}
    for prim in stage.TraverseAll():
        if prim.IsA(UsdShade.Material):
            material = UsdShade.Material(prim)
            texture_paths = get_material_texture_paths(material)
            if texture_paths:  # If any texture paths were found
                # Instead of using prim.GetName(), we find the connected shader name
                surface_output = material.GetSurfaceOutput()
                if surface_output.HasConnectedSource():
                    surface_source, _, _ = surface_output.GetConnectedSource()
                    surface_shader = UsdShade.Shader(surface_source)
                    shader_name = surface_shader.GetPrim().GetName()
                    all_materials_textures[shader_name] = texture_paths
    return all_materials_textures

def get_paths(usd_file):
    stage = Usd.Stage.Open(usd_file)
    materials_with_textures = find_materials_with_textures(stage)
    return materials_with_textures