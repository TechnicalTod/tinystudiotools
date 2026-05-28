"""
Per-show configuration loaded from the show's network folder.

Default path: {TINYSTUDIO_BASE_SHOW_DIR}{show_name}/config/show_config.json

Pins application versions so artists cannot launch a DCC build that does not
match how the show's files were authored.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .log_setup import get_module_logger

logger = get_module_logger(__name__)

DEFAULT_SHOW_CONFIG_RELATIVE = "config/show_config.json"
DEFAULT_BASE_SHOW_DIR = "S:/"
SUPPORTED_SCHEMA_VERSION = 1


class ShowVersionMismatchError(ValueError):
    """Raised when the requested app version does not match the show config."""

    def __init__(self, show: str, app_name: str, requested: str, required: str):
        self.show = show
        self.app_name = app_name
        self.requested = requested
        self.required = required
        super().__init__(
            f"Show '{show}' requires {app_name} {required}, but {requested} was selected. "
            f"Update {show}/config/show_config.json or choose the correct show."
        )


@dataclass(frozen=True)
class ShowConfig:
    """Parsed show_config.json for one show."""

    show_id: str
    display_name: str
    application_versions: Dict[str, str]
    config_path: Path
    raw: Dict

    def required_version(self, app_name: str) -> Optional[str]:
        """Pinned version for an app, or None if this show does not pin that app."""
        return self.application_versions.get(app_name.lower())

    def validate_version(self, app_name: str, version: str, show: str) -> None:
        """Raise ShowVersionMismatchError if the version is not allowed for this show."""
        required = self.required_version(app_name)
        if required is None:
            return
        if str(version).strip() != str(required).strip():
            raise ShowVersionMismatchError(show, app_name, version, required)


def resolve_show_config_path(
    show_name: str,
    base_show_dir: str = DEFAULT_BASE_SHOW_DIR,
    config_relative: str = DEFAULT_SHOW_CONFIG_RELATIVE,
) -> Path:
    base = Path(base_show_dir.rstrip("/\\"))
    return base / show_name / config_relative


def load_show_config(
    show_name: str,
    base_show_dir: str = DEFAULT_BASE_SHOW_DIR,
) -> Optional[ShowConfig]:
    """
    Load show_config.json for a show.

    Returns None if the file does not exist (show has no version pins).
    """
    config_path = resolve_show_config_path(show_name, base_show_dir)
    if not config_path.is_file():
        logger.debug("No show config at %s", config_path)
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", config_path, e)
        raise ValueError(f"Invalid show config JSON: {config_path}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Show config must be a JSON object: {config_path}")

    schema_version = data.get("schema_version", 1)
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        logger.warning(
            "Show config %s has schema_version %s (expected %s)",
            config_path,
            schema_version,
            SUPPORTED_SCHEMA_VERSION,
        )

    app_versions = _parse_application_versions(data)
    show_id = str(data.get("show_id") or show_name)
    display_name = str(data.get("display_name") or show_id)

    logger.info(
        "Loaded show config for %s (%d application pin(s)) from %s",
        show_id,
        len(app_versions),
        config_path,
    )

    return ShowConfig(
        show_id=show_id,
        display_name=display_name,
        application_versions=app_versions,
        config_path=config_path,
        raw=data,
    )


def _parse_application_versions(data: Dict) -> Dict[str, str]:
    """
    Accept either:
      "application_versions": { "maya": "2026", "unreal": "5.6" }
    or legacy array form for future growth:
      "applications": [ { "app": "maya", "version": "2026" }, ... ]
    """
    versions: Dict[str, str] = {}

    block = data.get("application_versions")
    if isinstance(block, dict):
        for app, ver in block.items():
            if app and ver is not None:
                versions[str(app).lower()] = str(ver).strip()

    apps_array = data.get("applications")
    if isinstance(apps_array, list):
        for entry in apps_array:
            if not isinstance(entry, dict):
                continue
            app = entry.get("app") or entry.get("name")
            ver = entry.get("version")
            if app and ver is not None:
                versions[str(app).lower()] = str(ver).strip()

    return versions
