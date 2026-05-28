"""
TinyStudio Tools Shelf Builder with Auto-Discovery

This module builds the Maya shelf using auto-discovery of tools
with TINYSTUDIO_TOOL_CONFIG metadata, organized into category buttons
with right-click menus (matching the original system).
"""

import os
import json
import maya.cmds as cmds
import mayaFilePaths
import shelfCreate


# Hardcoded icon mapping for shelf items
SHELF_ICONS = {
    "spacer": "spacer.png",
    "Version Up File": "VersionUp.png",
    "Center Pivot": "centerPivot.png",
    "Freeze Transforms": "freezeTransforms.png",
    "Delete History": "deleteHistory.png",
    "Move B to A": "moveBA.png",
    "Move To Origin": "moveToOrigin.png",
    "Move Pivot B to A": "movePivotBA.png",
    "Move Pivot To Origin": "movePivotToOrigin.png",
    "Modelling Tools": "modelling.png",
    "Rigging Tools": "rigging.png",
    "UV Tools": "UVTools.png",
    "Texture Tools": "textureTools.png",
    "Shader Tools": "shaderTools.png",
    "Camera Tools": "cameraTools.png",
    "General Tools": "genTools.png",
    "Techvis Tools": "techvis.png",
    "Copy/Paste Selection": "copyPaste.png",
    "Take Snapshot": "snapshotTools.png",
    "Maya Publisher": "publisher.png",
    "Unreal Tools": "unrealTools.png",
    "Workfiles": "workfiles.png",
}

DEFAULT_ICON = "defaultTool.png"


def load_tool_config():
    """Load tool configuration from JSON file"""
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(script_dir, "..", "config", "tinystudio_tools.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"categories": {}}


def create_tool_command(module_name, function_name, label):
    """Create a command function that safely imports and runs a tool"""

    def command():
        try:
            # Dynamic import and execution
            module = __import__(module_name, fromlist=[function_name])
            func = getattr(module, function_name)
            func()
        except Exception as e:
            cmds.warning(f"Error running {label}: {e}")

    return command


def get_icon_for_item(label, item_type):
    """Get the appropriate icon for a shelf item"""
    if item_type == "spacer":
        return SHELF_ICONS.get("spacer", "spacer.png")

    # Only top-level buttons get icons
    return SHELF_ICONS.get(label, DEFAULT_ICON)


def buildTinyStudioShelf():
    """Build the TinyStudio shelf from config"""
    print("Building TinyStudio shelf from config...")

    # Load configuration
    config = load_tool_config()
    shelf_items = config.get("shelf_items", [])

    if not shelf_items:
        print("No shelf items found in config!")
        return

    # Create shelf using existing system
    icon_path = mayaFilePaths.mayaShelfIconPath

    # Handle case where icon_path is None
    if icon_path is None:
        print("Warning: mayaShelfIconPath is None, using default path")
        # Use a default path relative to the script directory
        script_dir = os.path.dirname(__file__)
        icon_path = os.path.join(script_dir, "..", "icons").replace("\\", "/") + "/"

    shelf_tool = shelfCreate.ShelfTool("TinyStudioTools", icon_path)
    shelf_tool.createShelf()

    # Process each shelf item in order
    for item in shelf_items:
        item_type = item.get("type")

        try:
            if item_type == "spacer":
                # Add spacer
                icon = get_icon_for_item("spacer", "spacer")
                shelf_tool.addShelfSpacer(iconImage=icon)
                print(f"  Added spacer")

            elif item_type == "button":
                # Add individual button
                label = item.get("label", "Unknown")
                module_name = item.get("module")
                function_name = item.get("function")
                icon = item.get("icon") or get_icon_for_item(label, "button")

                if module_name and function_name:
                    # Create command for the button
                    cmd = create_tool_command(module_name, function_name, label)
                    button = shelf_tool.shelfButton(cmd, icon, label)

                    # Add menu items if they exist (no icons for menu items)
                    menu_items = item.get("menu", [])
                    if menu_items:
                        for menu_item in menu_items:
                            menu_label = menu_item.get("label", "")
                            menu_module = menu_item.get("module")
                            menu_function = menu_item.get("function")

                            if menu_module and menu_function:
                                menu_cmd = create_tool_command(
                                    menu_module, menu_function, menu_label
                                )
                                shelf_tool.addMenu(button, menu_label, menu_cmd)

                    print(f"  Added button: {label}")

            elif item_type == "category_button":
                # Add category button with primary action and menu
                label = item.get("label", "Unknown")
                primary_action = item.get("primary_action", {})
                icon = get_icon_for_item(label, "category_button")

                # Create primary command
                primary_module = primary_action.get("module")
                primary_function = primary_action.get("function")

                if primary_module and primary_function:
                    primary_cmd = create_tool_command(primary_module, primary_function, label)
                else:
                    # Default to blank command
                    primary_cmd = create_tool_command("genTools.sceneUtils", "blank", "Blank")

                # Create the category button
                button = shelf_tool.shelfButton(primary_cmd, icon, label)

                # Add menu items (no icons for menu items)
                menu_items = item.get("menu", [])
                if menu_items:
                    for menu_item in menu_items:
                        menu_type = menu_item.get("type")

                        if menu_type == "blank_item":
                            # Add blank menu item
                            shelf_tool.addMenu(
                                button,
                                "",
                                create_tool_command("genTools.sceneUtils", "blank", "Blank"),
                            )

                        elif menu_type == "spacer":
                            # Add menu spacer with label
                            menu_label = menu_item.get("label", "")
                            shelf_tool.addMenuSpacer(button, label=menu_label)

                        elif menu_type == "submenu":
                            # Add submenu
                            submenu_label = menu_item.get("label", "")
                            submenu = shelf_tool.addSubMenu(button, submenu_label)

                            # Add submenu items (no icons)
                            submenu_items = menu_item.get("items", [])
                            for submenu_item in submenu_items:
                                sub_label = submenu_item.get("label", "")
                                sub_module = submenu_item.get("module")
                                sub_function = submenu_item.get("function")

                                if sub_module and sub_function:
                                    sub_cmd = create_tool_command(
                                        sub_module, sub_function, sub_label
                                    )
                                    shelf_tool.addMenu(submenu, sub_label, sub_cmd)

                        else:
                            # Regular menu item (no icons)
                            menu_label = menu_item.get("label", "")
                            menu_module = menu_item.get("module")
                            menu_function = menu_item.get("function")

                            if menu_module and menu_function:
                                menu_cmd = create_tool_command(
                                    menu_module, menu_function, menu_label
                                )
                                shelf_tool.addMenu(button, menu_label, menu_cmd)

                print(f"  Added category button: {label}")

        except Exception as e:
            print(f"  Error creating {item_type} '{item.get('label', 'Unknown')}': {e}")
            import traceback

            traceback.print_exc()

    print(f"TinyStudio shelf built with {len(shelf_items)} items!")


if __name__ == "__main__":
    try:
        buildTinyStudioShelf()
    except Exception as e:
        print(f"Error building shelf: {e}")
        import traceback

        traceback.print_exc()
