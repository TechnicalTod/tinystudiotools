MAIN_WINDOW_OBJECT_NAME = "PublishSetDecAssetsMainWindow"
DEFAULT_VARIANT_NAME = "main"

PARAMETER_LIST = {
    "USDPreviewMaterial": {
        "diffuse": {"suffix": "Diffuse", "mayaParameter": "diffuseColor"},
        "emissive": {"suffix": "Emissive", "mayaParameter": "emissiveColor"},
        "ao": {"suffix": "AO", "mayaParameter": "occlusion"},
        "opacity": {"suffix": "Transparency", "mayaParameter": "opacity"},
        "metallic": {"suffix": "Metallic", "mayaParameter": "metallic"},
        "roughness": {"suffix": "Roughness", "mayaParameter": "roughness"},
        "normal": {"suffix": "Normal", "mayaParameter": "normal"},
        "subsurface": {
            "suffix": "Translucency",
            "mayaParameter": "clearcoat",
            "fileNodeParameter": "outAlpha",
        },
        "displacement": {
            "suffix": "Displacement",
            "mayaParameter": "displacement",
            "fileNodeParameter": "outAlpha",
        },
    }
}
