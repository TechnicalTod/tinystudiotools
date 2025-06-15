"""
Techvis crane import utilities

SAGA_TOOL_CONFIG:
{
    "category": "techvis",
    "label": "Crane Tools",
    "tooltip": "Import and manage techvis cranes"
}
"""

import maya.cmds as mc


def importST15():
    """
    Import Super Techno 15 crane

    SAGA_TOOL_CONFIG:
    {
        "label": "Super Techno 15",
        "tooltip": "Import Super Techno 15 crane",
        "icon": "crane_st15.png",
        "category": "techvis",
        "shelf_button": false,
        "menu_group": "Cranes"
    }
    """
    # Specify the path to the Maya scene file
    scene_path = r"L:\SagaTools\GenTools\cranes\superTechno15.mb"
    # Import the Maya scene file
    mc.file(
        scene_path,
        i=True,
        type="mayaBinary",
        options="v=0",
        preserveReferences=True,
        ignoreVersion=True,
    )


def importCrane(crane_type="st15"):
    """
    Import crane by type

    SAGA_TOOL_CONFIG:
    {
        "label": "Import Crane",
        "tooltip": "Import crane by type",
        "icon": "crane.png",
        "category": "techvis",
        "shelf_button": false,
        "menu_group": "Cranes"
    }
    """
    crane_files = {
        "st15": "superTechno15.mb",
        "st30": "superTechno30.mb",
        "techno50": "techno50.mb",
    }

    if crane_type not in crane_files:
        print(f"Unknown crane type: {crane_type}")
        return

    base_path = r"L:\SagaTools\GenTools\cranes"
    scene_path = f"{base_path}\\{crane_files[crane_type]}"
    mc.file(
        scene_path,
        i=True,
        type="mayaBinary",
        options="v=0",
        preserveReferences=True,
        ignoreVersion=True,
    )
