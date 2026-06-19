"""Entry point for the Import Unreal Assets tool window."""

from genTools.uiUtils import show_unreal_tool_window

from .main_window import MainWindow
from .styles import IMPORT_WINDOW_KEY


def show():
    return show_unreal_tool_window(MainWindow, IMPORT_WINDOW_KEY)


openWindow = show
