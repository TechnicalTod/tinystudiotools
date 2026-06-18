"""Export a rig puppet as an Unreal-ready skeletal mesh FBX plus local textures.

Shelf/menu entry point for manual exports outside the Asset Manager publish flow.
Uses the same MayaHost helpers as the ``fbx_rig`` publish step.

Standalone use (any saved workfile):
  1. Put the rig in **bind / build pose** (Advanced Skeleton: *Go to Build Pose*).
  2. Ensure export nodes exist (defaults ``root_joint`` + ``visGeo``, or set via puppet attrs).
  3. Save the scene, then run ``main()`` or use the Rigging shelf button.

Each export creates the next version folder under ``publish/rig/unreal/``
(``v001``, ``v002``, …) independent of the workfile version.

The exporter builds a clean skeleton at the scene root from the live joint world
transforms, duplicates vis geo to the scene root, binds skin, copies textures into
``tex/``, repaths file nodes for FBX export, then deletes the temporary export
nodes and restores the live texture paths. The live rig is never modified.

Output is written under the asset publish tree::

    .../assets/<category>/<asset>/publish/rig/unreal/<version>/
        <asset>_ExportedRigForUnreal_<version>.fbx
        tex/
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import NamedTuple, Optional

import maya.cmds as mc
import maya.mel as mel
import pymel.core as pm

from assetManager.host import MayaHost

_DEFAULT_EXPORT_NODES = ["root_joint", "visGeo"]
_RIG_VERSION_RE = re.compile(
    r"^(?P<asset>.+)_rig_(?P<variant>[a-z0-9][a-z0-9_-]*)_v(?P<version>\d+)$",
    re.IGNORECASE,
)
_UNREAL_VERSION_DIR_RE = re.compile(r"^v(?P<version>\d+)$", re.IGNORECASE)


class ExportContext(NamedTuple):
    output_dir: Path
    asset_name: str
    version_label: str
    export_nodes: list[str]


def _parse_rig_version_name(name: str) -> Optional[tuple[str, str, str]]:
    """Parse ``{asset}_rig_{variant}_v###`` → (asset, variant, version_label)."""
    match = _RIG_VERSION_RE.match(name)
    if not match:
        return None
    version_label = f"v{int(match.group('version')):03d}"
    return match.group("asset"), match.group("variant").lower(), version_label


def _find_puppet_metadata_node() -> Optional[pm.PyNode]:
    puppets = [
        node
        for node in pm.ls(type="transform")
        if node.hasAttr("rootJointName")
    ]
    if not puppets:
        return None
    if len(puppets) > 1:
        print(
            "Multiple puppet metadata nodes found; using "
            f"{puppets[0].name()!r}."
        )
    return puppets[0]


def _attr_string(node: pm.PyNode, attr: str, default: str = "") -> str:
    if not node.hasAttr(attr):
        return default
    value = node.attr(attr).get()
    return value if isinstance(value, str) and value else default


def resolve_export_nodes() -> list[str]:
    puppet = _find_puppet_metadata_node()
    if puppet is None:
        return list(_DEFAULT_EXPORT_NODES)
    return [
        _attr_string(puppet, "rootJointName", _DEFAULT_EXPORT_NODES[0]),
        _attr_string(puppet, "visGeoGroupName", _DEFAULT_EXPORT_NODES[1]),
    ]


def _asset_root_from_workfile(scene_path: Path) -> Path:
    """Return ``.../assets/<category>/<asset>`` from a workfile path."""
    current = scene_path.parent
    while current != current.parent:
        if (current / "work").is_dir():
            return current
        current = current.parent
    raise RuntimeError(
        "Could not find asset root from the saved scene path. "
        "Save under .../assets/<category>/<asset>/work/maya/<task>/."
    )


def _unreal_publish_root(asset_root: Path) -> Path:
    return asset_root / "publish" / "rig" / "unreal"


def _next_unreal_version_label(unreal_root: Path) -> str:
    """Return the next ``v###`` label under ``publish/rig/unreal/``."""
    highest = 0
    if unreal_root.is_dir():
        for child in unreal_root.iterdir():
            if not child.is_dir():
                continue
            match = _UNREAL_VERSION_DIR_RE.match(child.name)
            if match:
                highest = max(highest, int(match.group("version")))
    return f"v{highest + 1:03d}"


