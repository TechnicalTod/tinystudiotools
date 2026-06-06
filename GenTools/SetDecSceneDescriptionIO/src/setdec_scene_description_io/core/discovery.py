"""Show-drive discovery for environment scene descriptions."""

from __future__ import annotations

from .context import StudioContext
from .paths import ScenePaths, SceneSchema


class EnvDiscovery:
    """List environments and variants from the on-disk layout."""

    def __init__(self, context: StudioContext, schema: SceneSchema) -> None:
        self._context = context
        self._schema = schema
        self._paths = ScenePaths(str(context.base_show_dir), schema)

    @property
    def context(self) -> StudioContext:
        return self._context

    @property
    def paths(self) -> ScenePaths:
        return self._paths

    def invalidate(self) -> None:
        """No-op placeholder so the tree browser can call refresh like other tools."""

    def environments(self) -> list[str]:
        return ScenePaths.list_subdirs(
            self._paths.env_category_root(self._context.show)
        )

    def variants(self, env: str) -> list[str]:
        return ScenePaths.list_subdirs(
            self._paths.scene_description_root(self._context.show, env)
        )
