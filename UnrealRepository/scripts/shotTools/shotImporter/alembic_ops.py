"""Import published Alembic geometry caches into the shot level sequence."""

from __future__ import annotations

import unreal

import genTools.genUnrealImportUtils as genUnrealImportUtils

from . import paths
from .constants import SEQUENCER_FOLDER_CUSTOM
from .manifest import CustomAnimatedGeometryItem
from .setup_ops import ShotSetupResult


def _ensure_alembic_importer_available() -> None:
    if not hasattr(unreal, "AbcImportSettings"):
        raise RuntimeError("AlembicImporter plugin/API is not available in this Unreal build.")


def _import_geometry_cache(abc_path: str, destination_path: str) -> str:
    _ensure_alembic_importer_available()
    import_task = genUnrealImportUtils.buildAbcImportTask(
        abc_path,
        destination_path,
        genUnrealImportUtils.buildGeometryCacheImportOptions(),
    )
    imported_paths = genUnrealImportUtils.executeImportTasks([import_task])
    if not imported_paths:
        raise RuntimeError(
            "Geometry cache import returned no assets for {}".format(abc_path)
        )

    for asset_path in imported_paths:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path.split(".")[0])
        if isinstance(asset, unreal.GeometryCache):
            return asset_path

    raise RuntimeError(
        "Could not find imported geometry cache asset for {}".format(abc_path)
    )


def _configure_geometry_cache_section(
    section,
    geometry_cache_asset,
) -> None:
    """Set the geometry cache asset on a MovieSceneGeometryCacheSection."""
    for params_prop in ("params", "Params"):
        try:
            params = section.get_editor_property(params_prop)
        except Exception:
            continue

        for cache_prop in ("geometry_cache_asset", "geometry_cache"):
            try:
                params.set_editor_property(cache_prop, geometry_cache_asset)
                section.set_editor_property(params_prop, params)
                return
            except Exception:
                continue

    params_class = getattr(unreal, "MovieSceneGeometryCacheParams", None)
    if params_class is not None:
        params = params_class()
        params.set_editor_property("geometry_cache_asset", geometry_cache_asset)
        section.set_editor_property("params", params)
        return

    raise RuntimeError(
        "Could not configure geometry cache sequencer section params in this Unreal build."
    )


def _add_geometry_cache_track(
    loaded_level_sequence,
    possessable_actor,
    geometry_cache_asset,
    start_frame: float,
    end_frame: float,
) -> None:
    track = possessable_actor.add_track(unreal.MovieSceneGeometryCacheTrack)
    section = track.add_section()
    section.set_range(int(start_frame), int(end_frame))
    _configure_geometry_cache_section(section, geometry_cache_asset)


def import_alembic_items(
    setup: ShotSetupResult,
    items: list[CustomAnimatedGeometryItem],
) -> list[str]:
    if not items:
        return []

    saved_assets: list[str] = []
    loaded_level_sequence = unreal.load_asset(setup.sequence_asset_path)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(loaded_level_sequence)
    custom_folder = unreal.MovieSceneSequenceExtensions.add_root_folder_to_sequence(
        loaded_level_sequence, SEQUENCER_FOLDER_CUSTOM
    )

    for item in items:
        import_dir = paths.custom_geo_import_dir(setup.shot_dir, item)
        unreal.EditorAssetLibrary.make_directory(import_dir)
        geometry_cache_path = _import_geometry_cache(item.export_path, import_dir)
        saved_assets.append(geometry_cache_path.split(".")[0])
        geometry_cache_asset = unreal.load_asset(geometry_cache_path.split(".")[0])

        cache_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.GeometryCacheActor,
            unreal.Vector(0, 0, 0),
        )
        cache_actor.set_actor_label(paths.custom_geo_actor_label(item.name))
        cache_actor.set_folder_path(SEQUENCER_FOLDER_CUSTOM)
        cache_component = cache_actor.geometry_cache_component
        cache_component.set_geometry_cache(geometry_cache_asset)

        possessable_actor = loaded_level_sequence.add_possessable(cache_actor)
        custom_folder.add_child_object_binding(possessable_actor)
        _add_geometry_cache_track(
            loaded_level_sequence,
            possessable_actor,
            geometry_cache_asset,
            setup.start_frame,
            setup.end_frame,
        )

        print("Alembic geometry cache imported into sequencer: {}".format(item.name))
        print("From import path: {}".format(item.export_path))

    return saved_assets
