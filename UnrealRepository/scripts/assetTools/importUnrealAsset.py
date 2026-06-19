"""Backward-compat shim — use assetTools.ImportUnrealAssets instead."""

from assetTools.ImportUnrealAssets.ui.entry import openWindow, show
from assetTools.ImportUnrealAssets.ui.main_window import MainWindow

__all__ = ["MainWindow", "openWindow", "show"]
