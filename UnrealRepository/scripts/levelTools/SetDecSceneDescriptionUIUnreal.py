"""Unreal menu entry point for the shared SetDec scene-description IO tool.

Keep this module thin - it only exists so the Unreal tools menu has a stable
``levelTools.SetDecSceneDescriptionUIUnreal.show`` target. The real
implementation lives in ``setdec_scene_description_io`` (under
``GenTools/SetDecSceneDescriptionIO/src``, added to PYTHONPATH by the launcher).
"""

from __future__ import annotations


def show():
    """Open the SetDec scene-description IO window parented to Unreal."""
    from genTools.studio_python_path import ensure_setdec_scene_description_io

    ensure_setdec_scene_description_io()
    from setdec_scene_description_io.ui.main_window import show as show_scene_description

    return show_scene_description(host="unreal")


launch = show
