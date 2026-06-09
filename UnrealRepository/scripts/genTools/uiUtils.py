"""UI utility functions for Unreal editor tools."""

import os
import sys

import unreal
from PySide6 import QtWidgets

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()

from studioUiUtils import center_widget, load_qss

__all__ = [
    "center_widget",
    "content_path",
    "list_content_subdirs",
    "load_qss",
    "show_unreal_tool_window",
]


def content_path(*segments):
    """Resolve a path under the Unreal project Content directory."""
    return os.path.join(unreal.Paths.project_content_dir(), *segments)


def list_content_subdirs(*segments):
    """Return sorted subdirectory names under a Content folder."""
    path = content_path(*segments)
    if not os.path.isdir(path):
        return []
    return sorted(
        name
        for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    )


def show_unreal_tool_window(window_cls, object_name):
    """Create or replace a tool window parented to the Unreal editor."""
    app = QtWidgets.QApplication.instance()
    if app:
        existing = getattr(window_cls, "_tool_window", None)
        if existing is not None:
            existing.close()
            existing.deleteLater()
            window_cls._tool_window = None

        for win in QtWidgets.QApplication.allWindows():
            if win.objectName() == object_name:
                win.close()
                win.deleteLater()
    else:
        QtWidgets.QApplication(sys.argv)

    window = window_cls()
    window.show()
    unreal.parent_external_window_to_slate(window.winId())
    window_cls._tool_window = window
    return window
