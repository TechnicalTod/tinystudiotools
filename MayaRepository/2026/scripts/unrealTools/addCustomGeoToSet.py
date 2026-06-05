"""Shelf command: add selected transforms to the Unreal custom geo set."""

from unrealTools.shotPublisher.custom_geo_sets import add_selection_to_custom_geo_set


def run():
    add_selection_to_custom_geo_set()
