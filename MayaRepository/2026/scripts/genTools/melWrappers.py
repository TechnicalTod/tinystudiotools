"""
MEL command wrapper utilities for Maya

TINYSTUDIO_TOOL_CONFIG:
{
    "category": "utility",
    "label": "MEL Wrappers",
    "tooltip": "Python wrappers for common MEL commands"
}
"""

import maya.mel as mm


def movePivotBA():
    """
    Move pivot from B to A

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Move Pivot B to A",
        "tooltip": "Move pivot from object B to object A",
        "icon": "movePivotBA.png",
        "category": "transform",
        "shelf_button": true
    }
    """
    mm.eval("movePivotBA();")


def movePivotToOrigin():
    """
    Move pivot to origin

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Move Pivot To Origin",
        "tooltip": "Move pivot to world origin",
        "icon": "movePivotToOrigin.png",
        "category": "transform",
        "shelf_button": true
    }
    """
    mm.eval("movePivotToOrigin();")


def sortOutliner():
    """
    Sort outliner alphabetically

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Sort Outliner",
        "tooltip": "Sort outliner alphabetically",
        "icon": "sortOutliner.png",
        "category": "ui",
        "shelf_button": false,
        "menu_group": "UI"
    }
    """
    mm.eval("sortOutliner();")


def cometRename():
    """
    Launch Comet rename tool

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Comet Rename",
        "tooltip": "Launch Comet rename tool",
        "icon": "cometRename.png",
        "category": "utility",
        "shelf_button": false,
        "menu_group": "Utilities"
    }
    """
    mm.eval("cometRename();")


def detachDuplicateComponents():
    """
    Detach and duplicate selected components

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Duplicate Components",
        "tooltip": "Detach and duplicate selected components",
        "icon": "duplicateComponents.png",
        "category": "modelling",
        "shelf_button": false,
        "menu_group": "Components"
    }
    """
    mm.eval("detachDuplicateComponents();")


def selectNthEdge():
    """
    Select every Nth edge in edge ring

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Select Nth Edge",
        "tooltip": "Select every other edge in an edge ring",
        "icon": "selectNthEdge.png",
        "category": "selection",
        "shelf_button": false,
        "menu_group": "Selection"
    }
    """
    mm.eval('polySelectEdgesEveryN "edgeRing" 2;')


def randomVertCol():
    """
    Apply random vertex colors to selection

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Random Vertex Color",
        "tooltip": "Apply random vertex colors to selection",
        "icon": "randomVertCol.png",
        "category": "shading",
        "shelf_button": false,
        "menu_group": "Vertex Colors"
    }
    """
    mm.eval("randomVertCol();")


def doraSkinWeight():
    """
    Launch Dora Skin Weight tool

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Dora Skin Weight",
        "tooltip": "Launch Dora Skin Weight tool",
        "icon": "doraSkinWeight.png",
        "category": "rigging",
        "shelf_button": false,
        "menu_group": "Skinning"
    }
    """
    mm.eval("DoraSkinWeightImpExp();")
