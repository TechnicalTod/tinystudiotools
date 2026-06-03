"""
Per-artist Unreal .uproject paths keyed by show.

Stored at: L:/Artist/{username}/TinyStudioSettings/unreal_projects.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from .log_setup import get_module_logger

logger = get_module_logger(__name__)

ARTIST_ROOT = "L:/Artist"
SETTINGS_DIR_NAME = "TinyStudioSettings"
SETTINGS_FILENAME = "unreal_projects.json"
SCHEMA_VERSION = 1


def get_settings_path(username: str) -> Path:
    """Path to unreal_projects.json for the given Windows username."""
    base = Path(ARTIST_ROOT.rstrip("/\\"))
    return base / username / SETTINGS_DIR_NAME / SETTINGS_FILENAME


def _normalize_uproject_path(path: str) -> str:
    return str(Path(path).resolve()).replace("\\", "/")


def _is_valid_uproject_path(path: str) -> bool:
    return bool(path) and path.lower().endswith(".uproject")


def load_store(username: str) -> Dict:
    """Load the full settings document, or an empty scaffold if missing."""
    settings_path = get_settings_path(username)
    if not settings_path.is_file():
        return {"schema_version": SCHEMA_VERSION, "projects_by_show": {}}

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", settings_path, e)
        raise ValueError(f"Invalid unreal projects JSON: {settings_path}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Unreal projects settings must be a JSON object: {settings_path}")

    if "projects_by_show" not in data or not isinstance(data["projects_by_show"], dict):
        data["projects_by_show"] = {}

    data.setdefault("schema_version", SCHEMA_VERSION)
    return data


def load_projects(username: str) -> Dict[str, str]:
    """Return show name -> .uproject path mapping."""
    data = load_store(username)
    projects = data.get("projects_by_show", {})
    if not isinstance(projects, dict):
        return {}
    return {str(k): str(v) for k, v in projects.items() if k and v}


def save_project(username: str, show: str, uproject_path: str) -> Path:
    """
    Persist a show -> .uproject mapping. Creates TinyStudioSettings if needed.

    Returns:
        Path to the written settings file.

    Raises:
        ValueError: invalid show or uproject path.
        OSError: cannot create directory or write file.
    """
    show = str(show).strip()
    if not show:
        raise ValueError("Show name is required to save an Unreal project mapping.")

    normalized = _normalize_uproject_path(uproject_path)
    if not _is_valid_uproject_path(normalized):
        raise ValueError(f"Not a valid .uproject file: {uproject_path}")

    settings_path = get_settings_path(username)
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_store(username)
    data["schema_version"] = SCHEMA_VERSION
    data["projects_by_show"][show] = normalized

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    logger.info("Saved Unreal project for show '%s' -> %s", show, normalized)
    return settings_path


def get_project_path(username: str, show: str) -> Optional[Path]:
    """
    Look up the saved .uproject for a show.

    Returns None if no mapping exists. Does not verify the file exists on disk.
    """
    show = str(show).strip()
    if not show:
        return None

    projects = load_projects(username)
    raw = projects.get(show)
    if not raw:
        return None

    if not _is_valid_uproject_path(raw):
        logger.warning("Invalid stored uproject for show %s: %s", show, raw)
        return None

    return Path(raw)
