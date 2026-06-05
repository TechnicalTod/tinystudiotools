"""Create shot level, sequence, and content folders in Unreal."""

from __future__ import annotations

from dataclasses import dataclass

import unreal

from . import paths
from .constants import ANIMATION_SUBDIR, MEDIA_SUBDIR
from .manifest import ShotInfo


@dataclass
class ShotSetupResult:
    shot_dir: str
    level_asset_path: str
    sequence_asset_path: str
    start_frame: float
    end_frame: float
    fps: float


def _ensure_directory(dir_path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
        unreal.EditorAssetLibrary.make_directory(dir_path)


def _configure_sequence_fps(loaded_level_sequence, fps_val: float) -> None:
    new_frame_rate = unreal.FrameRate()
    fps_val = round(fps_val, 3)
    new_frame_rate.numerator = int(fps_val * 1000)
    new_frame_rate.denominator = 1000
    if fps_val == 23.976:
        new_frame_rate.numerator = int(24.0 * 1000)
        new_frame_rate.denominator = 1001
    loaded_level_sequence.set_display_rate(new_frame_rate)


def create_shot_setup(shot_info: ShotInfo) -> ShotSetupResult:
    shot_dir = paths.shot_version_dir(shot_info)
    _ensure_directory(shot_dir)
    _ensure_directory("{}/{}".format(shot_dir, ANIMATION_SUBDIR))
    _ensure_directory("{}/{}".format(shot_dir, MEDIA_SUBDIR))

    level_asset_path = paths.level_asset_path(
        shot_dir, shot_info.shot_number, shot_info.version
    )
    sequence_asset_path = paths.sequence_asset_path(
        shot_dir, shot_info.shot_number, shot_info.version
    )

    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset_path + ".umap"):
        level_library = unreal.EditorLevelLibrary()
        success = level_library.new_level(level_asset_path)
        if success:
            print("New level created: {}.umap".format(level_asset_path))
        else:
            print("Failed to create new level.")

    if not unreal.EditorAssetLibrary.does_asset_exist(sequence_asset_path + ".uasset"):
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.LevelSequenceFactoryNew()
        sequence_name = sequence_asset_path.split("/")[-1]
        sequence_asset = asset_tools.create_asset(sequence_name, shot_dir, None, factory)
        if sequence_asset:
            print("Level Sequence created: {}.uasset".format(sequence_asset_path))
        else:
            print("Failed to create Level Sequence.")

    loaded_level_sequence = unreal.load_asset(sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)

    start_frame = shot_info.start_frame
    end_frame = shot_info.playback_end_frame
    fps_val = shot_info.fps

    _configure_sequence_fps(loaded_level_sequence, fps_val)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(float(start_frame))
    loaded_level_sequence.set_playback_start(float(start_frame))
    loaded_level_sequence.set_playback_end(float(end_frame))
    loaded_level_sequence.set_view_range_start(float(start_frame - 0) / float(fps_val))
    loaded_level_sequence.set_view_range_end(float(end_frame + 9) / float(fps_val))
    loaded_level_sequence.set_work_range_start(float(start_frame - 10) / float(fps_val))
    loaded_level_sequence.set_work_range_end(float(end_frame + 9) / float(fps_val))

    print("Folder structure and assets created under: {}".format(shot_dir))

    return ShotSetupResult(
        shot_dir=shot_dir,
        level_asset_path=level_asset_path,
        sequence_asset_path=sequence_asset_path,
        start_frame=start_frame,
        end_frame=end_frame,
        fps=fps_val,
    )
