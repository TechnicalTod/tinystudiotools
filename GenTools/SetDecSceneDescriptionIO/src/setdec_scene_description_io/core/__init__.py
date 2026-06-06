"""Core (host-agnostic) modules for SetDec scene-description IO.

Only the dependency-light modules are imported eagerly. ``usd_io`` requires
``pxr`` (present inside Maya / Unreal, optional for standalone dev), so it is
imported explicitly by callers rather than at package import time.
"""

# Do not import scene_service here — it references adapters and would create a
# circular import when adapters.base loads core.records.
from . import context, discovery, host, paths, records, versioning  # noqa: F401
