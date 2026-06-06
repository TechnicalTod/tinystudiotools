"""Scene adapters for SetDec scene-description IO."""

from .base import SceneAdapter, SceneAdapterError
from .standalone_adapter import StandaloneAdapter

__all__ = [
    "SceneAdapter",
    "SceneAdapterError",
    "StandaloneAdapter",
    "build_adapter",
]


def build_adapter(host: str) -> SceneAdapter:
    """Factory: return the adapter for the resolved host.

    Maya and Unreal adapters are imported lazily so importing this module from a
    fresh Python never pulls in ``pymel`` / ``unreal``.
    """
    if host == "maya":
        from .maya_adapter import MayaAdapter

        return MayaAdapter()
    if host == "unreal":
        from .unreal_adapter import UnrealAdapter

        return UnrealAdapter()
    if host == "standalone":
        return StandaloneAdapter()
    raise ValueError(
        f"Unknown host {host!r}; expected maya, unreal or standalone."
    )