def _resolve_asset_name(scene_path: Path, asset_root: Path) -> str:
    puppet = _find_puppet_metadata_node()
    if puppet is not None:
        asset_name = _attr_string(puppet, "assetName")
        if asset_name:
            return asset_name

    parsed = _parse_rig_version_name(scene_path.stem)
    if parsed:
        return parsed[0]

    return asset_root.name


def resolve_export_context(*, reserve: bool = False) -> ExportContext:
    scene_path = Path(mc.file(query=True, sceneName=True))
    if not scene_path.name:
        raise RuntimeError("Save the scene before exporting.")

    asset_root = _asset_root_from_workfile(scene_path)
    asset_name = _resolve_asset_name(scene_path, asset_root)
    export_nodes = resolve_export_nodes()
    unreal_root = _unreal_publish_root(asset_root)
    version_label = _next_unreal_version_label(unreal_root)
    output_dir = unreal_root / version_label
    if reserve:
        output_dir.mkdir(parents=True, exist_ok=True)

    return ExportContext(output_dir, asset_name, version_label, export_nodes)


def preflight() -> bool:
    """Print what the exporter would use; return True when export can proceed."""
    try:
        ctx = resolve_export_context(reserve=False)
    except RuntimeError as exc:
        print(f"[preflight] {exc}")
        return False

    host = MayaHost()
    missing = host.nodes_exist(ctx.export_nodes)
    puppet = _find_puppet_metadata_node()

    print("[preflight] Export puppet for Skeletal Mesh")
    print(f"  scene:        {mc.file(query=True, sceneName=True)}")
    print(f"  publish root: {ctx.output_dir.parent}")
    print(f"  next version: {ctx.version_label}")
    print(f"  output dir:   {ctx.output_dir}")
    print(f"  asset name:   {ctx.asset_name}")
    print(f"  export nodes: {ctx.export_nodes}")
    print(f"  metadata on:  {puppet.name() if puppet else '(none — using defaults)'}")
    print("  tip:          set bind/build pose before export (AS: Go to Build Pose)")
    if missing:
        print(f"  MISSING:      {', '.join(missing)}")
        return False
    print("  status:       ready")
    return True


def _joint_hierarchy(skeleton_root: str) -> list[str]:
    if not mc.objExists(skeleton_root):
        return []
    root = (mc.ls(skeleton_root, long=True) or [skeleton_root])[0]
    joints = mc.listRelatives(
        root, allDescendents=True, type="joint", fullPath=True
    ) or []
    if mc.nodeType(root) == "joint":
        joints.append(root)
    return sorted(dict.fromkeys(joints), key=_dag_depth)


def _dag_depth(node: str) -> int:
    return len([part for part in node.split("|") if part])


def _skin_cluster(mesh_transform: str) -> Optional[str]:
    shapes = mc.listRelatives(mesh_transform, shapes=True, path=True) or []
    for shape in shapes:
        history = mc.listHistory(shape, pruneDagObjects=True) or []
        skins = mc.ls(history, type="skinCluster") or []
        if skins:
            return skins[0]
    return None


def _mesh_transforms(root: str) -> list[str]:
    transforms: list[str] = []
    root_long = (mc.ls(root, long=True) or [root])[0]
    candidates = [root_long] + (
        mc.listRelatives(root_long, allDescendents=True, type="transform", fullPath=True)
        or []
    )
    for transform in candidates:
        shapes = mc.listRelatives(
            transform, shapes=True, path=True, type="mesh", noIntermediate=True
        ) or []
        if shapes:
            transforms.append(transform)
    return sorted(dict.fromkeys(transforms))


def _mesh_shapes(root: str) -> list[str]:
    shapes = mc.listRelatives(root, shapes=True, path=True, type="mesh") or []
    shapes.extend(
        mc.listRelatives(
            root, allDescendents=True, shapes=True, path=True, type="mesh", noIntermediate=True
        ) or []
    )
    return list(dict.fromkeys(shapes))


def _try_go_to_build_pose() -> None:
    if not mc.pluginInfo("AdvancedSkeleton", query=True, loaded=True):
        return
    for setup in ("bodySetup", "asSelectorbiped"):
        if mc.objExists(setup):
            try:
                mel.eval(f'asGoToBuildPose "{setup}";')
                print(f"Advanced Skeleton build pose applied via {setup!r}.")
                return
            except Exception:
                continue


