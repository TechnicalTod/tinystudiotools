"""Image plate / MediaPlatePlus setup for imported cameras."""

from __future__ import annotations

import unreal

from .constants import MEDIA_PLATE_BLUEPRINT
from .paths import media_dir, media_source_asset_path


def create_img_source(asset_name: str, asset_path: str, sequence_path: str):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    img_media_source_class = unreal.ImgMediaSource
    img_media_source_asset = asset_tools.create_asset(
        asset_name,
        asset_path,
        img_media_source_class,
        None,
    )

    if img_media_source_asset:
        directory_path = unreal.DirectoryPath(path=sequence_path)
        img_media_source_asset.set_editor_property("sequence_path", directory_path)
        full_asset_path = "{}/{}".format(asset_path, asset_name)
        unreal.EditorAssetLibrary.save_asset(full_asset_path)
        print(
            "Successfully created Img Media Source asset: {} at path: {}".format(
                asset_name, full_asset_path
            )
        )
        return img_media_source_asset

    print(
        "Failed to create Img Media Source asset: {} at path: {}".format(
            asset_name, asset_path
        )
    )
    return None


def create_in_memory_media_playlist(img_media_source):
    try:
        new_media_playlist = unreal.MediaPlaylist()
        if new_media_playlist:
            new_media_playlist.add(img_media_source)
            print("Successfully created in-memory MediaPlaylist.")
            return new_media_playlist
        print("Failed to create the in-memory MediaPlaylist instance.")
        return None
    except Exception as exc:
        print("Failed to create in-memory MediaPlaylist: {}".format(exc))
        return None


def add_media_source_to_sequence(media_plate_actor, img_media_source) -> None:
    try:
        level_sequence = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
        if not level_sequence:
            print("No level sequence currently open.")
            return

        possessable = level_sequence.add_possessable(media_plate_actor)
        media_track = possessable.add_track(unreal.MovieSceneMediaTrack)

        if media_track:
            media_section = media_track.add_section()
            media_section.set_editor_property("media_source", img_media_source)
            start_frame = level_sequence.get_playback_start()
            end_frame = level_sequence.get_playback_end()
            media_section.set_range(start_frame, end_frame)
            print(
                "Successfully set media section range from frame {} to {}.".format(
                    start_frame, end_frame
                )
            )
            print(
                "Successfully added MediaPlatePlus to the level sequence with the correct media source."
            )
        else:
            print("Failed to create media source track on the possessable.")
    except Exception as exc:
        print("Failed to add MediaPlatePlus to the level sequence: {}".format(exc))


def add_media_plate_plus_to_level(
    img_media_source_path: str,
    media_plate_blueprint_path: str,
    camera_actor,
) -> None:
    media_plate_gc = unreal.EditorAssetLibrary.load_blueprint_class(media_plate_blueprint_path)
    if not media_plate_gc:
        print(
            "Failed to load Generated Class from MediaPlatePlus Blueprint at: {}".format(
                media_plate_blueprint_path
            )
        )
        return

    if not camera_actor:
        print("Failed to load camera actor")
        return

    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    spawn_location = unreal.Vector(0.0, 0.0, 0.0)
    media_plate_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        media_plate_gc, spawn_location
    )

    if not media_plate_actor:
        print("Failed to spawn MediaPlatePlus actor.")
        return

    try:
        media_plate_actor.set_editor_property("CameraLink", camera_actor)
        print("Successfully set CameraLink on MediaPlatePlus actor instance.")
    except Exception as exc:
        print("Failed to set CameraLink on MediaPlatePlus actor instance: {}".format(exc))

    img_media_source = None
    media_plate_component = media_plate_actor.media_plate_component
    if media_plate_component:
        img_media_source = unreal.EditorAssetLibrary.load_asset(img_media_source_path)
        if img_media_source:
            new_media_playlist = create_in_memory_media_playlist(img_media_source)
            if new_media_playlist:
                media_plate_component.set_editor_property("media_playlist", new_media_playlist)
                print("Successfully set new in-memory media playlist on MediaPlateComponent.")
        else:
            print("Failed to load ImgMediaSource asset at: {}".format(img_media_source_path))
    else:
        print("MediaPlatePlus actor does not have a media_plate_component.")

    add_media_source_to_sequence(media_plate_actor, img_media_source)


def import_image_plate(shot_dir: str, image_plate: str, camera_component) -> None:
    if not image_plate:
        return

    print(image_plate)
    print(camera_component)

    media_folder_path = media_dir(shot_dir)
    path_parts = shot_dir.split("/")
    asset_name = "_".join(path_parts[-2:])
    camera_actor = camera_component.get_owner()
    exr_dir = "/".join(image_plate.split("/")[:-1])

    create_img_source(asset_name, media_folder_path, exr_dir)
    add_media_plate_plus_to_level(
        media_source_asset_path(shot_dir),
        MEDIA_PLATE_BLUEPRINT,
        camera_actor,
    )
