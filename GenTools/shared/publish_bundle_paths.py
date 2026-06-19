"""Layout-aware disk and Unreal paths for static-mesh publish bundles.

Dependency-light: no pymel, maya, or unreal imports. Used by Maya Asset
Manager, Set Dec publish, Unreal import, and scene-description IO.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

try:
    from studioShowPaths import normalize_disk_path
except ImportError:
    _DRIVE_RELATIVE = re.compile(r"^([A-Za-z]):([^/\\])")

    def normalize_disk_path(path: str) -> str:
        if not path:
            return path
        path = path.replace("\\", "/")
        match = _DRIVE_RELATIVE.match(path)
        if match:
            path = "{0}:/{1}".format(match.group(1), path[2:])
        return path

LayoutKind = Literal["setdec", "asset_manager_model"]

_ASSET_MANAGER_MODEL_MARKER = "/publish/model/"
_SETDEC_MARKER = "/assets/setdec/"
_UE_ASSET_ROOT = "/Game/01_Assets"
_CATEGORY_NAMES = frozenset({"chr", "prop", "env", "veh"})


@dataclass(frozen=True)
class StaticMeshPublishIdentity:
    """One published static-mesh bundle on disk or in UE."""

    layout: LayoutKind
    base_path: str  # trailing slash
    asset_name: str
    variant: str
    version: str
    category: Optional[str] = None
    publish_type: Optional[str] = None
    bundle_stem: Optional[str] = None  # file basename without extension


@dataclass(frozen=True)
class BundlePaths:
    """Resolved paths for one publish bundle."""

    bundle_root: str
    fbx_dir: str
    usd_dir: str
    maya_dir: str
    tex_dir: str
    fbx_file: str
    usd_file: str
    maya_file: str
    ue_import_dir: str
    ue_mesh_object_path: str
    bundle_stem: str


def _normalize(path: str) -> str:
    return normalize_disk_path(path).rstrip("/")


def _with_trailing_slash(path: str) -> str:
    normalized = _normalize(path)
    return f"{normalized}/"


def detect_layout(base_path: str) -> LayoutKind:
    lowered = base_path.replace("\\", "/").lower()
    if _ASSET_MANAGER_MODEL_MARKER in lowered:
        return "asset_manager_model"
    if _SETDEC_MARKER in lowered:
        return "setdec"
    raise ValueError(f"Cannot detect publish layout from basePath: {base_path!r}")


def _parse_category_from_asset_manager_base(base_path: str) -> Optional[str]:
    """Extract chr/prop/env/veh from ``…/assets/{category}/{asset}/publish/model/``."""
    parts = [p for p in base_path.replace("\\", "/").split("/") if p]
    for idx, part in enumerate(parts):
        if part.lower() in _CATEGORY_NAMES and idx + 2 < len(parts):
            if parts[idx + 2].lower() == "publish" and idx + 3 < len(parts):
                if parts[idx + 3].lower() == "model":
                    return part.lower()
    return None


def _bundle_stem_for_identity(identity: StaticMeshPublishIdentity) -> str:
    if identity.bundle_stem:
        return identity.bundle_stem
    if identity.layout == "setdec":
        return f"{identity.asset_name}_{identity.version}"
    publish_type = identity.publish_type or "model"
    return f"{identity.asset_name}_{publish_type}_{identity.variant}_{identity.version}"


def bundle_paths(identity: StaticMeshPublishIdentity) -> BundlePaths:
    """Resolve on-disk bundle folders/files and UE import destinations."""
    base = _with_trailing_slash(identity.base_path)
    stem = _bundle_stem_for_identity(identity)

    if identity.layout == "setdec":
        bundle_root = (
            f"{base}{identity.asset_name}/{identity.variant}/{identity.version}/"
        )
        group_name = base.rstrip("/").split("/")[-1]
        ue_import_dir = (
            f"{_UE_ASSET_ROOT}/SETDEC/{group_name}/{identity.asset_name}/"
            f"{identity.variant}/{identity.version}"
        )
    else:
        bundle_root = f"{base}{stem}/"
        category = (identity.category or _parse_category_from_asset_manager_base(base) or "prop").upper()
        ue_import_dir = (
            f"{_UE_ASSET_ROOT}/{category}/{identity.asset_name}/"
            f"{identity.variant}/{identity.version}"
        )

    fbx_dir = f"{bundle_root}fbx/"
    usd_dir = f"{bundle_root}usd/"
    maya_dir = f"{bundle_root}maya/"
    tex_dir = f"{bundle_root}tex/"
    fbx_file = f"{fbx_dir}{stem}.fbx"
    usd_file = f"{usd_dir}{stem}.usda"
    maya_file = f"{maya_dir}{stem}.ma"
    ue_mesh_object_path = f"{ue_import_dir}/{stem}"

    return BundlePaths(
        bundle_root=bundle_root,
        fbx_dir=fbx_dir,
        usd_dir=usd_dir,
        maya_dir=maya_dir,
        tex_dir=tex_dir,
        fbx_file=fbx_file,
        usd_file=usd_file,
        maya_file=maya_file,
        ue_import_dir=ue_import_dir,
        ue_mesh_object_path=ue_mesh_object_path,
        bundle_stem=stem,
    )


def sm_prefixed_mesh_object_path(identity: StaticMeshPublishIdentity) -> str:
    """UE object path after static mesh import renames the asset to ``SM_{stem}``."""
    paths = bundle_paths(identity)
    return f"{paths.ue_import_dir}/SM_{paths.bundle_stem}"


def identity_from_legacy_setdec_args(
    asset_path: str,
    variant: str,
    version: str,
) -> StaticMeshPublishIdentity:
    """Build identity from Set Dec disk path ``{group_root}/{asset_name}``."""
    normalized = _normalize(asset_path)
    parts = normalized.split("/")
    asset_name = parts[-1]
    base_path = _with_trailing_slash("/".join(parts[:-1]))
    return StaticMeshPublishIdentity(
        layout="setdec",
        base_path=base_path,
        asset_name=asset_name,
        variant=variant,
        version=version,
    )


def identity_from_base_path(
    base_path: str,
    asset_name: str,
    variant: str,
    version: str,
    *,
    publish_type: str = "model",
) -> StaticMeshPublishIdentity:
    """Build identity from Maya ``basePath`` + asset metadata attrs."""
    layout = detect_layout(base_path)
    category = None
    if layout == "asset_manager_model":
        category = _parse_category_from_asset_manager_base(base_path)
    return StaticMeshPublishIdentity(
        layout=layout,
        base_path=_with_trailing_slash(base_path),
        asset_name=asset_name,
        variant=variant,
        version=version,
        category=category,
        publish_type=publish_type if layout == "asset_manager_model" else None,
    )


def parse_version_folder_name(folder_name: str) -> Optional[tuple[str, str, str, str]]:
    """Parse ``{asset}_model_{variant}_v###`` → (asset, model, variant, version)."""
    match = re.match(
        r"^(?P<asset>.+)_(?P<publish_type>model)_(?P<variant>[a-z0-9][a-z0-9_-]*)_v(?P<version>\d+)$",
        folder_name,
        re.IGNORECASE,
    )
    if not match:
        return None
    version_num = int(match.group("version"))
    version_label = f"v{version_num:03d}"
    return (
        match.group("asset"),
        match.group("publish_type").lower(),
        match.group("variant").lower(),
        version_label,
    )