def _clear_skin_clusters(mesh_transform: str) -> None:
    for shape in _mesh_shapes(mesh_transform):
        history = mc.listHistory(shape, pruneDagObjects=True) or []
        for node in mc.ls(history, type="skinCluster") or []:
            mc.delete(node)


def _pair_duplicate_meshes(source_geo: str, duplicate_geo: str) -> list[tuple[str, str]]:
    source_meshes = _mesh_transforms(source_geo)
    duplicate_meshes = _mesh_transforms(duplicate_geo)
    if len(source_meshes) != len(duplicate_meshes):
        raise RuntimeError(
            "Mesh count mismatch while preparing export: "
            f"{len(source_meshes)} source mesh(es), {len(duplicate_meshes)} duplicate mesh(es)."
        )
    return list(zip(source_meshes, duplicate_meshes))


def _create_export_skin_cluster(
    mesh: str,
    joints: list[str],
    max_influences: int,
) -> str:
    mesh_long = _long_name(mesh)
    joint_longs = [_long_name(j) for j in joints]
    shapes = mc.listRelatives(
        mesh_long, shapes=True, path=True, type="mesh", noIntermediate=True
    ) or []
    if not shapes:
        raise RuntimeError(
            f"Cannot skin export mesh {_short_name(mesh_long)!r}: no mesh shape found."
        )

    mc.select(joint_longs + [mesh_long], replace=True)
    try:
        result = mc.skinCluster(
            tsb=True,
            maximumInfluences=max_influences,
            obeyMaxInfluences=True,
            normalizeWeights=1,
        )
    finally:
        mc.select(clear=True)

    if not result:
        raise RuntimeError(
            f"Cannot skin export mesh {_short_name(mesh_long)!r}: skinCluster failed."
        )
    return result[0]


def _bind_and_copy_skin_weights(
    source_geo: str,
    duplicate_geo: str,
    export_joints: list[str],
) -> None:
    copied = 0
    skipped: list[str] = []
    for source_mesh, duplicate_mesh in _pair_duplicate_meshes(source_geo, duplicate_geo):
        source_mesh = _long_name(source_mesh)
        duplicate_mesh = _long_name(duplicate_mesh)
        source_skin = _skin_cluster(source_mesh)
        if not source_skin:
            skipped.append(_short_name(source_mesh))
            continue

        _clear_skin_clusters(duplicate_mesh)
        max_influences = mc.skinCluster(
            source_skin, query=True, maximumInfluences=True
        )
        duplicate_skin = _create_export_skin_cluster(
            duplicate_mesh,
            export_joints,
            max_influences,
        )
        mc.copySkinWeights(
            sourceSkin=source_skin,
            destinationSkin=duplicate_skin,
            surfaceAssociation="closestPoint",
            influenceAssociation=["closestJoint", "oneToOne", "name"],
            normalize=True,
            noMirror=True,
        )
        copied += 1

    print(f"Copied skin weights for {copied} mesh(es).")
    if skipped:
        raise RuntimeError(
            "Cannot export puppet with unskinned mesh(es): " + ", ".join(skipped[:8])
        )


def _assert_export_joint_names(source_joints: list[str], export_joints: list[str]) -> None:
    mismatches = [
        (_short_name(source), _short_name(export))
        for source, export in zip(source_joints, export_joints)
        if _short_name(source) != _short_name(export)
    ]
    if mismatches:
        details = ", ".join(
            f"{source}->{export}" for source, export in mismatches[:8]
        )
        raise RuntimeError(f"Export joint names changed: {details}")


def _short_name(node: str) -> str:
    return node.split("|")[-1].split(":")[-1]


def _long_name(node: str) -> str:
    """Resolve a node reference to a unique full DAG path."""
    if node.startswith("|"):
        if mc.objExists(node):
            return node
        raise RuntimeError(f"Node not found: {node!r}")

    matches = mc.ls(node, long=True) or []
    if not matches:
        raise RuntimeError(f"Node not found: {node!r}")
    if len(matches) > 1:
        preview = ", ".join(matches[:4])
        suffix = " ..." if len(matches) > 4 else ""
        raise RuntimeError(
            f"Ambiguous node name {node!r}: {len(matches)} matches ({preview}{suffix})."
        )
    return matches[0]


def _absolute_dag_path(node: str) -> str:
    return _long_name(node)


