"""
One-time setup for new TinyStudio shows on the studio show drive.

Creates the folder skeleton that matches an empty show layout (same top-level
tree as S:/1000_TinyStudioTestShow, without production asset/shot content),
and writes config/show_config.json using the same schema as the test show.

Usage:
    Edit SHOW_NUMBER / SHOW_NAME below, then run:
        python createNewShow.py

    Or pass arguments:
        python createNewShow.py --show-id 1001_MyNewShow
        python createNewShow.py --number 1001 --name MyNewShow --base-dir S:/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- Edit these before a one-off run (CLI flags override) ---
SHOW_NUMBER = "1001"
SHOW_NAME = "MyNewShow"
SHOW_DISPLAY_NAME = ""  # Leave empty to auto-derive from SHOW_NAME (e.g. "My New Show")
BASE_SHOW_DIR = r"S:/"

SHOW_CONFIG_RELATIVE = "config/show_config.json"

# Default DCC pins — matches S:/1000_TinyStudioTestShow/config/show_config.json
DEFAULT_APPLICATION_VERSIONS: dict[str, str] = {
    "maya": "2026",
    "unreal": "5.6",
    "ae": "2024",
}

# Relative paths under {base}/{show_id}/ — matches 1000_TinyStudioTestShow skeleton.
SHOW_FOLDER_TEMPLATE: tuple[str, ...] = (
    "assets/chr",
    "assets/env",
    "assets/prop",
    "assets/setdec",
    "assets/veh",
    "bidding",
    "config",
    "editorial/sequences",
    "episodes",
    "io",
    "prod/pulls",
    "prod/recordings",
)


def build_show_id(number: str, name: str) -> str:
    """Return folder name like ``1000_TinyStudioTestShow``."""
    number = number.strip()
    name = name.strip().strip("_")
    if not number or not name:
        raise ValueError("SHOW_NUMBER and SHOW_NAME must both be non-empty")
    return f"{number}_{name}"


def build_display_name(name: str) -> str:
    """Turn a show suffix like ``TinyStudioTestShow`` into ``Tiny Studio Test Show``."""
    part = name.strip().strip("_")
    if not part:
        return part
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", part)
    return spaced.replace("_", " ").strip()


def build_show_config(
    show_id: str,
    display_name: str,
    application_versions: dict[str, str] | None = None,
) -> dict:
    """Build show_config.json payload matching the test show schema."""
    return {
        "schema_version": 1,
        "show_id": show_id,
        "display_name": display_name,
        "application_versions": dict(application_versions or DEFAULT_APPLICATION_VERSIONS),
    }


def write_show_config(
    show_root: Path,
    show_id: str,
    display_name: str,
    *,
    dry_run: bool = False,
) -> Path:
    """Write config/show_config.json under the show root."""
    config_path = show_root / SHOW_CONFIG_RELATIVE
    payload = build_show_config(show_id, display_name)

    if dry_run:
        return config_path

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return config_path


def create_show_folders(
    show_id: str,
    base_show_dir: str | Path,
    *,
    dry_run: bool = False,
) -> list[Path]:
    """
    Create the show root and template subfolders.

    Returns the list of directories created (or that would be created if dry_run).
    """
    base = Path(str(base_show_dir).replace("\\", "/").rstrip("/"))
    show_root = base / show_id

    if show_root.exists():
        raise FileExistsError(f"Show folder already exists: {show_root}")

    created: list[Path] = []
    roots = [show_root, *(show_root / rel for rel in SHOW_FOLDER_TEMPLATE)]

    for folder in roots:
        if dry_run:
            created.append(folder)
            continue
        folder.mkdir(parents=True, exist_ok=False)
        created.append(folder)

    return created


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new TinyStudio show folder tree on the show drive.",
    )
    parser.add_argument(
        "--show-id",
        help="Full show folder name (e.g. 1001_MyNewShow). Overrides --number/--name.",
    )
    parser.add_argument(
        "--number",
        default=SHOW_NUMBER,
        help=f"Show number prefix (default: {SHOW_NUMBER})",
    )
    parser.add_argument(
        "--name",
        default=SHOW_NAME,
        help=f"Show name suffix after number_ (default: {SHOW_NAME})",
    )
    parser.add_argument(
        "--base-dir",
        default=BASE_SHOW_DIR,
        help=f"Drive root containing show folders (default: {BASE_SHOW_DIR})",
    )
    parser.add_argument(
        "--display-name",
        default=SHOW_DISPLAY_NAME,
        help="Human-readable show title for show_config.json (default: derived from --name)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print folders that would be created without writing to disk",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    show_id = args.show_id.strip() if args.show_id else build_show_id(args.number, args.name)
    name_suffix = show_id.split("_", 1)[-1] if "_" in show_id else show_id
    display_name = (args.display_name or "").strip() or build_display_name(
        args.name if not args.show_id else name_suffix
    )
    base_dir = args.base_dir

    show_root = Path(str(base_dir).replace("\\", "/").rstrip("/")) / show_id

    try:
        created = create_show_folders(show_id, base_dir, dry_run=args.dry_run)
        config_path = write_show_config(
            show_root,
            show_id,
            display_name,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(exc, file=sys.stderr)
        return 1
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to create show: {exc}", file=sys.stderr)
        return 1

    action = "Would create" if args.dry_run else "Created"
    print(f"{action} show: {show_id}")
    print(f"  Root: {show_root}")
    print(f"  Display name: {display_name}")
    print(f"  Config: {config_path}")
    if args.dry_run:
        print("  Config JSON:")
        print(json.dumps(build_show_config(show_id, display_name), indent=2))
    print(f"  Folders ({len(created)}):")
    for path in created:
        print(f"    {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
