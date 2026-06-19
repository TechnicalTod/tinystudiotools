"""Import Unreal Assets — static mesh, skeletal mesh, and material import for TinyStudio."""

from __future__ import annotations

__all__ = [
    "MASTER_MATERIAL_PATH",
    "ORMA_PARAMETERS",
    "StaticMeshPublishIdentity",
    "StaticMeshTextureImportResult",
    "USD_PREVIEW_PARAMETER_LIST",
    "WarnFn",
    "assign_mesh_materials",
    "assign_setdec_static_mesh_materials",
    "build_unreal_mesh_import_path",
    "bundle_paths",
    "ensure_setdec_static_mesh_imported",
    "ensure_static_mesh_imported",
    "expected_ue_mesh_object_path",
    "expected_ue_mesh_object_path_for_identity",
    "identity_from_base_path",
    "identity_from_legacy_setdec_args",
    "import_setdec_static_mesh",
    "import_setdec_static_mesh_pipeline",
    "import_setdec_textures",
    "import_static_mesh",
    "import_static_mesh_publish_pipeline",
    "import_static_mesh_textures",
    "resolve_identity",
    "resolve_static_mesh_object_path",
    "show",
    "sm_prefixed_mesh_object_path",
    "udim_to_glob",
]


def __getattr__(name: str):
    if name in ("MASTER_MATERIAL_PATH", "ORMA_PARAMETERS", "USD_PREVIEW_PARAMETER_LIST"):
        from . import constants

        return getattr(constants, name)
    if name == "StaticMeshTextureImportResult" or name == "WarnFn":
        from . import types

        return getattr(types, name)
    if name in (
        "StaticMeshPublishIdentity",
        "build_unreal_mesh_import_path",
        "bundle_paths",
        "expected_ue_mesh_object_path",
        "expected_ue_mesh_object_path_for_identity",
        "identity_from_base_path",
        "identity_from_legacy_setdec_args",
        "resolve_identity",
        "sm_prefixed_mesh_object_path",
        "udim_to_glob",
    ):
        from . import publish

        return getattr(publish, name)
    if name in ("assign_mesh_materials", "assign_setdec_static_mesh_materials"):
        from .materials import assignment

        return getattr(assignment, name)
    if name in ("import_setdec_static_mesh", "import_static_mesh"):
        from .static_mesh import import_mesh

        return getattr(import_mesh, name)
    if name in ("import_setdec_textures", "import_static_mesh_textures"):
        from .static_mesh import import_textures

        return getattr(import_textures, name)
    if name in (
        "ensure_setdec_static_mesh_imported",
        "ensure_static_mesh_imported",
        "import_setdec_static_mesh_pipeline",
        "import_static_mesh_publish_pipeline",
        "resolve_static_mesh_object_path",
    ):
        from .static_mesh import pipelines

        return getattr(pipelines, name)
    if name == "show":
        from .ui.entry import show

        return show
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