def _show_export_hierarchy(*roots: str) -> None:
    shown: set[str] = set()
    for root in roots:
        root_long = _long_name(root)
        nodes = [root_long] + (
            mc.listRelatives(root_long, allDescendents=True, fullPath=True) or []
        )
        for node in nodes:
            if node in shown:
                continue
            if mc.objExists(f"{node}.visibility"):
                mc.setAttr(f"{node}.visibility", 1)
            shown.add(node)


def _finalize_export_name(node: str, desired: str) -> str:
    """Rename an export node to match the source; fail if Maya cannot apply the exact name."""
    node_long = _long_name(node)
    if _short_name(node_long) == desired:
        return node_long

    try:
        renamed = mc.rename(node_long, desired)
    except RuntimeError as exc:
        raise RuntimeError(
            f"Cannot rename export node {_short_name(node_long)!r} to {desired!r}."
        ) from exc

    if _short_name(renamed) != desired:
        raise RuntimeError(
            f"Export node rename failed: expected {desired!r}, got {_short_name(renamed)!r}."
        )
    return _long_name(renamed)


def _duplicate_to_world(source: str) -> str:
    """Duplicate a rig branch and parent it directly under the scene root."""
    source_path = _absolute_dag_path(source)
    duplicate = mc.duplicate(source_path, renameChildren=True, inputConnections=False)[0]
    duplicate = _long_name(mc.parent(duplicate, world=True)[0])
    _snap_transform_from_source(source_path, duplicate)
    return _finalize_export_name(duplicate, _short_name(source))


def _delete_export_nodes(nodes: list[str]) -> None:
    for node in dict.fromkeys(nodes):
        try:
            node_long = _long_name(node)
        except RuntimeError:
            continue
        if mc.objExists(node_long):
            mc.delete(node_long)


def _copy_numeric_attr(source: str, dest: str, attr: str) -> None:
    src_plug = f"{source}.{attr}"
    dest_plug = f"{dest}.{attr}"
    if not mc.objExists(src_plug) or not mc.objExists(dest_plug):
        return
    try:
        value = mc.getAttr(src_plug)
        if isinstance(value, list):
            value = value[0]
        mc.setAttr(dest_plug, value)
    except RuntimeError:
        pass


def _build_clean_export_skeleton(source_root: str) -> tuple[str, list[str]]:
    """Create a fresh joint hierarchy from evaluated source joint world matrices."""
    source_joints = _joint_hierarchy(source_root)
    if not source_joints:
        raise RuntimeError(f"No joints found under {source_root!r}.")

    mc.refresh(force=True)
    source_matrices = {
        joint: mc.xform(joint, query=True, matrix=True, worldSpace=True)
        for joint in source_joints
    }
    source_parents = {
        joint: (mc.listRelatives(joint, parent=True, fullPath=True) or [None])[0]
        for joint in source_joints
    }

    source_set = set(source_joints)
    joint_map: dict[str, str] = {}
    export_joints: list[str] = []
    for source_joint in source_joints:
        parent = source_parents[source_joint]
        if parent in source_set:
            export_joint = mc.createNode(
                "joint",
                name=_short_name(source_joint),
                parent=joint_map[parent],
            )
            export_joint = _long_name(export_joint)
        else:
            export_joint = mc.createNode("joint", name=_short_name(source_joint))

        export_joint = _long_name(export_joint)
        _unlock_transform_attrs(export_joint)
        _copy_numeric_attr(source_joint, export_joint, "radius")
        _copy_numeric_attr(source_joint, export_joint, "rotateOrder")
        _copy_numeric_attr(source_joint, export_joint, "segmentScaleCompensate")

        mc.xform(export_joint, matrix=source_matrices[source_joint], worldSpace=True)
        joint_map[source_joint] = export_joint
        export_joints.append(export_joint)

    _print_pose_snap_check(list(zip(source_joints, export_joints))[:5])
    return export_joints[0], export_joints


def _snap_transform_from_source(source: str, duplicate: str) -> None:
    matrix = mc.xform(source, query=True, matrix=True, worldSpace=True)
    _unlock_transform_attrs(duplicate)
    mc.xform(duplicate, matrix=matrix, worldSpace=True)


