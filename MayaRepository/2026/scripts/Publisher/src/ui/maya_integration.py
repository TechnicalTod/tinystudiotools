"""
Maya Integration utilities for UI components
"""

import sys
import os
from pathlib import Path

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtWidgets import QWidget
    from PySide6.QtCore import Qt
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui
        from PySide2.QtWidgets import QWidget
        from PySide2.QtCore import Qt
    except ImportError:
        raise ImportError("Neither PySide6 nor PySide2 is available")

# Maya specific imports
try:
    import maya.OpenMayaUI as OMUI
    import shiboken6

    MAYA_AVAILABLE = True
except ImportError:
    try:
        import maya.OpenMayaUI as OMUI
        import shiboken2 as shiboken6

        MAYA_AVAILABLE = True
    except ImportError:
        MAYA_AVAILABLE = False
        OMUI = None
        shiboken6 = None


class MayaUIIntegration:
    """Helper class for Maya UI integration"""

    @staticmethod
    def get_maya_main_window():
        """Get Maya's main window for parenting"""
        if not MAYA_AVAILABLE or not OMUI:
            return None

        try:
            maya_win = OMUI.MQtUtil.mainWindow()
            if maya_win:
                return shiboken6.wrapInstance(int(maya_win), QWidget)
        except:
            pass

        return None

    @staticmethod
    def load_maya_stylesheet(widget, stylesheet_name="dark.qss"):
        """Load Maya-style stylesheet"""
        try:
            # Try to find stylesheet in Maya's scripts directory or custom paths
            stylesheet_paths = [
                # Add your custom stylesheet paths here
                Path(__file__).parent / "styles" / stylesheet_name,
                Path.home() / "maya" / "scripts" / "styles" / stylesheet_name,
            ]

            # Try Maya specific paths if available
            if MAYA_AVAILABLE:
                try:
                    import maya.cmds as cmds

                    maya_app_dir = Path(cmds.internalVar(userAppDir=True))
                    stylesheet_paths.append(maya_app_dir / "scripts" / "styles" / stylesheet_name)
                except:
                    pass

            # Load the first available stylesheet
            for stylesheet_path in stylesheet_paths:
                if stylesheet_path.exists():
                    with open(stylesheet_path, "r") as f:
                        widget.setStyleSheet(f.read())
                    return True

            print(f"Stylesheet '{stylesheet_name}' not found in any of the search paths")
            return False

        except Exception as e:
            print(f"Failed to load stylesheet: {e}")
            return False

    @staticmethod
    def center_window(widget):
        """Center window on screen or Maya main window"""
        if not widget:
            return

        # Try to center relative to Maya main window first
        maya_win = MayaUIIntegration.get_maya_main_window()
        if maya_win:
            parent_geo = maya_win.geometry()
            x = parent_geo.x() + (parent_geo.width() - widget.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - widget.height()) // 2
            widget.move(x, y)
        else:
            # Center on screen
            screen_geo = QtWidgets.QApplication.desktop().screenGeometry()
            x = (screen_geo.width() - widget.width()) // 2
            y = (screen_geo.height() - widget.height()) // 2
            widget.move(x, y)


def create_maya_docked_widget(widget_class, widget_name="MayaPublisherTool"):
    """Create a dockable widget in Maya"""
    if not MAYA_AVAILABLE:
        return None

    try:
        import maya.cmds as cmds

        # Delete existing widget if it exists
        if cmds.workspaceControl(widget_name, exists=True):
            cmds.deleteUI(widget_name)

        # Create the workspace control
        workspace_control = cmds.workspaceControl(
            widget_name,
            label="Maya Publisher Tool",
            tabToControl=("AttributeEditor", -1),
            initialWidth=400,
            minimumWidth=300,
            retain=False,
            floating=True,
        )

        # Get the workspace control widget
        control_widget = OMUI.MQtUtil.findControl(workspace_control)
        if control_widget:
            control_widget = shiboken6.wrapInstance(int(control_widget), QWidget)

            # Create and add our widget
            publisher_widget = widget_class()
            layout = QtWidgets.QVBoxLayout(control_widget)
            layout.addWidget(publisher_widget)
            layout.setContentsMargins(0, 0, 0, 0)

            return publisher_widget

    except Exception as e:
        print(f"Failed to create docked widget: {e}")

    return None
