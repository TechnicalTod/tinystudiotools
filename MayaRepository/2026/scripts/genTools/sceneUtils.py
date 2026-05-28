"""
Scene utility functions for Maya

TINYSTUDIO_TOOL_CONFIG:
{
    "category": "utility",
    "label": "Scene Utilities",
    "tooltip": "Utility functions for Maya scene operations"
}
"""

import maya.cmds as mc
import maya.mel as mm
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]


def loadAdvancedSkeleton():
    """
    Load Advanced Skeleton shelf

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "Load Advanced Skeleton",
        "tooltip": "Load the Advanced Skeleton rigging shelf",
        "icon": "advancedSkeleton.png",
        "category": "rigging",
        "shelf_button": false,
        "menu_group": "Rigging"
    }
    """
    advancedSkeletonInstallPath = str(_REPO_ROOT / "GenTools" / "AdvancedSkeleton" / "install.mel")
    mm.eval(f'source "{advancedSkeletonInstallPath}"')


def blank():
    """
    Do nothing - placeholder function

    TINYSTUDIO_TOOL_CONFIG:
    {
        "label": "No Operation",
        "tooltip": "Placeholder function that does nothing",
        "category": "utility",
        "shelf_button": false
    }
    """
    return