def _pair_joints(source_joints: list[str], duplicate_joints: list[str]) -> list[tuple[str, str]]:
    dup_by_short = {_short_name(joint): joint for joint in duplicate_joints}
    pairs: list[tuple[str, str]] = []
    missing: list[str] = []
    for source_joint in source_joints:
        short = _short_name(source_joint)
        duplicate_joint = dup_by_short.get(f"{short}1") or dup_by_short.get(short)
        if duplicate_joint is None:
            missing.append(short)
            continue
        pairs.append((source_joint, duplicate_joint))

    if missing:
        raise RuntimeError(
            "Could not match duplicate joints for: "
            + ", ".join(missing[:8])
            + (" ..." if len(missing) > 8 else "")
        )
    return pairs


def _unlock_transform_attrs(node: str) -> None:
    for attr in (
        "translateX", "translateY", "translateZ",
        "rotateX", "rotateY", "rotateZ",
        "scaleX", "scaleY", "scaleZ",
        "jointOrientX", "jointOrientY", "jointOrientZ",
    ):
        plug = f"{node}.{attr}"
        if not mc.objExists(plug):
            continue
        try:
            mc.setAttr(plug, lock=False, keyable=True)
        except RuntimeError:
            pass


def _snap_joint_poses(source_root: str, duplicate_root: str) -> None:
    """Copy evaluated world matrices from the driven source skeleton to the duplicate."""
    mc.refresh(force=True)

    if mc.nodeType(source_root) != "joint":
        _snap_transform_from_source(source_root, duplicate_root)

    source_joints = _joint_hierarchy(source_root)
    duplicate_joints = _joint_hierarchy(duplicate_root)
    if not source_joints:
        return

    pairs = _pair_joints(source_joints, duplicate_joints)
    matrices = [
        (duplicate_joint, mc.xform(source_joint, query=True, matrix=True, worldSpace=True))
        for source_joint, duplicate_joint in pairs
    ]
    for duplicate_joint, matrix in matrices:
        _unlock_transform_attrs(duplicate_joint)
        mc.xform(duplicate_joint, matrix=matrix, worldSpace=True)

    _print_pose_snap_check(pairs[:5])


def _print_pose_snap_check(pairs: list[tuple[str, str]]) -> None:
    if not pairs:
        print("Pose snap check: no joints found.")
        return

    print("Pose snap check:")
    for source_joint, duplicate_joint in pairs:
        src_pos = mc.xform(source_joint, query=True, translation=True, worldSpace=True)
        dup_pos = mc.xform(duplicate_joint, query=True, translation=True, worldSpace=True)
        delta = sum(abs(src_pos[i] - dup_pos[i]) for i in range(3))
        print(
            "  {} -> {} | src={} dup={} delta={:.6f}".format(
                _short_name(source_joint),
                _short_name(duplicate_joint),
                [round(v, 4) for v in src_pos],
                [round(v, 4) for v in dup_pos],
                delta,
            )
        )


def _strip_joint_drivers(joints: list[str]) -> None:
    """Remove any stray drivers on duplicate joints (should be none without input connections)."""
    joint_set = set(joints)
    for constraint in mc.ls(type="constraint") or []:
        related = set(mc.listConnections(constraint, source=True, destination=True) or [])
        if related & joint_set:
            mc.delete(constraint)

    transform_attrs = (
        "translate", "translateX", "translateY", "translateZ",
        "rotate", "rotateX", "rotateY", "rotateZ",
        "scale", "scaleX", "scaleY", "scaleZ",
    )
    for joint in joints:
        for attr in transform_attrs:
            plug = f"{joint}.{attr}"
            if not mc.objExists(plug):
                continue
            for src in mc.listConnections(plug, source=True, destination=False, plugs=True) or []:
                try:
                    mc.disconnectAttr(src, plug)
                except RuntimeError:
                    pass


