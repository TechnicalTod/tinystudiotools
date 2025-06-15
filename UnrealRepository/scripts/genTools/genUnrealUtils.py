from PySide6 import QtGui, QtWidgets, QtCore


def warningPopup(message):
    selectionWarningDialog = QtWidgets.QMessageBox()
    selectionWarningDialog.setText(message)
    selectionWarningDialog.setWindowTitle("Warning")
    selectionWarningDialog.exec_()
    print(message)
