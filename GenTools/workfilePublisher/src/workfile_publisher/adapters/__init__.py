"""Host adapters for the workfile publisher."""

from .base import HostAdapter, HostAdapterError
from .standalone_adapter import StandaloneAdapter

__all__ = [
    "HostAdapter",
    "HostAdapterError",
    "StandaloneAdapter",
    "build_adapter",
]


def build_adapter(host: str) -> HostAdapter:
    """Factory: return the right adapter for the resolved host.

    Lazy-imports the Maya adapter so importing this module from a fresh Python
    doesn't pull in Maya unless needed.
    """
    if host == "maya":
        from .maya_adapter import MayaAdapter

        return MayaAdapter()
    if host == "standalone":
        return StandaloneAdapter()
    raise ValueError(f"Unknown host {host!r}; expected maya or standalone.")