def parse_ue_setdec_static_mesh_object_path(ue_path: str) -> Optional[StaticMeshPublishIdentity]:
    """Parse ``/Game/01_Assets/SETDEC/{group}/{asset}/{variant}/{version}/…``."""
    path = ue_path.split(".")[0].replace("\\", "/")
    marker = "/setdec/"
    idx = path.lower().find(marker)
    if idx == -1:
        return None
    parts = [part for part in path[idx + len(marker) :].split("/") if part]
    if len(parts) < 5:
        return None
    group_name, asset_name, variant, version, mesh_name = parts[:5]
    expected = f"{asset_name}_{version}"
    if mesh_name != expected:
        return None
    show_base = _show_setdec_group_base_path(group_name)
    if show_base is None:
        return None
    return StaticMeshPublishIdentity(
        layout="setdec",
        base_path=show_base,
        asset_name=asset_name,
        variant=variant,
        version=version,
    )


def parse_ue_asset_manager_static_mesh_object_path(
    ue_path: str,
) -> Optional[StaticMeshPublishIdentity]:
    """Parse ``/Game/01_Assets/{CATEGORY}/{asset}/{variant}/{version}/{stem}``."""
    path = ue_path.split(".")[0].replace("\\", "/")
    prefix = f"{_UE_ASSET_ROOT}/"
    if not path.startswith(prefix):
        return None
    parts = [part for part in path[len(prefix) :].split("/") if part]
    if len(parts) < 5:
        return None
    category, asset_name, variant, version, mesh_name = parts[:5]
    if category.lower() in ("setdec",):
        return None
    show_base = _show_asset_manager_model_base_path(category.lower(), asset_name)
    if show_base is None:
        return None
    return StaticMeshPublishIdentity(
        layout="asset_manager_model",
        base_path=show_base,
        asset_name=asset_name,
        variant=variant,
        version=version,
        category=category.lower(),
        publish_type="model",
        bundle_stem=mesh_name,
    )


