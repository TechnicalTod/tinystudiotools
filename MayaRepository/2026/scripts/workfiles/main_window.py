"""Maya shelf entry point for the cross-DCC workfile publisher.

Keep this module thin - it only exists so the long-standing shelf button at
``Workfiles -> workfiles.main_window.main`` keeps working while the real
implementation lives in ``workfile_publisher``.
"""

from __future__ import annotations


def main():
    """Open the Workfile Publisher parented to Maya's main window."""
    from workfile_publisher.ui.main_window import show_in_maya

    return show_in_maya()
