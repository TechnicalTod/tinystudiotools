"""Unreal scene adapter.

``unreal`` is imported lazily so this module stays importable outside Unreal.
Unlike Maya, Unreal is Z-up, so this adapter owns the coordinate conversion:
the numpy / ``transforms3d`` basis-change math (previously in
``genTools.conversionUtilites`` + ``matrixComposition`` + ``changeOfBasis``)
lives here, used in both directions.
"""

from __future__ import annotations

import math
import os
import warnings
from typing import List, Optional, Tuple

import numpy as np
from transforms3d import affines, euler

from ..core.paths import (
    complete_path,
    disk_asset_folder,
    parse_ue_setdec_static_mesh_object_path,
)
from ..core.records import AssetRecord
from .base import SceneAdapter, SceneAdapterError

ENV_ROOT = "ENV"

# Y-up (Maya / USD) <-> Z-up (Unreal) change-of-basis.
_YUP_TO_ZUP = np.array(
    [
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ],
    dtype=int,
)


class UnrealAdapter(SceneAdapter):
    """Gather / rebuild the ``ENV`` actor hierarchy via the ``unreal`` API."""

    name = "unreal"
    label = "Unreal"

    def __init__(self) -> None:
        try:
            import unreal  # noqa: F401
        except Exception as exc:  # pragma: no cover - only runs inside Unreal
            raise SceneAdapterError(
                "UnrealAdapter requires running inside Unreal Engine."
            ) from exc

    # ---- export ---------------------------------------------------------
    def gather(self) -> List[AssetRecord]:
        import unreal
        import pxr.Gf as Gf

        editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors = editor_actor_subsystem.get_all_level_actors()

        env_actor = next(
            (a for a in all_actors if a.get_actor_label() == ENV_ROOT), None
        )
        if env_actor is None:
            warnings.warn("Actor named 'ENV' not found.")
            return []

        records: List[AssetRecord] = []

        def collect(actor, path: str = "") -> None:
            actor_name = actor.get_actor_label()
            full_path = f"{path}/{actor_name}" if path else actor_name

            parent_actor = actor.get_attach_parent_actor()
            if parent_actor is not None:
                local = actor.get_actor_transform().make_relative(
                    parent_actor.get_actor_transform()
                )
            else:
                local = actor.get_actor_transform()
            t = local.translation
            r = local.rotation
            s = local.scale3d

            translation = np.array([t.x, t.y, t.z])
            rotation = _euler_from_quaternion(r.x, r.y, r.z, r.w)
            scale = np.array([s.x, s.y, s.z])

            usd_t, usd_r, usd_s = _from_to_rotation_conversion(
                translation, rotation, scale, 1
            )
            usd_matrix = np.transpose(_compose_matrix(usd_t, usd_r, usd_s))

            asset_name = base_path = version = variant = None
            mesh_path = _static_mesh_path(actor)
            if mesh_path:
                asset_path = mesh_path.split(".")[0]
                mesh_asset = unreal.EditorAssetLibrary.find_asset_data(
                    asset_path
                ).get_asset()
                asset_name = unreal.EditorAssetLibrary.get_metadata_tag(
                    mesh_asset, "FBX.assetName"
                )
                base_path = unreal.EditorAssetLibrary.get_metadata_tag(
                    mesh_asset, "FBX.basePath"
                )
                version = unreal.EditorAssetLibrary.get_metadata_tag(
                    mesh_asset, "FBX.version"
                )
                variant = unreal.EditorAssetLibrary.get_metadata_tag(
                    mesh_asset, "FBX.variantName"
                )
                asset_name, base_path, version, variant = _resolve_setdec_publish_info(
                    asset_path,
                    asset_name,
                    base_path,
                    version,
                    variant,
                )

            records.append(
                AssetRecord(
                    hierarchy_path=full_path,
                    transform=Gf.Matrix4d(usd_matrix),
                    asset_name=asset_name,
                    base_path=base_path,
                    version=version,
                    variant=variant,
                )
            )

            for child in actor.get_attached_actors():
                collect(child, full_path)

        collect(env_actor)
        return records

    # ---- import ---------------------------------------------------------
    def apply(self, records: List[AssetRecord]) -> None:
        import unreal

        ensured_imports: set[tuple[str, str, str, str]] = set()
        auto_imported = 0

        for record in records:
            if record.transform is not None:
                local = np.transpose(np.array(record.transform))
                t, r, s = _decompose_matrix(local)
                translation, rotation, scale = _from_to_rotation_conversion(t, r, s, 1)
            else:
                translation = rotation = scale = None

            if record.is_group:
                actor = _get_or_create_actor_hierarchy(record.hierarchy_path)
            else:
                variant = record.variant or "base"
                normalized_base = (record.base_path or "").replace("\\", "/").rstrip(
                    "/"
                )
                ue_path = complete_path(
                    record.base_path,
                    variant,
                    record.version,
                    record.asset_name,
                    "ue",
                )
                asset = unreal.load_asset(ue_path)
                if asset is None:
                    import_key = (
                        normalized_base,
                        record.asset_name,
                        variant,
                        record.version,
                    )
                    if import_key not in ensured_imports:
                        from assetTools.setdec_import_ops import (
                            ensure_setdec_static_mesh_imported,
                        )

                        disk_asset_path = disk_asset_folder(
                            record.base_path, record.asset_name
                        )
                        if ensure_setdec_static_mesh_imported(
                            disk_asset_path,
                            variant,
                            record.version,
                            warn=unreal.log_warning,
                        ):
                            auto_imported += 1
                        ensured_imports.add(import_key)
                    asset = unreal.load_asset(ue_path)
                if asset is None:
                    unreal.log_warning(f"Asset not found for path: {ue_path}")
                    continue
                actor = _get_or_create_actor_hierarchy(record.hierarchy_path, asset=asset)

            if actor is not None and translation is not None:
                _apply_transform(actor, translation, rotation, scale)

        if auto_imported:
            unreal.log(
                "SetDec scene import: auto-imported {} Set Dec asset(s).".format(
                    auto_imported
                )
            )

        _freeze_static_meshes()


