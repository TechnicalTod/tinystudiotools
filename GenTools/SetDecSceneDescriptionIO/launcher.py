#!/usr/bin/env python
"""SetDec Scene Description IO external launcher.

Used for standalone development (``python launcher.py``). Inside a DCC the
tool is opened through the shelf / menu shim, which calls
``setdec_scene_description_io.ui.main_window.show(host=...)``; this script is
not used in those paths.
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


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TinyStudio SetDec Scene Description IO (external launcher)."
    )
    parser.add_argument(
        "--host",
        choices=("maya", "unreal", "standalone"),
        default="standalone",
        help="Which host to target (default: standalone).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.host != "standalone":
        print(
            f"{args.host} mode does not launch through this script. Use the "
            f"shelf / menu button inside {args.host}."
        )
        return 2

    from setdec_scene_description_io.ui.main_window import show_standalone

    return show_standalone()


if __name__ == "__main__":
    sys.exit(main())
