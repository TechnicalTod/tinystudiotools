"""
Modelling selection utilities

SAGA_TOOL_CONFIG:
{
    "category": "modelling",
    "label": "Selection Utilities",
    "tooltip": "Advanced selection utilities for modeling"
}
"""

import maya.cmds as mc


def toggleSelectByAngle():
    """
    Toggle select faces by angle constraint

    SAGA_TOOL_CONFIG:
    {
        "label": "Select by Angle",
        "tooltip": "Toggle selection by angle constraint",
        "icon": "selectByAngle.png",
        "category": "selection",
        "shelf_button": false,
        "menu_group": "Selection"
    }
    """
    if not mc.polySelectConstraint(query=True, ap=True) is True:
        mc.polySelectConstraint(ap=True, at=38)
    else:
        mc.polySelectConstraint(ap=False, at=0)
