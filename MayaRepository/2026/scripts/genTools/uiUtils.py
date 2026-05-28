"""
UI utility functions for Maya

TINYSTUDIO_TOOL_CONFIG:
{
    "category": "utility",
    "label": "UI Utilities",
    "tooltip": "Utility functions for Maya UI operations"
}
"""

import maya.cmds as mc
import mayaFilePaths


def load_qss(filename):
    """Load a Qt stylesheet from the shared pyQtStyleSheets folder."""
    path = "{}/{}".format(mayaFilePaths.styleSheetFilepath, filename)
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def openUVEditor():
    """
    Open UV Editor panel

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "UV Editor",
        "tooltip": "Open the UV Editor panel",
        "icon": "UVTools.png",
        "category": "uv",
        "primary": true,
        "shelf_button": true
    }
    """
    for panel in mc.getPanel(sty="polyTexturePlacementPanel") or []:
        mc.scriptedPanel(panel, e=True, to=True)


def copyCurrentScenePath():
    """
    Copy current Maya scene path to clipboard

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Copy Scene Path",
        "tooltip": "Copy current scene path to clipboard",
        "icon": "clipboard.png",
        "category": "utility",
        "shelf_button": false,
        "menu_group": "Utilities"
    }
    """
    from PySide6 import QtGui

    maya_file = mc.file(sceneName=True, q=True)
    clip = QtGui.QClipboard()
    clip.setText(str(maya_file))
