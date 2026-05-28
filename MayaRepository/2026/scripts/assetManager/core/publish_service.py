"""Publish orchestration."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import List, Optional

from ..exporters.base import ExportError, run_exports
from ..host import MayaHost
from .context import StudioContext
from .paths import preview_filename, publish_dir_for_target
from .schema import AssetPublishSchema
from .target import AssetPublishTarget
from .versioning import (
    PublishEntry,
    VersionReservationError,
    list_publish_versions,
    reserve_version_dir,
)


class PublishService:
    def __init__(self, context: StudioContext, schema: AssetPublishSchema) -> None:
        self._context = context
        self._schema = schema

    def publish_dir(self, target: AssetPublishTarget) -> Path:
        return publish_dir_for_target(self._context, target)

    def list_versions(
        self,
        target: AssetPublishTarget,
        *,
        include_all_variants: bool = True,
    ) -> List[PublishEntry]:
        folder = self.publish_dir(target)
        variant = None if include_all_variants else target.variant
        return list_publish_versions(
            folder,
            target.asset,
            target.publish_type,
            variant=variant,
            padding=self._schema.version_padding,
        )

    def next_version_for_target(self, target: AssetPublishTarget) -> int:
        from .versioning import next_version

        folder = self.publish_dir(target)
        return next_version(
            folder,
            target.asset,
            target.publish_type,
            target.variant,
            padding=self._schema.version_padding,
        )

    def publish(
        self,
        host: MayaHost,
        target: AssetPublishTarget,
        screenshot_path: Optional[Path] = None,
    ) -> Path:
        folder = self.publish_dir(target)
        try:
            version_dir = reserve_version_dir(
                folder,
                target.asset,
                target.publish_type,
                target.variant,
                padding=self._schema.version_padding,
            )
        except VersionReservationError:
            raise

        match = re.search(r"_v(\d+)$", version_dir.name)
        version = int(match.group(1)) if match else 1

        try:
            artifacts = run_exports(host, self._schema, target, version_dir, version)
            if screenshot_path and screenshot_path.is_file():
                preview = version_dir / preview_filename(
                    target.asset,
                    target.publish_type,
                    target.variant,
                    version,
                    padding=self._schema.version_padding,
                )
                shutil.copy2(screenshot_path, preview)
                artifacts.append(preview.name)

            manifest = version_dir / "manifest.json"
            if manifest.is_file():
                data = json.loads(manifest.read_text(encoding="utf-8"))
            else:
                data = {}
            data.update(
                {
                    "asset": target.asset,
                    "category": target.category,
                    "publish_type": target.publish_type,
                    "variant": target.variant,
                    "version": version,
                    "artifacts": artifacts,
                }
            )
            manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            if version_dir.exists() and not any(version_dir.iterdir()):
                version_dir.rmdir()
            elif version_dir.exists():
                shutil.rmtree(version_dir, ignore_errors=True)
            raise

        return version_dir
