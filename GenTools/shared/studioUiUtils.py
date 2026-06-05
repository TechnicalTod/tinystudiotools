"""Shared Qt UI helpers for Maya, Unreal, and other TinyStudio DCC tools."""

import os

from studioFilePaths import styleSheetFilepath


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
    """Center a top-level widget on the primary screen (Qt6 / PySide6)."""
    from PySide6 import QtGui, QtWidgets

    qr = widget.frameGeometry()
    screen = QtWidgets.QApplication.primaryScreen()
    if screen is None:
        screen = QtGui.QGuiApplication.primaryScreen()
    if screen is not None:
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        widget.move(qr.topLeft())
