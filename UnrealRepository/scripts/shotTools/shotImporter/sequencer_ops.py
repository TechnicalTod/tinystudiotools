"""Sequencer track helpers for shot import.

Shot-importer-specific variant with explicit frame ranges. See
``shotTools.sequencerFunctions`` for the simpler generic example.
"""

from __future__ import annotations

import unreal


def add_skeletal_animation_track(
    animation_path: str,
    possessable_actor,
    start_frame: float,
    end_frame: float,
) -> None:
    animation_asset = unreal.AnimSequence.cast(unreal.load_asset(animation_path))
    params = unreal.MovieSceneSkeletalAnimationParams()
    params.set_editor_property("Animation", animation_asset)
    animation_track = possessable_actor.add_track(
        track_type=unreal.MovieSceneSkeletalAnimationTrack
    )
    animation_section = animation_track.add_section()
    animation_section.set_editor_property("Params", params)
    animation_section.set_range(start_frame, end_frame)
