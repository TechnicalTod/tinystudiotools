"""Import published custom geo static meshes into the shot level sequence."""

from __future__ import annotations

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from . import paths
from .constants import SEQUENCER_FOLDER_CUSTOM
from .manifest import CustomGeoItem
from .setup_ops import ShotSetupResult


def _sequencer_fbx_import_settings() -> unreal.MovieSceneUserImportFBXSettings:
    import_setting = unreal.MovieSceneUserImportFBXSettings()
    import_setting.set_editor_property("match_by_name_only", False)
    import_setting.set_editor_property("force_front_x_axis", False)
    import_setting.set_editor_property("create_cameras", False)
    import_setting.set_editor_property("reduce_keys", False)
    import_setting.set_editor_property("reduce_keys_tolerance", 0.001)
    return import_setting


def _import_static_mesh(fbx_path: str, destination_path: str) -> str:
    import_options = genUnrealImportUtils.buildStaticMeshImportOptions()
    import_options.static_mesh_import_data.set_editor_property(
        "transform_vertex_to_absolute", False
    )
    import_options.static_mesh_import_data.set_editor_property(
        "bake_pivot_in_vertex", False
    )
    import_task = genUnrealImportUtils.buildImportTask(
        fbx_path,
        destination_path,
        import_options,
    )
    imported_paths = genUnrealImportUtils.executeImportTasks([import_task])
    if not imported_paths:
        raise RuntimeError("Static mesh FBX import returned no assets for {}".format(fbx_path))

    for asset_path in imported_paths:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            return asset_path

    raise RuntimeError(
        "Could not find imported static mesh asset for {}".format(fbx_path)
    )


def import_custom_geo_items(
    setup: ShotSetupResult,
    items: list[CustomGeoItem],
) -> None:
    custom_geo_folder_path = paths.custom_geo_dir(setup.shot_dir)
    loaded_level_sequence = unreal.load_asset(setup.sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
    custom_folder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(
        loaded_level_sequence, SEQUENCER_FOLDER_CUSTOM
    )
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    for item in items:
        static_mesh_path = _import_static_mesh(item.export_path, custom_geo_folder_path)
        loaded_static_mesh = unreal.load_asset(static_mesh_path)

        static_mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0, 0, 0)
        )
        static_mesh_actor.set_actor_label(paths.custom_geo_actor_label(item.name))
        static_mesh_actor.set_folder_path(SEQUENCER_FOLDER_CUSTOM)
        static_mesh_component = static_mesh_actor.static_mesh_component
        static_mesh_component.set_static_mesh(loaded_static_mesh)

        possessable_actor = loaded_level_sequence.add_possessable(static_mesh_actor)
        custom_folder.add_child_object_binding(possessable_actor)

        unreal.SequencerTools.import_level_sequence_fbx(
            world,
            loaded_level_sequence,
            [possessable_actor],
            _sequencer_fbx_import_settings(),
            item.export_path,
        )

        print("Custom geo imported into sequencer: {}".format(item.name))
        print("From import path: {}".format(item.export_path))
