"""Shared Qt UI helpers for Maya, Unreal, and other TinyStudio DCC tools."""

from __future__ import annotations

import os
import sys
import weakref
from typing import Callable, Literal, Optional

from studioFilePaths import styleSheetFilepath

_HOST = Literal["maya", "unreal", "standalone"]
_WINDOW_REGISTRY: dict[str, weakref.ref] = {}
_WINDOW_STRONG_REFS: dict[str, object] = {}


def _import_qt():
    try:
        from PySide6 import QtCore, QtGui, QtWidgets

        return QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore[no-redef]

        return QtCore, QtGui, QtWidgets


def _ensure_qapplication():
    _, _, QtWidgets = _import_qt()
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app


def _is_widget_alive(widget) -> bool:
    if widget is None:
        return False
    try:
        # Minimized or hidden windows are still alive; only deleted wrappers raise.
        widget.objectName()
        return True
    except RuntimeError:
        return False


def _find_live_widget(key: str):
    """Return an existing live widget from the registry or top-level scan."""
    _, _, QtWidgets = _import_qt()

    ref = _WINDOW_REGISTRY.get(key)
    if ref is not None:
        widget = ref()
        if _is_widget_alive(widget):
            return widget
        _WINDOW_REGISTRY.pop(key, None)

    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == key and _is_widget_alive(widget):
            return widget

    for window in QtWidgets.QApplication.allWindows():
        if window.objectName() == key and _is_widget_alive(window):
            return window

    return None


def _register_widget(key: str, widget) -> None:
    def _clear(_obj=None):
        if _WINDOW_REGISTRY.get(key) is ref:
            _WINDOW_REGISTRY.pop(key, None)
        _WINDOW_STRONG_REFS.pop(key, None)

    ref = weakref.ref(widget, _clear)
    _WINDOW_REGISTRY[key] = ref
    _WINDOW_STRONG_REFS[key] = widget


def _focus_widget(widget) -> None:
    if hasattr(widget, "isMinimized") and widget.isMinimized():
        widget.showNormal()
    else:
        widget.show()
    widget.raise_()
    widget.activateWindow()


def _icons_dir():
    for env_name in ("MAYA_REPO", "UNREAL_REPO"):
        repo_root = (os.getenv(env_name) or "").replace("\\", "/")
        if repo_root and os.path.isdir(repo_root + "/icons"):
            return repo_root + "/icons"
    return None


def load_qss(filename):
    """Load a Qt stylesheet from GenTools/pyQtStyleSheets."""
    if not styleSheetFilepath:
        raise RuntimeError(
            "Stylesheet path not configured. Set SCRIPT_DIR, MAYA_REPO, or UNREAL_REPO."
        )
    path = "{}{}".format(styleSheetFilepath, filename)
    with open(path, "r", encoding="utf-8") as fh:
        qss = fh.read()

    icons_dir = _icons_dir()
    if icons_dir:
        qss = qss.replace("url(../../icons/", "url({}/".format(icons_dir))
        qss = qss.replace("url(../icons/", "url({}/".format(icons_dir))
    return qss


def center_widget(widget):
    """Center a top-level widget on the primary screen."""
    _, QtGui, QtWidgets = _import_qt()

    qr = widget.frameGeometry()
    screen = QtWidgets.QApplication.primaryScreen()
    if screen is None:
        screen = QtGui.QGuiApplication.primaryScreen()
    if screen is not None:
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        widget.move(qr.topLeft())


def maya_main_window():
    """Return Maya's main window as a QWidget, or None outside Maya."""
    try:
        import maya.OpenMayaUI as omui
    except ImportError:
        return None

    try:
        from shiboken6 import wrapInstance
    except ImportError:
        try:
            from shiboken2 import wrapInstance  # type: ignore[no-redef]
        except ImportError:
            return None

    _, _, QtWidgets = _import_qt()
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def show_singleton_qt_window(
    key: str,
    factory: Callable[[], object],
    *,
    host: _HOST = "standalone",
    parent=None,
):
    """Show a tool window once; raise/focus an existing instance on repeat calls."""
    QtCore, _, QtWidgets = _import_qt()
    _ensure_qapplication()

    existing = _find_live_widget(key)
    if existing is not None:
        _focus_widget(existing)
        return existing

    window = factory()
    if window is None:
        return None

    if parent is not None and hasattr(window, "setParent"):
        window.setParent(parent)

    window.setObjectName(key)
    if host != "unreal" and hasattr(window, "setAttribute"):
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    window.show()

    if host == "unreal":
        import unreal

        unreal.parent_external_window_to_slate(window.winId())

    _register_widget(key, window)
    return window
