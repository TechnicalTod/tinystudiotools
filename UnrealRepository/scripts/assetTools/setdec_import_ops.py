"""Backward-compat shim — use assetTools.ImportUnrealAssets instead."""

from assetTools.ImportUnrealAssets import __all__ as _package_all
from assetTools.ImportUnrealAssets.constants import (
    MASTER_MATERIAL_PATH,
    ORMA_PARAMETERS,
    USD_PREVIEW_PARAMETER_LIST,
)
from assetTools.ImportUnrealAssets.publish import (
    StaticMeshPublishIdentity,
    build_unreal_mesh_import_path,
    bundle_paths,
    expected_ue_mesh_object_path,
    expected_ue_mesh_object_path_for_identity,
    identity_from_base_path,
    identity_from_legacy_setdec_args,
    resolve_identity,
    sm_prefixed_mesh_object_path,
    udim_to_glob,
)
from assetTools.ImportUnrealAssets.types import StaticMeshTextureImportResult, WarnFn
from assetTools.ImportUnrealAssets.materials.assignment import (
    assign_mesh_materials,
    assign_setdec_static_mesh_materials,
)
from assetTools.ImportUnrealAssets.static_mesh.import_mesh import (
    import_setdec_static_mesh,
    import_static_mesh,
    published_fbx_path,
    published_fbx_path_for_identity,
)
from assetTools.ImportUnrealAssets.static_mesh.import_textures import (
    import_setdec_textures,
    import_static_mesh_textures,
)
from assetTools.ImportUnrealAssets.static_mesh.pipelines import (
    ensure_setdec_static_mesh_imported,
    ensure_static_mesh_imported,
    import_setdec_static_mesh_pipeline,
    import_static_mesh_publish_pipeline,
    resolve_static_mesh_object_path,
)
from assetTools.ImportUnrealAssets.static_mesh.version_copy import (
    copy_lightmap_and_materials_from_previous,
    get_previous_version_static_mesh,
)

__all__ = list(_package_all) + [
    "copy_lightmap_and_materials_from_previous",
    "get_previous_version_static_mesh",
    "published_fbx_path",
    "published_fbx_path_for_identity",
]
