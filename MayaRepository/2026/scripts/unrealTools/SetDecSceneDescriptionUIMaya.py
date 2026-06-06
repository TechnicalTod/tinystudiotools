"""Maya shelf entry point for the shared SetDec scene-description IO tool.

Keep this module thin - it only exists so the Maya tools menu has a stable
``unrealTools.SetDecSceneDescriptionUIMaya.launch`` target. The real
implementation lives in ``setdec_scene_description_io`` (under
``GenTools/SetDecSceneDescriptionIO/src``, added to PYTHONPATH by the launcher).
"""

from __future__ import annotations


def launch():
    """Open the SetDec scene-description IO window parented to Maya."""
    from genTools.studio_python_path import ensure_setdec_scene_description_io

    ensure_setdec_scene_description_io()
    from setdec_scene_description_io.ui.main_window import show_in_maya

    return show_in_maya()