def _duplicate_for_export(export_nodes: list[str]) -> list[str]:
    """Build a clean root skeleton, duplicate vis geo to world, copy skin weights."""
    if len(export_nodes) < 2:
        raise RuntimeError("Expected skeleton root and geometry root export nodes.")

    skeleton_root, geometry_root = export_nodes[0], export_nodes[1]
    source_geometry = _absolute_dag_path(geometry_root)
    source_skeleton = _absolute_dag_path(skeleton_root)
    source_joints = _joint_hierarchy(source_skeleton)

    created: list[str] = []
    try:
        dup_geometry = _duplicate_to_world(source_geometry)
        created.append(dup_geometry)

        export_skeleton, export_joints = _build_clean_export_skeleton(source_skeleton)
        created.append(export_skeleton)
        if len(source_joints) != len(export_joints):
            raise RuntimeError(
                "Export skeleton joint count mismatch: "
                f"{len(source_joints)} source vs {len(export_joints)} export."
            )

        export_joints = [
            _finalize_export_name(export_joint, _short_name(source_joint))
            for source_joint, export_joint in zip(source_joints, export_joints)
        ]
        export_skeleton = export_joints[0]
        _assert_export_joint_names(source_joints, export_joints)

        _bind_and_copy_skin_weights(source_geometry, dup_geometry, export_joints)

        return [export_skeleton, dup_geometry]
    except Exception:
        _delete_export_nodes(created)
        raise


def _export_fbx_rig(ctx: ExportContext) -> Path:
    """Export rig FBX from a temporary duplicate so the live rig is untouched."""
    export_nodes = ctx.export_nodes
    missing = [n for n in export_nodes if not mc.objExists(n)]
    if missing:
        raise RuntimeError(f"Missing rig export nodes: {', '.join(missing)}")

    ctx.output_dir.mkdir(parents=True, exist_ok=True)
    fbx_path = (
        ctx.output_dir
        / f"{ctx.asset_name}_ExportedRigForUnreal_{ctx.version_label}.fbx"
    )

    export_roots = _duplicate_for_export(export_nodes)
    texture_dir = ctx.output_dir / "tex"
    restore_texture_paths: list[tuple[str, str]] = []
    try:
        restore_texture_paths = _copy_textures_and_repath(export_roots, texture_dir)
        _show_export_hierarchy(*export_roots)
        mc.select([_long_name(node) for node in export_roots], replace=True)
        mel.eval("FBXResetExport")
        mel.eval("FBXExportSmoothingGroups -v true")
        mel.eval('FBXExport -f "{}" -s'.format(fbx_path.as_posix()))
    finally:
        _restore_texture_paths(restore_texture_paths)
        _delete_export_nodes(export_roots)

    return fbx_path


_TEXTURE_NODE_PATH_ATTRS: dict[str, str] = {
    "file": "fileTextureName",
    "aiImage": "filename",
}


def _materials_for_roots(root_nodes: list[str]) -> set[str]:
    materials: set[str] = set()
    for root in root_nodes:
        if not mc.objExists(root):
            continue
        root_long = _long_name(root)
        meshes = mc.listRelatives(
            root_long,
            allDescendents=True,
            fullPath=True,
            type="mesh",
            noIntermediate=True,
        ) or []
        root_shapes = mc.listRelatives(
            root_long, shapes=True, fullPath=True, type="mesh", noIntermediate=True
        ) or []
        for mesh in set(meshes + root_shapes):
            for sg in mc.listConnections(mesh, type="shadingEngine") or []:
                for plug in ("surfaceShader", "displacementShader", "volumeShader"):
                    for shader in mc.listConnections(f"{sg}.{plug}") or []:
                        materials.add(shader)
    return materials


def _get_texture_path(texture_node: str) -> str:
    attr_name = _TEXTURE_NODE_PATH_ATTRS.get(mc.nodeType(texture_node))
    if not attr_name:
        return ""
    attr = f"{texture_node}.{attr_name}"
    if not mc.objExists(attr):
        return ""
    return (mc.getAttr(attr) or "").replace("\\", "/")


def _set_texture_path(texture_node: str, path: str) -> None:
    attr_name = _TEXTURE_NODE_PATH_ATTRS.get(mc.nodeType(texture_node))
    if not attr_name:
        return
    attr = f"{texture_node}.{attr_name}"
    if mc.objExists(attr):
        mc.setAttr(attr, path.replace("\\", "/"), type="string")


def _texture_nodes_for_materials(materials: set[str]) -> list[str]:
    """All texture nodes upstream of export materials (includes bump/normal chains)."""
    texture_nodes: set[str] = set()
    for material in materials:
        history = mc.listHistory(material, pruneDagObjects=True) or []
        for node in history:
            if mc.nodeType(node) in _TEXTURE_NODE_PATH_ATTRS:
                texture_nodes.add(node)
    return sorted(texture_nodes)


