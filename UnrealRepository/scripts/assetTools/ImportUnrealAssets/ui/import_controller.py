"""Import orchestration for the Import Unreal Assets UI."""

from __future__ import annotations

import os

from PySide6 import QtWidgets

import genTools.genUnrealUtils as genUnrealUtils

from ..materials.assignment import assign_mesh_materials
from ..publish import identity_from_base_path
from ..publish_layout import (
    asset_manager_asset_root,
    is_asset_manager_asset_root,
    is_asset_manager_version_path,
)
from ..skeletal.import_mesh import import_skeletal_mesh
from ..skeletal.import_textures import import_skeletal_textures
from ..static_mesh.pipelines import (
    import_setdec_static_mesh_pipeline,
    import_static_mesh_publish_pipeline,
)
from .browser_helpers import cell_combo, path_from_table_item
from assetTools.setdec_paths import normalize_disk_path


def run_import_for_table(window) -> None:
    """Run import for all rows in the import table."""
    reply = QtWidgets.QMessageBox.question(
        window,
        "Import Options",
        "Use previous version settings (materials & lightmaps)?",
        QtWidgets.QMessageBox.StandardButton.Yes
        | QtWidgets.QMessageBox.StandardButton.No
        | QtWidgets.QMessageBox.StandardButton.Cancel,
    )
    if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
        return
    use_previous_version_settings = reply == QtWidgets.QMessageBox.StandardButton.Yes

    table = window.tableWidget
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item is None:
            continue

        asset_path = path_from_table_item(item)
        variant_combo = cell_combo(table, row, 1)
        version_combo = cell_combo(table, row, 2)
        asset_type_combo = cell_combo(table, row, 3)
        if variant_combo is None or version_combo is None or asset_type_combo is None:
            continue
        variant_name = variant_combo.currentText()
        version_number = version_combo.currentText()
        asset_type = asset_type_combo.currentText()

        if asset_type == "Static Mesh":
            if is_asset_manager_asset_root(asset_path) or is_asset_manager_version_path(
                asset_path
            ):
                asset_root = asset_manager_asset_root(asset_path)
                base_path = (
                    normalize_disk_path(os.path.join(asset_root, "publish", "model")) + "/"
                )
                asset_name = os.path.basename(asset_root.rstrip("/\\"))
                identity = identity_from_base_path(
                    base_path,
                    asset_name,
                    variant_name,
                    version_number,
                )
                import_static_mesh_publish_pipeline(
                    identity,
                    warn=genUnrealUtils.warningPopup,
                    use_previous_version_settings=use_previous_version_settings,
                )
            else:
                import_setdec_static_mesh_pipeline(
                    asset_path,
                    variant_name,
                    version_number,
                    warn=genUnrealUtils.warningPopup,
                    use_previous_version_settings=use_previous_version_settings,
                )

        elif asset_type == "Skeletal Mesh":
            layout = window._row_publish_layout(row)
            imported_mesh, unreal_mesh_import_path = import_skeletal_mesh(
                asset_path,
                variant_name,
                version_number,
                layout=layout,
            )
            if imported_mesh is None:
                continue
            imported_textures = import_skeletal_textures(
                asset_path,
                variant_name,
                version_number,
                unreal_mesh_import_path,
                layout=layout,
            )
            assign_mesh_materials(
                imported_mesh,
                unreal_mesh_import_path,
                imported_textures,
                asset_type,
                warn=genUnrealUtils.warningPopup,
            )
