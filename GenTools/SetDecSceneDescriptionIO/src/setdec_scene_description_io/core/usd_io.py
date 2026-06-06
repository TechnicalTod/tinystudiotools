"""USD stage read / write - the shared half of every exporter and builder.

This module is the single home for the prim-hierarchy + ``assetInfo`` + transform
logic that used to be duplicated in ``USDSceneExporterMaya``,
``USDSceneExporterUnreal``, ``USDSceneBuilderMaya`` and ``USDSceneBuilderUnreal``.
It depends only on ``pxr`` (available in both Maya and Unreal) and never touches
a DCC API directly.
"""

from __future__ import annotations

import os
import warnings
from typing import List

import pxr.Gf as Gf
import pxr.Usd as Usd
import pxr.UsdGeom as UsdGeom

from .paths import complete_path
from .records import AssetRecord


def parse_usd(file_path: str) -> List[AssetRecord]:
    """Read a scene-description ``.usda`` into :class:`AssetRecord` objects.

    Each ``Xform`` prim becomes one record carrying its local transform and any
    ``assetInfo`` metadata (``name`` / ``path`` / ``version`` / ``variant``).
    """
    stage = Usd.Stage.Open(file_path)
    records: List[AssetRecord] = []

    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Xform):
            continue

        xform = UsdGeom.Xformable(prim)
        local_transformation = xform.GetLocalTransformation()

        asset_name = base_path = version = variant = None
        if prim.HasMetadata("assetInfo"):
            asset_info = prim.GetMetadata("assetInfo")
            asset_name = asset_info.get("name")
            base_path = asset_info.get("path")
            version = asset_info.get("version")
            variant = asset_info.get("variant")

        records.append(
            AssetRecord(
                hierarchy_path=prim.GetPath().pathString,
                transform=local_transformation,
                asset_name=asset_name,
                base_path=base_path,
                version=version,
                variant=variant,
            )
        )

    return records


def write_usd(file_path: str, records: List[AssetRecord]):
    """Serialise records to a new ``.usda`` scene description.

    Refuses to overwrite an existing file (versioning is the caller's job).
    Returns the written path, or ``None`` when nothing was written.
    """
    if not file_path.lower().endswith((".usd", ".usda")):
        file_path = file_path + ".usda"

    if not records:
        return None

    if os.path.exists(file_path):
        warnings.warn(
            f"The usd path at {file_path} already exists. Please remove it or change the path"
        )
        return None

    stage = Usd.Stage.CreateNew(file_path)

    for record in records:
        # Build the prim hierarchy down to this record's path.
        parent_path = "/"
        for node_name in record.hierarchy_path.split("/"):
            if not node_name:
                continue
            current_path = parent_path + node_name
            if not stage.GetPrimAtPath(current_path):
                stage.DefinePrim(current_path, "Xform")
            parent_path = current_path + "/"

        prim = stage.GetPrimAtPath(parent_path[:-1])  # drop trailing '/'

        if not record.is_group:
            reference = complete_path(
                record.base_path,
                record.variant or "base",
                record.version,
                record.asset_name,
                "usd",
            )
            prim.GetReferences().AddReference(reference)

            # Structured metadata readable in both Unreal and Houdini.
            prim.SetAssetInfoByKey("name", record.asset_name)
            prim.SetAssetInfoByKey("path", record.base_path)
            prim.SetAssetInfoByKey("version", record.version)
            prim.SetAssetInfoByKey("variant", record.variant)

        if record.transform is not None:
            _set_transform(prim, record.transform)

    stage.GetRootLayer().Save()
    return file_path


def _set_transform(prim, matrix) -> None:
    """Set (or update) the prim's single transform xformOp from ``matrix``."""
    xform = UsdGeom.Xformable(prim)
    xform_ops = xform.GetOrderedXformOps()
    xform_op = next(
        (op for op in xform_ops if op.GetOpType() == UsdGeom.XformOp.TypeTransform),
        None,
    )
    if xform_op is None:
        xform_op = xform.AddTransformOp()
    xform_op.Set(Gf.Matrix4d(matrix))