def _expand_texture_files(texture_path: str) -> list[Path]:
    texture_path = texture_path.replace("\\", "/")
    if not texture_path:
        return []

    literal = Path(texture_path)
    if literal.is_file() and "<UDIM>" not in texture_path and "<udim>" not in texture_path:
        return [literal]

    if "/" not in texture_path:
        return [literal] if literal.is_file() else []

    directory, file_name = texture_path.rsplit("/", 1)
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return [literal] if literal.is_file() else []

    stem = file_name.split(".<UDIM>")[0].split(".<udim>")[0]
    prefix = stem.split(".")[0]
    matches = [
        candidate
        for candidate in dir_path.iterdir()
        if candidate.is_file() and candidate.name.startswith(prefix)
    ]
    if matches:
        return matches
    return [literal] if literal.is_file() else []


def _texture_files_for_materials(materials: set[str]) -> list[Path]:
    seen: list[Path] = []
    seen_lookup: set[str] = set()
    for texture_node in _texture_nodes_for_materials(materials):
        for path in _expand_texture_files(_get_texture_path(texture_node)):
            key = str(path.resolve()).lower()
            if key in seen_lookup or not path.is_file():
                continue
            seen_lookup.add(key)
            seen.append(path)
    return seen


def _collect_textures_for_nodes(root_nodes: list[str]) -> list[Path]:
    """Gather on-disk textures for materials assigned under ``root_nodes``."""
    return _texture_files_for_materials(_materials_for_roots(root_nodes))


def _copy_textures_to_dir(textures: list[Path], texture_dir: Path) -> list[Path]:
    texture_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in textures:
        dest = texture_dir / src.name
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        copied.append(dest)
    return copied


def _repath_texture_nodes_to_dir(
    texture_nodes: list[str],
    texture_dir: Path,
) -> list[tuple[str, str]]:
    """Point texture nodes at ``texture_dir``; return ``(node, original_path)`` pairs."""
    restore: list[tuple[str, str]] = []
    texture_dir = texture_dir.resolve()
    for texture_node in texture_nodes:
        original = _get_texture_path(texture_node)
        if not original:
            continue

        file_name = Path(original).name
        dest = texture_dir / file_name
        if not dest.is_file():
            for src in _expand_texture_files(original):
                if src.is_file():
                    shutil.copy2(src, texture_dir / src.name)
            if not dest.is_file():
                stem = file_name.split(".<UDIM>")[0].split(".<udim>")[0].split(".")[0]
                if not any(path.name.startswith(stem) for path in texture_dir.iterdir()):
                    print(
                        f"Warning: skipping repath for {texture_node!r}; "
                        f"texture {file_name!r} not found in {texture_dir}."
                    )
                    continue

        restore.append((texture_node, original))
        _set_texture_path(texture_node, str(dest).replace("\\", "/"))
    return restore


def _restore_texture_paths(restore: list[tuple[str, str]]) -> None:
    for texture_node, original in restore:
        _set_texture_path(texture_node, original)


def _copy_textures_and_repath(
    export_roots: list[str],
    texture_dir: Path,
) -> list[tuple[str, str]]:
    """Copy textures for export roots into ``texture_dir`` and repath their texture nodes."""
    materials = _materials_for_roots(export_roots)
    texture_nodes = _texture_nodes_for_materials(materials)
    textures = _texture_files_for_materials(materials)
    _copy_textures_to_dir(textures, texture_dir)
    return _repath_texture_nodes_to_dir(texture_nodes, texture_dir)


def export_rig_for_unreal(ctx: ExportContext) -> Path:
    return _export_fbx_rig(ctx)


def export_textures_for_unreal(ctx: ExportContext) -> list[Path]:
    texture_dir = ctx.output_dir / "tex"
    if not texture_dir.is_dir():
        return []
    return sorted(path for path in texture_dir.iterdir() if path.is_file())


def main() -> None:
    if not preflight():
        return

    ctx = resolve_export_context(reserve=True)
    print(
        "\nExporting rig from a pose-snapped duplicate — live controls and joints are not modified."
    )
    print(f"Publishing to {ctx.output_dir} ...")
    fbx_path = export_rig_for_unreal(ctx)
    print(f"FBX written to {fbx_path}")

    copied = export_textures_for_unreal(ctx)
    if copied:
        print(f"Textures copied/repathed to {ctx.output_dir / 'tex'} ({len(copied)} file(s))")
    else:
        print(f"No textures found for {ctx.export_nodes[1]!r}.")