def parse_ue_static_mesh_object_path(ue_path: str) -> Optional[StaticMeshPublishIdentity]:
    parsed = parse_ue_setdec_static_mesh_object_path(ue_path)
    if parsed is not None:
        return parsed
    return parse_ue_asset_manager_static_mesh_object_path(ue_path)


def ue_publish_prefix(base_path: str) -> str:
    """Map a show-drive ``basePath`` to the UE folder before variant/version."""
    base = _with_trailing_slash(base_path)
    layout = detect_layout(base_path)
    if layout == "setdec":
        marker = "/assets/setdec/"
        idx = base.lower().find(marker)
        suffix = base[idx + len(marker) :] if idx != -1 else ""
        return f"{_UE_ASSET_ROOT}/SETDEC/{suffix}"
    category = (_parse_category_from_asset_manager_base(base) or "prop").upper()
    parts = [part for part in base.rstrip("/").split("/") if part]
    asset_name = parts[parts.index("assets") + 2]
    return f"{_UE_ASSET_ROOT}/{category}/{asset_name}/"


def complete_path(
    base_path: str,
    variant: str,
    version: str,
    asset_name: str,
    ext: str,
    *,
    publish_type: str = "model",
) -> str:
    """Build disk or UE path to one published bundle artifact."""
    identity = identity_from_base_path(
        base_path,
        asset_name,
        variant,
        version,
        publish_type=publish_type,
    )
    paths = bundle_paths(identity)
    if ext == "ue":
        if identity.layout == "asset_manager_model":
            return paths.ue_mesh_object_path
        prefix = ue_publish_prefix(base_path).rstrip("/")
        return f"{prefix}/{asset_name}/{variant}/{version}/{asset_name}_{version}"
    if ext == "maya":
        return paths.maya_file
    if ext == "usd":
        return paths.usd_file
    if ext == "fbx":
        return paths.fbx_file
    raise ValueError(f"Unsupported extension {ext!r}")


def disk_asset_folder(base_path: str, asset_name: str) -> str:
    """Legacy Set Dec helper — group folder + asset short name."""
    return f"{_normalize(base_path)}/{asset_name}"


def _show_setdec_group_base_path(group_name: str) -> Optional[str]:
    import os

    show = os.environ.get("SHOW_NAME", "").strip()
    base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR", "").strip()
    if not show or not base:
        return None
    try:
        from studioShowPaths import setdec_group_folder

        return setdec_group_folder(show, group_name, trailing_slash=True)
    except Exception:
        show_root = f"{base.replace(chr(92), '/').rstrip('/')}/{show}"
        return f"{show_root}/assets/setdec/{group_name}/"


def _show_asset_manager_model_base_path(category: str, asset_name: str) -> Optional[str]:
    import os

    show = os.environ.get("SHOW_NAME", "").strip()
    base = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR", "").strip()
    if not show or not base:
        return None
    show_root = base.replace("\\", "/").rstrip("/")
    if not show_root.endswith(show):
        show_root = f"{show_root}/{show}"
    return f"{show_root}/assets/{category}/{asset_name}/publish/model/"
