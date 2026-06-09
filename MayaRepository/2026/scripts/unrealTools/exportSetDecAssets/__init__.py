from genTools.uiUtils import show_singleton_qt_window

from .constants import MAIN_WINDOW_OBJECT_NAME
from .main_window import MainWindow


def show():
    return show_singleton_qt_window(
        MAIN_WINDOW_OBJECT_NAME,
        MainWindow,
        host="maya",
    )


openWindow = show
