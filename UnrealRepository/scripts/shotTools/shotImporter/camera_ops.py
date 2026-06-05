"""Import published cameras into the shot level sequence."""

from __future__ import annotations

import unreal

from . import media_plate_ops
from .constants import SEQUENCER_FOLDER_CAM
from .manifest import CameraItem
from .setup_ops import ShotSetupResult


def import_cameras(setup: ShotSetupResult, cameras: list[CameraItem]) -> None:
    loaded_level_sequence = unreal.load_asset(setup.sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
    cam_folder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(
        loaded_level_sequence, SEQUENCER_FOLDER_CAM
    )

    for camera in cameras:
        camera_fbx_path = camera.export_path
        sensor_width = camera.horizontal_film_aperture
        sensor_height = camera.vertical_film_aperture
        image_plate = camera.image_plate

        cine_camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor, unreal.Vector(0, 0, 0)
        )
        cine_camera.set_folder_path(SEQUENCER_FOLDER_CAM)
        cine_camera.set_actor_label(camera.name + "_UECam")

        possessable_actor = loaded_level_sequence.add_possessable(cine_camera)
        binding_id = unreal.MovieSceneObjectBindingID()
        binding_id.set_editor_property("guid", possessable_actor.get_id())

        track = loaded_level_sequence.add_track(unreal.MovieSceneCameraCutTrack)
        section = track.add_section()
        section.set_range(setup.start_frame, setup.end_frame)

        import_setting = unreal.MovieSceneUserImportFBXSettings()
        import_setting.set_editor_property("match_by_name_only", False)
        import_setting.set_editor_property("force_front_x_axis", False)
        import_setting.set_editor_property("create_cameras", False)
        import_setting.set_editor_property("reduce_keys", False)
        import_setting.set_editor_property("reduce_keys_tolerance", 0.001)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.SequencerTools.import_level_sequence_fbx(
            world,
            loaded_level_sequence,
            [possessable_actor],
            import_setting,
            camera_fbx_path,
        )

        filmback_settings = unreal.CameraFilmbackSettings(
            sensor_width=sensor_width, sensor_height=sensor_height
        )
        camera_component = cine_camera.get_cine_camera_component()
        camera_component.set_editor_property("filmback", filmback_settings)

        cam_folder.add_child_object_binding(possessable_actor)
        media_plate_ops.import_image_plate(setup.shot_dir, image_plate, camera_component)
        print("Camera imported into sequencer: {}".format(camera.name))
        print("From import path: {}".format(camera_fbx_path))

        section.set_camera_binding_id(binding_id)
