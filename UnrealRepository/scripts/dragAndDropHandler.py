import sys
from PySide2 import QtWidgets, QtGui, QtCore
import unreal
 
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAcceptDrops(True)
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle('Unreal Drag and Drop')
        self.setGeometry(300, 300, 300, 200)
        self.label = QtWidgets.QLabel('Drag an item here', self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
 
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
 
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.label.setText(f'Dropped: {file_path}')
 
#load UI
def openWindow():
    if QtWidgets.QApplication.instance():
        #Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            print (win.objectName())
            if 'Import Unreal Assets' in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())

openWindow()