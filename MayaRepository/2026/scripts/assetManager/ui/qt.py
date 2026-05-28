"""Qt binding shim.

Maya 2026 ships PySide6, so that is the only binding the tool targets.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore[import-not-found]

Qt = QtCore.Qt
Signal = QtCore.Signal
Slot = QtCore.Slot

__all__ = ["QtCore", "QtGui", "QtWidgets", "Qt", "Signal", "Slot"]
