"""Import published puppet animation into the shot level sequence."""

from __future__ import annotations

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from . import paths, sequencer_ops
from .constants import SEQUENCER_FOLDER_ANIM
from .manifest import PuppetItem
from .setup_ops import ShotSetupResult


def import_animation_fbx(
    puppet_fbx_path: str,
    animation_folder_path: str,
    skeleton_path: str,
) -> list[str]:
    import_task = genUnrealImportUtils.buildImportTask(
        puppet_fbx_path,
        animation_folder_path,
        genUnrealImportUtils.buildAnimationImportOptions(skeleton_path),
    )
    return genUnrealImportUtils.executeImportTasks([import_task])


def _resolve_skeletal_assets(puppet: PuppetItem) -> tuple[str, str]:
    skeletal_mesh_base_path = paths.puppet_asset_dir(puppet)
    all_assets = unreal.EditorAssetLibrary.list_assets(skeletal_mesh_base_path)
    skeletal_mesh_path = None
    skeleton_path = None

    for asset_path in all_assets:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.SkeletalMesh):
            skeletal_mesh_path = asset_path
        if isinstance(asset, unreal.Skeleton):
            skeleton_path = asset_path

    if not skeletal_mesh_path or not skeleton_path:
        raise RuntimeError(
            "Could not find skeletal mesh and skeleton under {}".format(
                skeletal_mesh_base_path
            )
        )
    return skeletal_mesh_path, skeleton_path


def import_puppets(setup: ShotSetupResult, puppets: list[PuppetItem]) -> None:
    animation_folder_path = paths.animation_dir(setup.shot_dir)
    loaded_level_sequence = unreal.load_asset(setup.sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
    puppet_folder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(
        loaded_level_sequence, SEQUENCER_FOLDER_ANIM
    )

    for puppet in puppets:
        skeletal_mesh_path, skeleton_path = _resolve_skeletal_assets(puppet)
        imported_animation = import_animation_fbx(
            puppet.export_path,
            animation_folder_path,
            skeleton_path,
        )
        if not imported_animation:
            raise RuntimeError(
                "Animation FBX import returned no assets for {}".format(puppet.name)
            )

        loaded_skeletal_mesh = unreal.load_asset(skeletal_mesh_path)
        skeletal_mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0)
        )
        skeletal_mesh_actor.set_actor_label(puppet.name)
        skeletal_mesh_actor.set_folder_path(SEQUENCER_FOLDER_ANIM)
        skeletal_mesh_component = skeletal_mesh_actor.get_component_by_class(
            unreal.SkeletalMeshComponent
        )
        skeletal_mesh_component.set_skeletal_mesh(loaded_skeletal_mesh)

        possessable_actor = loaded_level_sequence.add_possessable(skeletal_mesh_actor)
        sequencer_ops.add_skeletal_animation_track(
            imported_animation[0],
            possessable_actor,
            setup.start_frame,
            setup.end_frame,
        )
        puppet_folder.add_child_object_binding(possessable_actor)
