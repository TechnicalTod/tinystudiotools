"""High-level publish/open orchestration.

The service stitches together :mod:`path_schema`, :mod:`versioning` and an
arbitrary :class:`~workfile_publisher.adapters.base.HostAdapter`. It is the
only module the UI talks to for save/open actions; this keeps the UI free of
DCC- and disk-layout details.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from . import path_schema as ps
from .context import StudioContext
from .versioning import (
    VersionReservationError,
    WorkfileEntry,
    list_workfiles,
    reserve_next_version,
)


@dataclass(frozen=True)
class WorkfileTarget:
    """Everything the service needs to compute a workfile path.

    ``kind`` is ``"asset"`` or ``"shot"``. For assets, ``category`` and
    ``asset`` must be set. For shots, ``episode``, ``sequence`` and ``shot``
    must be set.
    """

    kind: str
    dcc: str
    task: str
    variant: str
    # Asset-only:
    category: Optional[str] = None
    asset: Optional[str] = None
    # Shot-only:
    episode: Optional[str] = None
    sequence: Optional[str] = None
    shot: Optional[str] = None

    def prefix(self) -> str:
        """Filename prefix (asset name for assets, shot name for shots)."""
        if self.kind == "asset":
            if not self.asset:
                raise ValueError("Asset workfile target requires 'asset'.")
            return self.asset
        if self.kind == "shot":
            if not self.shot:
                raise ValueError("Shot workfile target requires 'shot'.")
            return self.shot
        raise ValueError(f"Unknown target kind {self.kind!r}")


class PublishService:
    """High-level operations the UI calls."""

    def __init__(self, context: StudioContext, schema: ps.PathSchema):
        self.context = context
        self.schema = schema

    # -- path helpers ------------------------------------------------------
    def workfile_dir(self, target: WorkfileTarget) -> Path:
        if target.kind == "asset":
            if not (target.category and target.asset):
                raise ValueError("Asset target requires category and asset.")
            return ps.asset_workfile_dir(
                self.context, target.category, target.asset, target.dcc, target.task
            )
        if target.kind == "shot":
            if not (target.episode and target.sequence and target.shot):
                raise ValueError("Shot target requires episode, sequence and shot.")
            return ps.shot_workfile_dir(
                self.context,
                target.episode,
                target.sequence,
                target.shot,
                target.dcc,
                target.task,
            )
        raise ValueError(f"Unknown target kind {target.kind!r}")

    # -- listing -----------------------------------------------------------
    def list_for_target(
        self,
        target: WorkfileTarget,
        *,
        include_all_variants: bool = True,
    ) -> List[WorkfileEntry]:
        """Return existing workfiles for the given context/task.

        Args:
            target: Workfile target. Only ``kind``, ``dcc``, ``task`` and the
                context fields are required (``variant`` is ignored when
                ``include_all_variants`` is True).
            include_all_variants: When True, return every variant so the UI
                table can group/group-by; when False, restrict to the
                ``target.variant`` value.
        """
        dcc_spec = self.schema.get_dcc(target.dcc)
        folder = self.workfile_dir(target)
        variant = None if include_all_variants else target.variant
        return list_workfiles(
            folder,
            prefix=target.prefix(),
            task=target.task,
            ext=dcc_spec.extension,
            variant=variant,
        )

    # -- write / read actions ---------------------------------------------
    def publish(self, host_adapter, target: WorkfileTarget) -> Path:
        """Reserve the next version and ask the adapter to save into it.

        Args:
            host_adapter: Anything implementing
                :class:`workfile_publisher.adapters.base.HostAdapter`.
            target: Where this workfile belongs.

        Returns:
            The final path on disk after the adapter has written it.
        """
        dcc_spec = self.schema.get_dcc(target.dcc)
        if not dcc_spec.supports(target.kind):
            raise ValueError(
                f"DCC {target.dcc!r} does not support {target.kind!r} workfiles."
            )

        folder = self.workfile_dir(target)
        try:
            reserved = reserve_next_version(
                folder,
                prefix=target.prefix(),
                task=target.task,
                variant=target.variant,
                ext=dcc_spec.extension,
                padding=self.schema.version_padding,
            )
        except VersionReservationError:
            raise

        try:
            host_adapter.save_as(reserved)
        except Exception:
            # The placeholder we created is now useless if the save failed.
            # Best-effort clean-up so we don't burn version numbers.
            try:
                if reserved.exists() and reserved.stat().st_size == 0:
                    reserved.unlink()
            except OSError:
                pass
            raise

        return reserved

    def open_workfile(self, host_adapter, path: Path) -> None:
        """Ask the host adapter to open an existing workfile."""
        if not path.exists():
            raise FileNotFoundError(f"Workfile does not exist: {path}")
        host_adapter.open(path)
