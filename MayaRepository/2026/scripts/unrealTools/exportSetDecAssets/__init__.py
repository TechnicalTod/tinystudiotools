import sys

from PySide6 import QtWidgets

from .constants import MAIN_WINDOW_OBJECT_NAME
from .main_window import MainWindow


def openWindow():
    app = QtWidgets.QApplication.instance()
    if app:
        for win in QtWidgets.QApplication.allWindows():
            if win.objectName() == MAIN_WINDOW_OBJECT_NAME:
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    MainWindow.window = MainWindow()
    MainWindow.window.show()
