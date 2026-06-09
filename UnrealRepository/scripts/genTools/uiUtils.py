"""UI utility functions for Unreal editor tools."""

import os
import sys

import unreal
from PySide6 import QtWidgets

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()

from studioUiUtils import center_widget, load_qss, show_singleton_qt_window

_UNREAL_TOOL_WINDOWS: dict[str, object] = {}

__all__ = [
    "center_widget",
    "content_path",
    "list_content_subdirs",
    "load_qss",
    "show",
    "show_singleton_qt_window",
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


def show(window_cls, object_name, *, parent=None):
    """Show a Unreal tool window once; raise/focus an existing instance."""
    window = show_singleton_qt_window(
        object_name,
        lambda: window_cls(parent=parent) if parent is not None else window_cls(),
        host="unreal",
        parent=parent,
    )
    if window is not None:
        _UNREAL_TOOL_WINDOWS[object_name] = window
        window_cls._tool_window = window
    return window


def show_unreal_tool_window(window_cls, object_name, *, parent=None):
    """Backward-compatible alias for show()."""
    return show(window_cls, object_name, parent=parent)
