"""
Maya Shelf Integration Script
Adds the Maya Publishing Tool to Maya's shelf
"""

import os
import sys
from pathlib import Path


def add_to_maya_shelf():
    """Add the publishing tool to Maya's shelf"""
    try:
        import maya.cmds as cmds
        import maya.mel as mel
    except ImportError:
        print("This script must be run from within Maya")
        return False

    # Get the path to this script
    script_dir = Path(__file__).parent
    main_script = script_dir / "src" / "ui" / "main_window.py"

    # Create the shelf button command
    command = f"""
import sys
from pathlib import Path

script_path = r"{script_dir}"
if str(script_path) not in sys.path:
    sys.path.insert(0, str(script_path))

try:
    from src.ui.main_window import main
    window = main()
    print("Maya Publishing Tool launched successfully")
except Exception as e:
    print(f"Failed to launch Maya Publishing Tool: {{e}}")
    import traceback
    traceback.print_exc()
"""

    # Shelf name
    shelf_name = "Custom"

    # Check if shelf exists, create if not
    if not cmds.shelfLayout(shelf_name, exists=True):
        # Get the main shelf
        main_shelf = mel.eval("$tempVar = $gShelfTopLevel")
        cmds.shelfLayout(shelf_name, parent=main_shelf)

    # Add the button
    button_name = cmds.shelfButton(
        parent=shelf_name,
        label="Maya Publisher",
        annotation="Maya Asset Publishing Tool",
        image="menuIconWindow.png",  # Built-in Maya icon
        command=command,
        sourceType="python",
    )

    print(f"✅ Maya Publishing Tool added to {shelf_name} shelf")
    print(f"Button name: {button_name}")

    return True


def remove_from_maya_shelf():
    """Remove the publishing tool from Maya's shelf"""
    try:
        import maya.cmds as cmds
    except ImportError:
        print("This script must be run from within Maya")
        return False

    shelf_name = "Custom"

    if cmds.shelfLayout(shelf_name, exists=True):
        # Get all buttons on the shelf
        buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []

        for button in buttons:
            # Check if this is our button
            try:
                annotation = cmds.shelfButton(button, query=True, annotation=True)
                if annotation == "Maya Asset Publishing Tool":
                    cmds.deleteUI(button)
                    print(f"✅ Removed Maya Publishing Tool button: {button}")
                    return True
            except:
                continue

    print("⚠️ Maya Publishing Tool button not found on shelf")
    return False


def install_shelf_button():
    """Install the shelf button (main function)"""
    print("Installing Maya Publishing Tool shelf button...")
    return add_to_maya_shelf()


def uninstall_shelf_button():
    """Uninstall the shelf button"""
    print("Removing Maya Publishing Tool shelf button...")
    return remove_from_maya_shelf()


if __name__ == "__main__":
    # Check if we're in Maya
    try:
        import maya.cmds as cmds

        print("Running in Maya environment")
        install_shelf_button()
    except ImportError:
        print("Not running in Maya - this script is for Maya integration only")
        print("To use this script:")
        print("1. Copy this script to Maya")
        print("2. Run: exec(open(r'path/to/maya_shelf.py').read())")
        print("   or")
        print("3. Import and call: import maya_shelf; maya_shelf.install_shelf_button()")
