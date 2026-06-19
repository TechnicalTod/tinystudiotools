"""Import published Set Dec custom animated geometry into the shot level sequence."""

from __future__ import annotations

from typing import Callable, List, Optional

import unreal

import assetTools.setdec_import_ops as setdec_import_ops

from . import alembic_ops, animated_fbx_ops, paths
from .constants import SEQUENCER_FOLDER_CUSTOM
from .manifest import (
    EXPORT_FORMAT_ALEMBIC,
    EXPORT_FORMAT_FBX,
    CustomAnimatedGeometryItem,
)
from .setup_ops import ShotSetupResult

WarnFn = Callable[[str], None]


def _warn_default(message: str) -> None:
    print(message)


def _ensure_publish_bundle_paths():
    try:
        from publish_bundle_paths import identity_from_base_path  # type: ignore
        return identity_from_base_path
    except ImportError:
        from genTools.studio_python_path import ensure_gen_tools_shared

        ensure_gen_tools_shared()
        from publish_bundle_paths import identity_from_base_path  # type: ignore
        return identity_from_base_path


identity_from_base_path = _ensure_publish_bundle_paths()


def _build_identity(item: CustomAnimatedGeometryItem):
    return identity_from_base_path(
        item.base_path,
        item.asset_name,
        item.variant,
        item.asset_version,
    )


def _import_setdec_textures(
    item: CustomAnimatedGeometryItem,
    unreal_import_path: str,
    *,
    warn: WarnFn,
) -> setdec_import_ops.StaticMeshTextureImportResult:
    identity = _build_identity(item)
    return setdec_import_ops.import_static_mesh_textures(
        identity,
        unreal_import_path,
        warn=warn,
    )


def _assign_setdec_materials_to_static_mesh(
    static_mesh_path: str,
    unreal_import_path: str,
    imported_textures: Optional[List[str]],
    *,
    orma_channels_by_slot: Optional[dict] = None,
    scalar_values_by_slot: Optional[dict] = None,
) -> None:
    setdec_import_ops.assign_setdec_static_mesh_materials(
        [static_mesh_path],
        unreal_import_path,
        imported_textures,
        orma_channels_by_slot=orma_channels_by_slot,
        scalar_values_by_slot=scalar_values_by_slot,
    )
    unreal.EditorAssetLibrary.save_asset(static_mesh_path.split(".")[0])


def _assign_setdec_materials_to_geometry_cache(
    cache_actor,
    imported_textures: Optional[List[str]],
    unreal_mat_import_path: str,
    *,
    warn: WarnFn,
) -> None:
    if not imported_textures:
        warn("No Set Dec textures imported for geometry cache material assignment.")
        return

    unreal_eal = unreal.EditorAssetLibrary()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    loaded_master_material = unreal_eal.load_asset(
        setdec_import_ops.MASTER_MATERIAL_PATH
    )
    if loaded_master_material is None:
        warn("Could not load master material for Set Dec geometry cache assignment.")
        return

    unreal.EditorAssetLibrary.make_directory(unreal_mat_import_path)
    material_instance = asset_tools.create_asset(
        "MI_setdec_cache",
        unreal_mat_import_path,
        unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew(),
    )
    material_instance.set_editor_property("parent", loaded_master_material)

    for texture_path in imported_textures:
        texture_path = texture_path.split(".")[0]
        loaded_texture = unreal_eal.load_asset(texture_path)
        if loaded_texture is None:
            continue
        parameter_name = loaded_texture.get_name().split("_")[-1]
        if parameter_name in ("AO", "Metallic", "Roughness"):
            loaded_texture.set_editor_property("srgb", 0)
        switch_name = "use{}Texture".format(parameter_name)
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            material_instance,
            switch_name,
            True,
        )
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            material_instance,
            parameter_name,
            loaded_texture,
        )

    cache_component = cache_actor.geometry_cache_component
    if cache_component.get_num_materials() > 0:
        cache_component.set_material(0, material_instance)
    else:
        geometry_cache = cache_component.get_editor_property("geometry_cache")
        if geometry_cache is not None:
            geometry_cache.set_editor_property("materials", [material_instance])

    unreal.EditorAssetLibrary.save_asset(material_instance.get_path_name().split(".")[0])


def import_setdec_fbx_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
    *,
    warn: WarnFn = _warn_default,
) -> list[str]:
    if not items:
        return []

    saved_assets: list[str] = []
    loaded_level_sequence = unreal.load_asset(setup.sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
    custom_folder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(
        loaded_level_sequence, SEQUENCER_FOLDER_CUSTOM
    )
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    for item in items:
        import_dir = paths.custom_geo_import_dir(setup.shot_dir, item)
        unreal.EditorAssetLibrary.make_directory(import_dir)
        static_mesh_path = animated_fbx_ops.import_static_mesh_fbx(
            item.export_path,
            import_dir,
        )
        saved_assets.append(static_mesh_path.split(".")[0])

        texture_result = _import_setdec_textures(item, import_dir, warn=warn)
        _assign_setdec_materials_to_static_mesh(
            static_mesh_path,
            import_dir,
            texture_result.imported_textures,
            orma_channels_by_slot=texture_result.orma_channels_by_slot,
            scalar_values_by_slot=texture_result.scalar_values_by_slot,
        )
        animated_fbx_ops._spawn_static_mesh_item(  # noqa: SLF001
            setup,
            item,
            static_mesh_path,
            loaded_level_sequence,
            custom_folder,
            world,
        )
        print("Set Dec FBX imported into sequencer: {}".format(item.name))

    return saved_assets


def import_setdec_alembic_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
    *,
    warn: WarnFn = _warn_default,
) -> list[str]:
    saved_assets: list[str] = []
    for item in items:
        import_dir = paths.custom_geo_import_dir(setup.shot_dir, item)
        unreal.EditorAssetLibrary.make_directory(import_dir)
        texture_result = _import_setdec_textures(item, import_dir, warn=warn)
        mat_dir = "{}/MAT".format(import_dir)
        saved_assets.extend(alembic_ops.import_alembic_items(setup, [item]))

        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        target_label = paths.custom_geo_actor_label(item.name)
        cache_actor = next(
            (actor for actor in actors if actor.get_actor_label() == target_label),
            None,
        )
        if cache_actor is not None:
            _assign_setdec_materials_to_geometry_cache(
                cache_actor,
                texture_result.imported_textures,
                mat_dir,
                warn=warn,
            )
        print("Set Dec Alembic imported into sequencer: {}".format(item.name))
    return saved_assets


def import_setdec_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
    *,
    warn: WarnFn = _warn_default,
) -> list[str]:
    fbx_items = [item for item in items if item.export_format == EXPORT_FORMAT_FBX]
    alembic_items = [
        item for item in items if item.export_format == EXPORT_FORMAT_ALEMBIC
    ]
    saved: list[str] = []
    if fbx_items:
        saved.extend(import_setdec_fbx_items(setup, fbx_items, warn=warn))
    if alembic_items:
        saved.extend(import_setdec_alembic_items(setup, alembic_items, warn=warn))
    return saved
