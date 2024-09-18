from PySide2 import QtGui, QtWidgets, QtCore

def warningPopup(message):
    selectionWarningDialog = QtWidgets.QMessageBox()
    selectionWarningDialog.setText(message)
    selectionWarningDialog.setWindowTitle("Warning")
    selectionWarningDialog.exec_()
    print (message)