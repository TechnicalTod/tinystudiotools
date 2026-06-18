"""Maya scene API used by every check and export plugin.

This is the single place where ``maya.cmds`` / ``maya.mel`` / ``pymel`` are
imported. Plugins call ``MayaHost`` methods instead of importing Maya
themselves; that keeps the rest of the package importable from any context
(e.g. tests, batch tools) without dragging Maya into the import graph.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional


class MayaHost:
    """Concrete Maya scene API."""

    name = "maya"
    label = "Maya"

    # --------------------------------------------------------------- capture

    def capture_viewport_screenshot(self, dest: Path) -> bool:
        try:
            import maya.cmds as cmds
        except ImportError:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            cmds.playblast(
                completeFilename=str(dest),
                forceOverwrite=True,
                format="image",
                compression="png",
                quality=100,
                widthHeight=(512, 512),
                viewer=False,
                showOrnaments=True,
                offScreen=True,
            )
            return dest.is_file()
        except Exception:
            return False

    # ---------------------------------------------------------------- checks

    def selection_not_empty(self) -> bool:
        import maya.cmds as cmds

        return bool(cmds.ls(selection=True))

    def nodes_exist(self, names: List[str]) -> List[str]:
        import maya.cmds as cmds

        return [n for n in names if not cmds.objExists(n)]

    def selection_has_history(self) -> bool:
        import maya.cmds as cmds

        sel = cmds.ls(selection=True, long=True) or []
        for node in sel:
            shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.nodeType(shape) in ("mesh", "nurbsSurface"):
                    hist = cmds.listHistory(shape, pruneDagObjects=True) or []
                    if len(hist) > 1:
                        return True
        return False

    def node_exists(self, name: str) -> bool:
        import maya.cmds as cmds

        return bool(cmds.objExists(name))

    def list_assignable_materials(self) -> List[str]:
        """Return material nodes connected to any shading engine in the scene.

        Default materials shipped with Maya (``lambert1``, ``particleCloud1``,
        ``standardSurface1``) are filtered out — checks on naming convention
        should not flag scene defaults.
        """
        import maya.cmds as cmds

        defaults = {"lambert1", "particleCloud1", "standardSurface1"}
        materials: list[str] = []
        for sg in cmds.ls(type="shadingEngine") or []:
            shaders = cmds.listConnections(f"{sg}.surfaceShader") or []
            for shader in shaders:
                if shader in defaults or shader in materials:
                    continue
                materials.append(shader)
        return materials

    def attr_exists(self, node: str, attr: str) -> bool:
        import maya.cmds as cmds

        if not cmds.objExists(node):
            return False
        return bool(cmds.attributeQuery(attr, node=node, exists=True))

    def attr_string_value(self, node: str, attr: str) -> Optional[str]:
        import maya.cmds as cmds

        if not cmds.objExists(f"{node}.{attr}"):
            return None
        try:
            value = cmds.getAttr(f"{node}.{attr}")
        except Exception:
            return None
        return value if isinstance(value, str) else None

    def meshes_outside_group(self, group_name: str) -> List[str]:
        """Return mesh shape long paths that are not descendants of ``group_name``.

        If ``group_name`` does not exist, every mesh in the scene is returned
        so the caller can surface a useful message.
        """
        import maya.cmds as cmds

        meshes = cmds.ls(type="mesh", long=True, noIntermediate=True) or []
        if not meshes:
            return []
        if not cmds.objExists(group_name):
            return list(meshes)
        group_long = cmds.ls(group_name, long=True) or [f"|{group_name}"]
        accept = tuple(f"{p}|" for p in group_long) + (f"|{group_name}|",)
        return [m for m in meshes if not m.startswith(accept)]

    # ---------------------------------------------------------------- exports

    def save_scene_as(self, path: Path) -> None:
        import maya.cmds as cmds

        path.parent.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix.lower()
        file_type = "mayaBinary" if suffix == ".mb" else "mayaAscii"
        cmds.file(rename=str(path))
        cmds.file(save=True, type=file_type)

    def _collect_textures_from_materials(self, materials: set[str]) -> List[Path]:
        """Expand ``file`` nodes on ``materials`` into on-disk texture paths."""
        import maya.cmds as cmds

        seen: list[Path] = []
        seen_lookup: set[str] = set()
        if not materials:
            return seen

        for material in materials:
            history = cmds.listHistory(material, pruneDagObjects=True) or []
            file_nodes = [node for node in history if cmds.nodeType(node) == "file"]
            for file_node in set(file_nodes):
                texture_attr = f"{file_node}.fileTextureName"
                if not cmds.objExists(texture_attr):
                    continue
                texture_path = cmds.getAttr(texture_attr) or ""
                if not texture_path:
                    continue
                texture_path = texture_path.replace("\\", "/")
                directory, file_name = os.path.split(texture_path)
                if not os.path.isdir(directory):
                    continue

                stem = file_name.split(".<UDIM>")[0].split(".<udim>")[0]
                for candidate in os.listdir(directory):
                    if not candidate.startswith(stem.split(".")[0]):
                        continue
                    full = Path(directory) / candidate
                    key = str(full).lower()
                    if key in seen_lookup or not full.is_file():
                        continue
                    seen_lookup.add(key)
                    seen.append(full)
        return seen

    def collect_applied_textures(self) -> List[Path]:
        """Texture files referenced by file nodes connected to any material.

        Walks shading engines → materials → ``file`` nodes; expands UDIM tile
        siblings on disk so the bundle is complete. Returns deduplicated
        absolute paths; missing files are skipped.
        """
        return self._collect_textures_from_materials(set(self.list_assignable_materials()))

    def collect_textures_for_nodes(self, root_nodes: List[str]) -> List[Path]:
        """Textures referenced by materials assigned to meshes under ``root_nodes``."""
        import maya.cmds as cmds

        materials: set[str] = set()
        for root in root_nodes:
            if not cmds.objExists(root):
                continue
            meshes = cmds.listRelatives(
                root,
                allDescendents=True,
                fullPath=True,
                type="mesh",
                noIntermediate=True,
            ) or []
            root_shapes = cmds.listRelatives(
                root, shapes=True, fullPath=True, type="mesh", noIntermediate=True
            ) or []
            for mesh in set(meshes + root_shapes):
                for sg in cmds.listConnections(mesh, type="shadingEngine") or []:
                    for shader in cmds.listConnections(f"{sg}.surfaceShader") or []:
                        materials.add(shader)
        return self._collect_textures_from_materials(materials)

    def export_fbx_selection(self, path: Path) -> None:
        import maya.cmds as cmds
        import maya.mel as mel

        path.parent.mkdir(parents=True, exist_ok=True)
        sel = cmds.ls(selection=True)
        if not sel:
            raise RuntimeError("Nothing selected for FBX export.")
        cmds.select(sel, replace=True)
        mel.eval("FBXResetExport")
        mel.eval('FBXExport -f "{}" -s'.format(path.as_posix()))

    def export_fbx_rig(
        self,
        version_dir: Path,
        asset_name: str,
        export_nodes: Optional[List[str]] = None,
        version_label: Optional[str] = None,
    ) -> Path:
        import maya.cmds as cmds
        import maya.mel as mel

        export_nodes = list(export_nodes or ["root_joint", "visGeo"])
        missing = [n for n in export_nodes if not cmds.objExists(n)]
        if missing:
            raise RuntimeError(f"Missing rig export nodes: {', '.join(missing)}")

        version_name = version_label or version_dir.name
        fbx_base = version_dir / "UnrealExport"
        fbx_base.mkdir(parents=True, exist_ok=True)
        fbx_path = fbx_base / f"{asset_name}_ExportedRigForUnreal_{version_name}.fbx"

        temp_group = cmds.group(empty=True, name="_unrealExport_TEMP", world=True)
        duplicate_roots: list[str] = []
        try:
            for node in export_nodes:
                dup = cmds.duplicate(node, renameChildren=True, inputConnections=True)[0]
                cmds.parent(dup, temp_group)
                duplicate_roots.append(dup)

            dup_nodes: set[str] = set()
            for root in duplicate_roots:
                dup_nodes.add(root)
                dup_nodes.update(cmds.listRelatives(root, allDescendents=True) or [])

            for constraint in cmds.ls(type="constraint") or []:
                related = set(
                    cmds.listConnections(constraint, source=True, destination=True) or []
                )
                if related and related.issubset(dup_nodes):
                    cmds.delete(constraint)

            cmds.select(duplicate_roots, replace=True)
            mel.eval("FBXResetExport")
            mel.eval("FBXExportSmoothingGroups -v true")
            mel.eval('FBXExport -f "{}" -s'.format(fbx_path.as_posix()))
        finally:
            if cmds.objExists(temp_group):
                cmds.delete(temp_group)

        return fbx_path

    # ----------------------------------------------------------- scene I/O

    def open_scene(self, path: Path) -> None:
        """Open a published scene, replacing the current Maya file."""
        import maya.cmds as cmds

        if not path.is_file():
            raise RuntimeError(f"Scene not found: {path}")
        cmds.file(str(path), open=True, force=True, ignoreVersion=True)

    def reference_scene(self, path: Path, namespace: str) -> None:
        """Reference a published scene into the current Maya file."""
        import maya.cmds as cmds

        if not path.is_file():
            raise RuntimeError(f"Scene not found: {path}")
        cmds.file(
            str(path),
            reference=True,
            ignoreVersion=True,
            namespace=namespace,
        )

    def import_scene(self, path: Path) -> None:
        """Import a published scene directly into the current Maya file."""
        import maya.cmds as cmds

        if not path.is_file():
            raise RuntimeError(f"Scene not found: {path}")
        cmds.file(
            str(path),
            i=True,
            ignoreVersion=True,
            mergeNamespacesOnClash=True,
            namespace=":",
        )

    def is_scene_modified(self) -> bool:
        import maya.cmds as cmds

        try:
            return bool(cmds.file(query=True, modified=True))
        except Exception:
            return False

    @staticmethod
    def sanitize_namespace(name: str) -> str:
        """Return a Maya-safe namespace derived from an asset name."""
        import re

        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name.strip())
        if not cleaned:
            return "asset"
        if cleaned[0].isdigit():
            cleaned = f"a_{cleaned}"
        return cleaned

    # ---------------------------------------------------- static mesh publish

    def selected_mesh_transforms(self) -> List[str]:
        """Return long names of selected transforms that have a mesh shape."""
        import maya.cmds as cmds

        selected = cmds.ls(selection=True, long=True) or []
        meshes: list[str] = []
        for node in selected:
            shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
            if any(cmds.nodeType(shape) == "mesh" for shape in shapes):
                meshes.append(node)
        return meshes

    def selection_is_single_mesh_transform(self) -> bool:
        return len(self.selected_mesh_transforms()) == 1

    def selection_has_usd_preview_material(self) -> bool:
        import maya.cmds as cmds

        for transform in self.selected_mesh_transforms():
            shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
            for shape in shapes:
                shading_engines = cmds.listConnections(shape, type="shadingEngine") or []
                for shading_engine in shading_engines:
                    materials = (
                        cmds.listConnections(f"{shading_engine}.surfaceShader") or []
                    )
                    for material in materials:
                        if cmds.nodeType(material) == "usdPreviewSurface":
                            return True
        return False

    def selection_has_published_mesh(self) -> bool:
        import maya.cmds as cmds

        for transform in self.selected_mesh_transforms():
            if cmds.attributeQuery("published", node=transform, exists=True):
                try:
                    if bool(cmds.getAttr(f"{transform}.published")):
                        return True
                except Exception:
                    continue
        return False

    def publish_static_mesh_bundle(
        self,
        bundle_root: Path,
        *,
        file_stem: str,
        asset_name: str,
        variant_name: str,
        version_label: str,
        base_path: str,
        publish_layout: str = "asset_manager_model",
    ) -> List[str]:
        """Publish USD Preview static mesh bundle with undo safety."""
        from genTools import static_mesh_publish_ops as publish_ops

        transforms = self.selected_mesh_transforms()
        if len(transforms) != 1:
            raise RuntimeError("Select exactly one mesh transform to publish.")

        import pymel.core as pm

        mesh_object = pm.PyNode(transforms[0])
        return publish_ops.publish_static_mesh_bundle(
            mesh_object,
            bundle_root,
            file_stem=file_stem,
            asset_name=asset_name,
            variant_name=variant_name,
            version_label=version_label,
            base_path=base_path,
            usd_parent_scope=asset_name,
            publish_layout=publish_layout,
            replace_in_scene=True,
        )
