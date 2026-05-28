#!/usr/bin/env python
"""TinyStudio Workfile Publisher external launcher.

Used by standalone development (``python launcher.py --host standalone``).

Inside Maya the artist hits the *Workfiles* shelf button, which calls
:func:`workfile_publisher.ui.main_window.show_in_maya` directly; this script
is not used in that path.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make ``src/`` importable when launched from the repo directly.
_REPO_ROOT = Path(__file__).resolve().parent
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TinyStudio Workfile Publisher (external launcher)."
    )
    parser.add_argument(
        "--host",
        choices=("maya", "standalone"),
        default="standalone",
        help="Which host the publisher should target (default: standalone).",
    )
    parser.add_argument(
        "--show",
        default=None,
        help="Show name override (used by standalone when env is empty).",
    )
    parser.add_argument(
        "--base-show-dir",
        default=None,
        help="Show drive root (e.g. S:/). Standalone-only fallback.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    _setup_logging()
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.host == "maya":
        # Direct CLI launch inside Maya is not the supported flow; tell the
        # user how to actually open it.
        print(
            "Maya mode does not launch through this script. Use the Workfiles "
            "shelf button in Maya, or call "
            "workfile_publisher.ui.main_window.show_in_maya() from a Maya "
            "Python shell."
        )
        return 2

    from workfile_publisher.ui.main_window import show_standalone

    return show_standalone(
        host=args.host,
        cli_show=args.show,
        cli_base_show_dir=args.base_show_dir,
    )


if __name__ == "__main__":
    sys.exit(main())