# ---------------------------------------------------------------------------
# Unreal scene helpers


def _nonempty_tag(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _resolve_setdec_publish_info(
    mesh_object_path: str,
    asset_name: Optional[str],
    base_path: Optional[str],
    version: Optional[str],
    variant: Optional[str],
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Fill missing publish metadata from the UE content path."""
    asset_name = _nonempty_tag(asset_name)
    base_path = _nonempty_tag(base_path)
    version = _nonempty_tag(version)
    variant = _nonempty_tag(variant)

    if asset_name and base_path and version and variant:
        return asset_name, base_path, version, variant

    parsed = parse_ue_setdec_static_mesh_object_path(mesh_object_path)
    if parsed is None:
        return asset_name, base_path, version, variant

    group_base_path = _show_setdec_group_folder(parsed.group_name)
    return (
        asset_name or parsed.asset_name,
        base_path or group_base_path,
        version or parsed.version,
        variant or parsed.variant,
    )


def _show_setdec_group_folder(group_name: str) -> Optional[str]:
    show = os.environ.get("SHOW_NAME", "").strip()
    if not show:
        return None

    try:
        from genTools.studio_python_path import ensure_gen_tools_shared

        ensure_gen_tools_shared()
        from studioShowPaths import setdec_group_folder

        return setdec_group_folder(show, group_name, trailing_slash=True)
    except Exception:
        base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR", "").strip()
        if not base:
            return None
        show_root = f"{base.replace(chr(92), '/').rstrip('/')}/{show}"
        return f"{show_root}/assets/setdec/{group_name}/"


def _static_mesh_path(actor):
    import unreal

    if not isinstance(actor, unreal.StaticMeshActor):
        return None
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component or not component.static_mesh:
        return None
    return component.static_mesh.get_path_name()


def _get_or_create_actor_hierarchy(usd_hierarchy: str, asset=None):
    import unreal

    parts = usd_hierarchy.strip("/").split("/")
    parent_actor = None
    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    for i, actor_name in enumerate(parts):
        existing_actor = None
        for candidate in editor_actor_subsystem.get_all_level_actors():
            if (
                candidate.get_actor_label() == actor_name
                and candidate.get_attach_parent_actor() == parent_actor
            ):
                existing_actor = candidate
                break

        if not existing_actor:
            is_leaf_asset = asset and i == len(parts) - 1
            if is_leaf_asset:
                existing_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
                    asset, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
                )
                if existing_actor and existing_actor.root_component:
                    existing_actor.root_component.set_mobility(
                        unreal.ComponentMobility.MOVABLE
                    )
            else:
                existing_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                    unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
                )
            existing_actor.set_actor_label(actor_name)

        if parent_actor and existing_actor:
            if existing_actor.get_attach_parent_actor() != parent_actor:
                existing_actor.attach_to_actor(
                    parent_actor,
                    unreal.Name(""),
                    unreal.AttachmentRule.KEEP_WORLD,
                    unreal.AttachmentRule.KEEP_WORLD,
                    unreal.AttachmentRule.KEEP_WORLD,
                    False,
                )

        parent_actor = existing_actor

    return parent_actor


def _apply_transform(actor, translation, rotation, scale) -> None:
    import unreal

    actor.set_actor_relative_location(
        unreal.Vector(translation[0], translation[1], translation[2]),
        sweep=False,
        teleport=True,
    )
    actor.set_actor_relative_scale3d(unreal.Vector(*scale))
    # Unreal uses Pitch (X), Yaw (Y), Roll (Z); flip X/Y to match the converter.
    actor.set_actor_relative_rotation(
        unreal.Rotator(-rotation[0], -rotation[1], rotation[2]), False, True
    )


def _freeze_static_meshes() -> None:
    """Flip every StaticMeshActor's component from MOVABLE back to STATIC."""
    import unreal

    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in editor_actor_subsystem.get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if component and component.mobility != unreal.ComponentMobility.STATIC:
            component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)


# ---------------------------------------------------------------------------
# Coordinate math (numpy / transforms3d) - Unreal only


def _compose_matrix(trans, rots, scales, order: str = "sxyz"):
    """Compose a 4x4 matrix from translation, rotation (degrees) and scale."""
    radians = [angle / 360.0 * 2.0 * math.pi for angle in rots]
    rot_matrix = euler.euler2mat(*radians, axes=order)
    return affines.compose(trans, rot_matrix, scales)


def _decompose_matrix(matrix, order: str = "sxyz"):
    """Decompose a 4x4 matrix into ``(translation, rotation_deg, scale)``."""
    m_t, m_r, m_s, _ = affines.decompose44(matrix)
    rots = euler.mat2euler(m_r, axes=order)
    rots = [rad * 360.0 / 2.0 / math.pi for rad in rots]
    return list(m_t), rots, list(m_s)


def _change_xform(source_xform, change_of_basis):
    """Re-express a transform in a new basis: ``B * M * inverse(B)``."""
    inverse = np.linalg.inv(change_of_basis)
    return np.matmul(np.matmul(change_of_basis, source_xform), inverse)


def _from_to_rotation_conversion(translation, rotation, scale, units):
    """Convert a Maya/USD (Y-up) transform to/from Unreal (Z-up)."""
    matrix_a = _compose_matrix(translation, rotation, scale, order="sxyz")
    matrix_b = _change_xform(matrix_a, _YUP_TO_ZUP)
    t, r, s = _decompose_matrix(matrix_b, order="sxyz")
    t = (t[0] * units, t[1] * units, t[2] * units)
    return t, r, s


def _euler_from_quaternion(x, y, z, w):
    """Convert a quaternion to Euler angles (degrees)."""
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = max(-1.0, min(1.0, t2))
    pitch_y = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)

    return math.degrees(roll_x), math.degrees(pitch_y), math.degrees(yaw_z)
