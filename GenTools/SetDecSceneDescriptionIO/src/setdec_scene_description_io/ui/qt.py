"""Qt binding shim.

Prefer PySide6 (Maya 2025+, Unreal 5.x), fall back to PySide2 for older hosts.
Importing from this module instead of either binding keeps the rest of the UI
binding-agnostic.
"""

from __future__ import annotations

try:
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore[import-not-found]

    QT_BINDING = "PySide6"
except ImportError:  # pragma: no cover - exercised on older hosts
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore[import-not-found]

    QT_BINDING = "PySide2"

Qt = QtCore.Qt
Signal = QtCore.Signal
Slot = QtCore.Slot

__all__ = ["QtCore", "QtGui", "QtWidgets", "Qt", "Signal", "Slot", "QT_BINDING"]
