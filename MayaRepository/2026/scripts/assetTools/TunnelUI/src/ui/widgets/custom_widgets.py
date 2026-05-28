"""
Custom widgets for TunnelUI Asset Browser.

This module contains custom Qt widgets extracted and refactored from the original TunnelUI.
"""

from PySide6.QtWidgets import QTabBar
from PySide6.QtCore import QSize


class StretchedTabBar(QTabBar):
    """Custom tab bar that stretches tabs to fill available width"""

    def __init__(self):
        super().__init__()
        self.setExpanding(True)

    def tabSizeHint(self, index):
        """Calculate tab size to distribute width evenly across all tabs"""
        # Get the default size hint and adjust the width so each tab takes equal space
        size = super().tabSizeHint(index)

        if self.parent():
            total_width = self.parent().width()  # Total width of the parent widget
            tab_count = self.count()  # Number of tabs
            if tab_count > 0:
                size.setWidth(total_width // tab_count)  # Divide the width by the number of tabs

        return size
