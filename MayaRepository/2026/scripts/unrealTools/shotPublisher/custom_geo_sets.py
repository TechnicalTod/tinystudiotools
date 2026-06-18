"""Maya objectSet helpers for custom animated geometry published to Unreal."""

from __future__ import annotations

import pymel.core as pm

from .constants import (
    CUSTOM_GEO_ALEMBIC_SET_NAME,
    CUSTOM_GEO_FBX_SET_NAME,
    CUSTOM_GEO_SET_NAMES,
)


def ensure_custom_geo_set(set_name: str):
    if pm.objExists(set_name):
        return pm.PyNode(set_name)
    return pm.sets(name=set_name, empty=True)


def add_selection_to_set(set_name: str) -> int:
    selection = pm.ls(sl=True, type="transform") or pm.ls(sl=True)
    if not selection:
        print(
            "Nothing selected. Select transform(s) to add to '{}'.".format(set_name)
        )
        return 0

    custom_set = ensure_custom_geo_set(set_name)
    pm.sets(custom_set, edit=True, forceElement=selection)
    print("Added {} item(s) to '{}'.".format(len(selection), set_name))
    return len(selection)


def add_selection_to_fbx_set() -> int:
    return add_selection_to_set(CUSTOM_GEO_FBX_SET_NAME)


def add_selection_to_alembic_set() -> int:
    return add_selection_to_set(CUSTOM_GEO_ALEMBIC_SET_NAME)


def list_set_members(set_name: str) -> list[str]:
    if not pm.objExists(set_name):
        return []

    members = pm.sets(set_name, query=True) or []
    result: list[str] = []
    for member in members:
        if pm.objExists(member):
            result.append(pm.PyNode(member).name())
    return result


def list_custom_animated_geometry_members() -> list[tuple[str, str]]:
    """Return (source_set, member_name) for all publishable custom geo members."""
    entries: list[tuple[str, str]] = []
    for set_name in CUSTOM_GEO_SET_NAMES:
        for member_name in list_set_members(set_name):
            entries.append((set_name, member_name))
    return entries
