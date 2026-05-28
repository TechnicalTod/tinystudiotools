"""Studio context from TinyStudioLauncher environment variables."""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass
from pathlib import Path


class ContextError(RuntimeError):
    """Raised when the launcher-provided context is missing or invalid."""


@dataclass(frozen=True)
class StudioContext:
    """Resolved studio context for a Playblast Manager session."""

    show: str
    base_show_dir: Path
    lib_dir: Path
    username: str

    @property
    def show_root(self) -> Path:
        return self.base_show_dir / self.show


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _normalize_base_and_show(base: str, show: str) -> tuple[Path, str, Path]:
    show = show.strip().strip("/\\")
    base_path = Path(base.replace("\\", "/"))

    if base_path.name == show and base_path.exists():
        return base_path.parent, show, base_path

    show_root = base_path / show
    if show_root.exists():
        return base_path, show, show_root

    base_str = str(base_path).replace("\\", "/").rstrip("/")
    suffix = "/" + show
    if base_str.endswith(suffix) or base_str.endswith(show):
        trimmed = base_str[: -len(show)].rstrip("/\\")
        if trimmed:
            candidate = Path(trimmed) / show
            if candidate.exists():
                return Path(trimmed), show, candidate

    return base_path, show, show_root


def resolve_context() -> StudioContext:
    """Build context from launcher env vars."""
    show = _env("SHOW_NAME")
    base = _env("TINYSTUDIO_BASE_SHOW_DIR")

    if not show:
        raise ContextError(
            "SHOW_NAME is not set. Launch Maya through TinyStudioLauncher, "
            "then reopen Playblast Manager."
        )
    if not base:
        raise ContextError(
            "TINYSTUDIO_BASE_SHOW_DIR is not set. Relaunch through TinyStudioLauncher."
        )

    lib = _env("TINYSTUDIO_LIB_DIR") or "L:/"
    user = _env("USERNAME") or getpass.getuser()

    base_show_dir, show, show_root = _normalize_base_and_show(base, show)
    if not show_root.exists():
        raise ContextError(
            f"Show folder does not exist: {show_root}\n"
            "Check that SHOW_NAME matches a folder on the show drive."
        )

    return StudioContext(
        show=show,
        base_show_dir=base_show_dir,
        lib_dir=Path(lib.replace("\\", "/")),
        username=user,
    )
