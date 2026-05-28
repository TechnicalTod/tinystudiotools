"""Studio context resolution from launcher-managed environment variables.

The launcher (``GenTools/TinyStudioLauncher``) bakes ``SHOW_NAME``,
``TINYSTUDIO_BASE_SHOW_DIR``, ``TINYSTUDIO_LIB_DIR`` and ``USERNAME`` into the
DCC process. The publisher uses these as the single source of truth - there is
no in-UI show picker.
"""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ContextError(RuntimeError):
    """Raised when the launcher-provided context is missing or invalid."""


@dataclass(frozen=True)
class StudioContext:
    """Resolved studio context for a publisher session.

    Attributes:
        show: Show folder name as it lives under ``base_show_dir`` (e.g.
            ``1000_TinyStudioTestShow``).
        base_show_dir: Root drive/dir containing all shows (e.g. ``S:/``).
        lib_dir: TinyStudio library root (e.g. ``L:/``).
        username: Current artist's username.
        show_root: Absolute path to ``base_show_dir/show``.
    """

    show: str
    base_show_dir: Path
    lib_dir: Path
    username: str

    @property
    def show_root(self) -> Path:
        return self.base_show_dir / self.show

    @property
    def assets_root(self) -> Path:
        return self.show_root / "assets"

    @property
    def episodes_root(self) -> Path:
        return self.show_root / "episodes"

    def describe(self) -> str:
        """Human-readable summary, suitable for window titles / status bars."""
        return (
            f"Show: {self.show} | Drive: {self.base_show_dir} | "
            f"User: {self.username}"
        )


def _env(name: str) -> str:
    value = os.environ.get(name, "")
    return value.strip()


def _normalize_base_and_show(base: str, show: str) -> tuple[Path, str, Path]:
    """Return ``(base_show_dir, show, show_root)`` with duplicate show segments folded.

    Some hosts mis-set ``TINYSTUDIO_BASE_SHOW_DIR`` to the show folder itself
    (e.g. ``S:/1000_TinyStudioTestShow``) while ``SHOW_NAME`` is the same string,
    which would otherwise build ``S:/Show/Show``.
    """
    show = show.strip().strip("/\\")
    base_path = Path(base.replace("\\", "/"))

    # Base already points at the show folder.
    if base_path.name == show and base_path.exists():
        return base_path.parent, show, base_path

    show_root = base_path / show
    if show_root.exists():
        return base_path, show, show_root

    # Base path ends with the show segment but is not a valid show_root alone.
    base_str = str(base_path).replace("\\", "/").rstrip("/")
    suffix = "/" + show
    if base_str.endswith(suffix) or base_str.endswith(show):
        trimmed = base_str[: -len(show)].rstrip("/\\")
        if trimmed:
            candidate = Path(trimmed) / show
            if candidate.exists():
                return Path(trimmed), show, candidate

    return base_path, show, show_root


def resolve_context(
    cli_show: Optional[str] = None,
    cli_base_show_dir: Optional[str] = None,
    allow_cli_override: bool = False,
    *,
    prefer_cli: bool = False,
) -> StudioContext:
    """Build a :class:`StudioContext` from environment variables.

    The launcher is the single source of truth. CLI overrides are only honoured
    when ``allow_cli_override`` is ``True``; the environment value still wins
    if both are set, matching the plan's "env wins" guarantee.

    Args:
        cli_show: Optional ``--show`` flag value (forwarded by JSX from AE,
            or supplied by the developer in standalone mode).
        cli_base_show_dir: Optional ``--base-show-dir`` flag value (standalone
            override only).
        allow_cli_override: When ``True`` (AE / standalone hosts), use CLI
            values as a fallback if the env var is empty.
        prefer_cli: When ``True`` (AE spawn from JSX), trust ``--show`` and
            ``--base-show-dir`` over inherited env. Detached ``cmd /c start``
            children often do not receive the DCC environment.

    Returns:
        A validated :class:`StudioContext`.

    Raises:
        ContextError: If required values cannot be resolved or the show folder
            doesn't exist on disk.
    """
    env_show = _env("SHOW_NAME")
    env_base = _env("TINYSTUDIO_BASE_SHOW_DIR")

    if prefer_cli and allow_cli_override:
        show = (cli_show or env_show or "").strip()
        base = (cli_base_show_dir or env_base or "").strip()
    else:
        show = env_show
        if not show and allow_cli_override and cli_show:
            show = cli_show.strip()
        base = env_base
        if not base and allow_cli_override and cli_base_show_dir:
            base = cli_base_show_dir.strip()

    if not show:
        raise ContextError(
            "SHOW_NAME is not set. Launch the DCC through TinyStudioLauncher "
            "so the show is baked into the environment, then reopen the "
            "Workfile Publisher."
        )

    if not base:
        raise ContextError(
            "TINYSTUDIO_BASE_SHOW_DIR is not set. Relaunch through "
            "TinyStudioLauncher."
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
        lib_dir=Path(lib),
        username=user,
    )
