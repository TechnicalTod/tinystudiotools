"""Shelf command: add selected transforms to the Unreal custom geo Alembic set."""

from unrealTools.shotPublisher.custom_geo_sets import add_selection_to_alembic_set


def run():
    add_selection_to_alembic_set()
