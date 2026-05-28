"""Publish path builders."""

from __future__ import annotations

from pathlib import Path

from .context import StudioContext
from .target import AssetPublishTarget


def asset_publish_root(
    ctx: StudioContext,
    category: str,
    asset: str,
    publish_type: str,
) -> Path:
    """``S:/<show>/assets/<category>/<asset>/publish/<publish_type>/``"""
    return ctx.assets_root / category / asset / "publish" / publish_type


def version_dir_name(
    asset: str,
    publish_type: str,
    variant: str,
    version: int,
    *,
    padding: int = 3,
) -> str:
    return f"{asset}_{publish_type}_{variant}_v{version:0{padding}d}"


def preview_filename(
    asset: str,
    publish_type: str,
    variant: str,
    version: int,
    *,
    padding: int = 3,
) -> str:
    return f"{asset}_{publish_type}_{variant}_v{version:0{padding}d}_preview.png"


def scene_filename(
    asset: str,
    publish_type: str,
    variant: str,
    version: int,
    *,
    padding: int = 3,
    extension: str = ".ma",
) -> str:
    return f"{asset}_{publish_type}_{variant}_v{version:0{padding}d}{extension}"


def scene_path_for_version(
    version_dir: Path,
    asset: str,
    publish_type: str,
    variant: str,
    version: int,
    *,
    padding: int = 3,
) -> Path | None:
    """Return the published Maya scene for a version folder, if present."""
    for ext in (".ma", ".mb"):
        expected = version_dir / scene_filename(
            asset,
            publish_type,
            variant,
            version,
            padding=padding,
            extension=ext,
        )
        if expected.is_file():
            return expected
    if not version_dir.is_dir():
        return None
    for child in version_dir.iterdir():
        if child.is_file() and child.suffix.lower() in (".ma", ".mb"):
            if "_preview" not in child.stem.lower():
                return child
    return None


def publish_dir_for_target(ctx: StudioContext, target: AssetPublishTarget) -> Path:
    return asset_publish_root(
        ctx, target.category, target.asset, target.publish_type
    )


def preview_path_for_version(
    version_dir: Path,
    asset: str,
    publish_type: str,
    variant: str,
    version: int,
    *,
    padding: int = 3,
) -> Path | None:
    """Return the preview image for a publish version folder, if present."""
    expected = version_dir / preview_filename(
        asset, publish_type, variant, version, padding=padding
    )
    if expected.is_file():
        return expected
    if not version_dir.is_dir():
        return None
    for child in version_dir.iterdir():
        if child.is_file() and child.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
            if "_preview" in child.stem.lower() or child.name.lower().startswith("preview"):
                return child
    return None
