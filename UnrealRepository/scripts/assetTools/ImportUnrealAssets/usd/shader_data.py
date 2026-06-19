from pxr import Usd, UsdShade

# USD Preview Surface inputs that map to UE scalars/colours when no texture is connected.
SCALAR_FALLBACK_INPUTS = {
    "diffuseColor": "albedo_color",
    "emissiveColor": "emissive_color",
    "metallic": "metallic",
    "roughness": "roughness",
}

USD_PREVIEW_SURFACE_DEFAULTS = {
    "diffuseColor": (0.5, 0.5, 0.5),
    "emissiveColor": (0.0, 0.0, 0.0),
    "metallic": 0.0,
    "roughness": 0.5,
}


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
            input_name_str = input.GetBaseName()
            texture_paths[input_name_str] = texture_path
    return texture_paths


def _normalize_usd_scalar_value(value, usd_input_name: str):
    if usd_input_name in ("diffuseColor", "emissiveColor"):
        return (float(value[0]), float(value[1]), float(value[2]))
    return float(value)


def _fallback_from_uv_texture(shader_input, usd_input_name: str):
    """Read UsdUVTexture ``inputs:fallback`` when a file texture is connected but unresolved."""
    if not shader_input.HasConnectedSource():
        return None

    source, _, _ = shader_input.GetConnectedSource()
    shader = UsdShade.Shader(source)
    if not shader or shader.GetIdAttr().Get() != "UsdUVTexture":
        return None

    fallback_input = shader.GetInput("fallback")
    if fallback_input is None:
        return None

    fallback = fallback_input.Get()
    if fallback is None:
        return None

    if usd_input_name in ("diffuseColor", "emissiveColor"):
        return (float(fallback[0]), float(fallback[1]), float(fallback[2]))
    if usd_input_name in ("metallic", "roughness", "occlusion", "opacity"):
        if len(fallback) >= 4:
            return float(fallback[3])
        return float(fallback[0])
    return None


def _input_has_authored_value(shader_input) -> bool:
    attr = shader_input.GetAttr()
    if attr is None:
        return False
    return attr.IsAuthored()


def _valid_shader_input(shader_input) -> bool:
    if shader_input is None:
        return False
    attr = shader_input.GetAttr()
    return attr is not None and attr.IsValid()


def get_scalar_fallbacks_from_shader(shader, texture_paths: dict) -> dict:
    """Return scalar/colour values for inputs that have no resolved texture path."""
    scalars = {}
    for usd_input, scalar_key in SCALAR_FALLBACK_INPUTS.items():
        if usd_input in texture_paths:
            continue

        shader_input = shader.GetInput(usd_input)
        if not _valid_shader_input(shader_input):
            continue

        if shader_input.HasConnectedSource():
            fallback = _fallback_from_uv_texture(shader_input, usd_input)
            if fallback is not None:
                scalars[scalar_key] = fallback
            continue

        if _input_has_authored_value(shader_input):
            value = shader_input.Get()
            if value is not None:
                scalars[scalar_key] = _normalize_usd_scalar_value(value, usd_input)
                continue

        scalars[scalar_key] = _normalize_usd_scalar_value(
            USD_PREVIEW_SURFACE_DEFAULTS[usd_input],
            usd_input,
        )

    return scalars


def get_material_texture_paths(material):
    all_texture_paths = {}
    surface_output = material.GetSurfaceOutput()
    if surface_output.HasConnectedSource():
        surface_source, _, _ = surface_output.GetConnectedSource()
        surface_shader = UsdShade.Shader(surface_source)
        all_texture_paths.update(get_texture_paths_from_shader(surface_shader))
    return all_texture_paths


def _surface_preview_shader(material):
    surface_output = material.GetSurfaceOutput()
    if not surface_output.HasConnectedSource():
        return None
    surface_source, _, _ = surface_output.GetConnectedSource()
    surface_shader = UsdShade.Shader(surface_source)
    if surface_shader.GetIdAttr().Get() != "UsdPreviewSurface":
        return None
    return surface_shader


def find_material_shader_data(stage):
    all_material_data = {}
    for prim in stage.TraverseAll():
        if not prim.IsA(UsdShade.Material):
            continue

        material = UsdShade.Material(prim)
        surface_shader = _surface_preview_shader(material)
        if surface_shader is None:
            continue

        shader_name = surface_shader.GetPrim().GetName()
        texture_paths = get_texture_paths_from_shader(surface_shader)
        scalar_values = get_scalar_fallbacks_from_shader(surface_shader, texture_paths)
        all_material_data[shader_name] = {
            "textures": texture_paths,
            "scalars": scalar_values,
        }
    return all_material_data


def get_shader_data(usd_file):
    stage = Usd.Stage.Open(usd_file)
    return find_material_shader_data(stage)


def get_paths(usd_file):
    shader_data = get_shader_data(usd_file)
    return {shader_name: data["textures"] for shader_name, data in shader_data.items()}
