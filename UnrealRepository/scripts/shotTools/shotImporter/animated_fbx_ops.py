"""Import published custom animated FBX static meshes into the shot level sequence."""

from __future__ import annotations

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from . import paths
from .constants import SEQUENCER_FOLDER_CUSTOM
from .manifest import CustomAnimatedGeometryItem
from .setup_ops import ShotSetupResult


def _sequencer_fbx_import_settings() -> unreal.MovieSceneUserImportFBXSettings:
    import_setting = unreal.MovieSceneUserImportFBXSettings()
    import_setting.set_editor_property("match_by_name_only", True)
    import_setting.set_editor_property("force_front_x_axis", False)
    import_setting.set_editor_property("create_cameras", False)
    import_setting.set_editor_property("reduce_keys", False)
    import_setting.set_editor_property("reduce_keys_tolerance", 0.001)
    return import_setting


def import_static_mesh_fbx(fbx_path: str, destination_path: str) -> str:
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
    genUnrealImportUtils.executeImportTasks([import_task])
    return genUnrealImportUtils.resolve_static_mesh_object_path(
        import_task,
        destination_path,
    )


def _spawn_static_mesh_item(
    setup: ShotSetupResult,
    item: CustomAnimatedGeometryItem,
    static_mesh_path: str,
    loaded_level_sequence,
    custom_folder,
    world,
) -> None:
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

    if item.animated:
        unreal.SequencerTools.import_level_sequence_fbx(
            world,
            loaded_level_sequence,
            [possessable_actor],
            _sequencer_fbx_import_settings(),
            item.export_path,
        )


def import_animated_fbx_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
) -> list[str]:
    if not items:
        return []

    saved_assets: list[str] = []
    destination_root = paths.custom_geo_fbx_dir(setup.shot_dir)
    unreal.EditorAssetLibrary.make_directory(destination_root)

    loaded_level_sequence = unreal.load_asset(setup.sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
    custom_folder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(
        loaded_level_sequence, SEQUENCER_FOLDER_CUSTOM
    )
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    for item in items:
        import_dir = paths.custom_geo_import_dir(setup.shot_dir, item)
        unreal.EditorAssetLibrary.make_directory(import_dir)
        static_mesh_path = import_static_mesh_fbx(item.export_path, import_dir)
        saved_assets.append(static_mesh_path.split(".")[0])
        _spawn_static_mesh_item(
            setup,
            item,
            static_mesh_path,
            loaded_level_sequence,
            custom_folder,
            world,
        )
        print("Custom animated FBX imported into sequencer: {}".format(item.name))
        print("From import path: {}".format(item.export_path))

    return saved_assets
