import sys
import subprocess
import os
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PySide2.QtGui import QIcon
from PySide2.QtCore import QSize

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class SagaLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set window properties
        stylesheet_path = resource_path('styles/dark.qss')
        with open(stylesheet_path, "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle('Saga App Launcher')
        self.setGeometry(100, 100, 300, 200)

        # Create layout
        layout = QVBoxLayout()

        # Create buttons
        button1 = QPushButton()
        icon1_path = resource_path('icons/mayaIcon.png')
        icon1 = QIcon(icon1_path)
        button1.setIcon(icon1)
        button1.setIconSize(QSize(100, 100))
        button1.clicked.connect(self.run_batch1)

        button2 = QPushButton()
        icon2_path = resource_path('icons/unrealIcon.png')
        icon2 = QIcon(icon2_path)
        button2.setIcon(icon2)
        button2.setIconSize(QSize(100, 100))
        button2.clicked.connect(self.run_batch2)

        # Add buttons to layout
        layout.addWidget(button1)
        layout.addWidget(button2)

        # Set layout
        self.setLayout(layout)

    def run_batch1(self):
        batch1_path = resource_path('batch_files/launchMaya2023.bat')
        subprocess.run(batch1_path, shell=True)

    def run_batch2(self):
        batch2_path = resource_path('batch_files/launchUnrealProject.bat')
        subprocess.run(batch2_path, shell=True)

def main():
    app = QApplication(sys.argv)
    launcher = SagaLauncher()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
