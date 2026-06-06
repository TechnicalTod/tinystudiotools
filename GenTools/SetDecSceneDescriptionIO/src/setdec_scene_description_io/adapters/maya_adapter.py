"""Maya scene adapter.

``pymel`` and ``pxr`` are imported lazily so this module stays importable from a
standalone Python (the factory only instantiates :class:`MayaAdapter` inside
Maya).

Maya is Y-up like USD, so transforms pass through unconverted: the gathered
local matrix is written straight to USD, and a USD local matrix is applied
straight back onto the Maya node.
"""

from __future__ import annotations

import os
import warnings
from typing import List

from ..core.paths import complete_path
from ..core.records import AssetRecord
from .base import SceneAdapter, SceneAdapterError

ENV_ROOT = "ENV"


class MayaAdapter(SceneAdapter):
    """Gather / rebuild the ``ENV`` hierarchy via ``pymel``."""

    name = "maya"
    label = "Maya"

    def __init__(self) -> None:
        try:
            import pymel.core  # noqa: F401
        except Exception as exc:  # pragma: no cover - only runs inside Maya
            raise SceneAdapterError(
                "MayaAdapter requires running inside Autodesk Maya."
            ) from exc

    # ---- export ---------------------------------------------------------
    def gather(self) -> List[AssetRecord]:
        import pymel.core as pm
        import pxr.Gf as Gf

        if not pm.objExists(ENV_ROOT):
            warnings.warn("Actor named 'ENV' not found.")
            return []

        root_null = pm.PyNode(ENV_ROOT)
        all_objects = [root_null] + pm.listRelatives(
            root_null, allDescendents=True, type="transform"
        )

        records: List[AssetRecord] = []
        for obj in all_objects:
            hierarchy_path = obj.longName().replace("|", "/")
            transform = Gf.Matrix4d(obj.getMatrix(worldSpace=False))

            shape = obj.getShape()
            if shape and shape.nodeType() == "mesh":
                if obj.hasAttr("published") and obj.published.get():
                    records.append(
                        AssetRecord(
                            hierarchy_path=hierarchy_path,
                            transform=transform,
                            asset_name=obj.assetName.get(),
                            base_path=obj.basePath.get(),
                            version=obj.version.get(),
                            variant=obj.variantName.get(),
                        )
                    )
                # Unpublished / non-kosher meshes are skipped intentionally.
            else:
                # A plain transform group: keep its place in the hierarchy.
                records.append(
                    AssetRecord(hierarchy_path=hierarchy_path, transform=transform)
                )

        return records

    # ---- import ---------------------------------------------------------
    def apply(self, records: List[AssetRecord]) -> None:
        import pymel.core as pm

        for record in records:
            transform = record.transform
            flat_matrix = (
                _flatten_matrix(transform) if transform is not None else None
            )

            if record.is_group:
                group_node = _find_or_create_transform(record.hierarchy_path)
                if group_node is not None and flat_matrix is not None:
                    pm.xform(group_node, matrix=flat_matrix, relative=False)
                continue

            ma_path = complete_path(
                record.base_path,
                record.variant,
                record.version,
                record.asset_name,
                "maya",
            )
            if not os.path.exists(ma_path):
                print(f"File not found: {ma_path}")
                continue

            parent_path = (
                record.hierarchy_path.rsplit("/", 1)[0]
                if "/" in record.hierarchy_path
                else ""
            )
            parent_node = _find_or_create_transform(parent_path)

            loaded_nodes = pm.importFile(ma_path, returnNewNodes=True)
            asset_node = next(
                node for node in loaded_nodes if pm.nodeType(node) == "transform"
            )
            asset_node.rename(record.asset_name)
            if parent_node is not None:
                pm.parent(asset_node, parent_node)
            if flat_matrix is not None:
                pm.xform(asset_node, matrix=flat_matrix, relative=False)


def _flatten_matrix(matrix) -> tuple:
    """Flatten a 4x4 ``Gf.Matrix4d`` to the 16-float tuple ``pm.xform`` wants."""
    return tuple(element for row in matrix for element in row)


def _find_or_create_transform(path: str):
    """Find or create the Maya transform chain for a slash-delimited path."""
    import pymel.core as pm

    if not path:
        return None

    current_node = None
    for part in path.strip("/").split("/"):
        if not part:
            continue
        full_path = (current_node + "|" + part) if current_node else ("|" + part)
        if pm.objExists(full_path):
            current_node = pm.PyNode(full_path)
        elif current_node:
            current_node = pm.group(em=True, name=part, parent=current_node)
        else:
            current_node = pm.group(em=True, name=part)

    return current_node
