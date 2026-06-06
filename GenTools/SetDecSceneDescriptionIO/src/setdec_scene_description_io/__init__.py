"""TinyStudio cross-DCC SetDec scene-description IO.

Round-trips an environment ("setdec") layout between Maya and Unreal through a
shared ``.usda`` scene description. The host-agnostic USD read/write lives in
:mod:`setdec_scene_description_io.core`; per-DCC scene gathering and rebuilding
lives in :mod:`setdec_scene_description_io.adapters`.
"""

__version__ = "0.1.0"
