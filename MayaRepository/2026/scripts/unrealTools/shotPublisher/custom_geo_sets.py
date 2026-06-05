"""Maya objectSet helpers for custom geo published to Unreal."""

from __future__ import annotations

import pymel.core as pm

from .constants import CUSTOM_GEO_SET_NAME


def ensure_custom_geo_set():
    if pm.objExists(CUSTOM_GEO_SET_NAME):
        return pm.PyNode(CUSTOM_GEO_SET_NAME)
    return pm.sets(name=CUSTOM_GEO_SET_NAME, empty=True)


def add_selection_to_custom_geo_set() -> int:
    selection = pm.ls(sl=True, type="transform") or pm.ls(sl=True)
    if not selection:
        print("Nothing selected. Select transform(s) to add to '{}'.".format(CUSTOM_GEO_SET_NAME))
        return 0

    custom_set = ensure_custom_geo_set()
    pm.sets(custom_set, edit=True, forceElement=selection)
    print(
        "Added {} item(s) to '{}'.".format(len(selection), CUSTOM_GEO_SET_NAME)
    )
    return len(selection)


def list_custom_geo_members() -> list[str]:
    if not pm.objExists(CUSTOM_GEO_SET_NAME):
        return []

    members = pm.sets(CUSTOM_GEO_SET_NAME, query=True) or []
    result: list[str] = []
    for member in members:
        if pm.objExists(member):
            result.append(pm.PyNode(member).name())
    return result
