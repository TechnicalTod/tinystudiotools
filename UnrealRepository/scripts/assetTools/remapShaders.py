from PySide2 import QtGui, QtWidgets, QtCore
from PySide2.QtWidgets import QStyledItemDelegate, QStyleOptionButton, QStyle
from PySide2.QtCore import Qt, QRect, QEvent
import os
import sys
import unreal
from importlib import reload
import unrealFilePaths

class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # window prefs
        with open("{}/dark.qss".format(unrealFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle('Remap multiple shaders')
        self.setFocus()
        self.center()
        self.show()
        self.setGeometry(100, 100, 500, 500)

        #window layout setup
        self.createWidgets()
        self.connectLayout()

    #sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def createWidgets(self):
        self.treeView = QtWidgets.QTreeView()
        #self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.addSelectedButton = QtWidgets.QPushButton("Add (select in CB)")
        self.removeButton = QtWidgets.QPushButton("Remove Selected From List")
        self.toggleButton = QtWidgets.QPushButton("Toggle Selection")
        self.clearButton = QtWidgets.QPushButton("Clear All")
        self.remapShadersButton = QtWidgets.QPushButton("Remap Shaders")

        self.loaderShaderName = QtWidgets.QLineEdit("Please Load Shader From Content Browser.....")
        self.loaderShaderName.setReadOnly(True)

        # Set up the model for QTreeView
        self.model = QtGui.QStandardItemModel()
        self.treeView.setModel(self.model)
        self.treeView.setHeaderHidden(True)  # Hide the default header
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.openContextMenu)

        # button widget
        self.browseButton = QtWidgets.QPushButton()
        self.browseButton.setIcon(QtGui.QIcon("{}/shaderIcon.png".format(unrealFilePaths.UNREAL_shelfIconPath)))

        self.browseButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.browseButton.customContextMenuRequested.connect(self.showShaderContextMenu)
        
        #adjust the import button style sheet
        with open("{}/importButton.qss".format(unrealFilePaths.styleSheetFilepath), "r") as fh:
            self.remapShadersButton.setStyleSheet(fh.read())
        with open("{}/openButton.qss".format(unrealFilePaths.styleSheetFilepath), "r") as fh:
            self.browseButton.setStyleSheet(fh.read())

    #connect and populate the layout
    def connectLayout(self):
        #self.treeView.clicked.connect("")
        self.addSelectedButton.clicked.connect(self.populateListWithSelected)
        self.clearButton.clicked.connect(self.clearList)
        self.removeButton.clicked.connect(self.removeSelectedItems)
        self.toggleButton.clicked.connect(self.toggleAll)
        self.clearButton.clicked.connect(self.clearList)
        self.browseButton.clicked.connect(self.getSelectedShader)

        self.remapShadersButton.clicked.connect(self.remapShaders)

        buttonLayout = QtWidgets.QGridLayout()
        buttonLayout.addWidget(self.addSelectedButton, 0, 0)
        buttonLayout.addWidget(self.removeButton, 1, 0)
        buttonLayout.addWidget(self.toggleButton, 2, 0)
        buttonLayout.addWidget(self.clearButton, 3, 0)


        shaderLayout = QtWidgets.QGridLayout()
        shaderLayout.addWidget(self.loaderShaderName, 0, 0, 1, 5)
        shaderLayout.addWidget(self.browseButton, 0, 5, 1, 1)

        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.setRowStretch(1, 1)
        mainLayout.addLayout(shaderLayout, 0, 0, 1, 6)
        mainLayout.addWidget(self.treeView, 1, 0, 5, 5)
        mainLayout.addLayout(buttonLayout, 1, 5, 3, 1, alignment= QtCore.Qt.AlignTop)
        mainLayout.addWidget(self.remapShadersButton, 4, 5, alignment= QtCore.Qt.AlignBottom)

    def populateListWithSelected(self):
        # Get the selected assets from the content browser
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        for asset in selected_assets:
            if isinstance(asset, unreal.StaticMesh):
                staticMeshName = asset.get_name()
                staticMeshItem = QtGui.QStandardItem(QtGui.QIcon("{}/shaderIcon.png".format(unrealFilePaths.UNREAL_shelfIconPath)), str(staticMeshName))
                staticMeshItem.setFlags(staticMeshItem.flags() & ~QtCore.Qt.ItemIsEditable)
                staticMeshItem.setData(asset.get_path_name(), Qt.UserRole)
                self.makeItemBold([staticMeshItem], QtCore.Qt.black)
                staticMaterials = asset.static_materials
                for material in staticMaterials:
                    slotName = material.material_slot_name
                    material_item = QtGui.QStandardItem(str(slotName))
                    material_item.setFlags(material_item.flags() & ~QtCore.Qt.ItemIsEditable)
                    material_item.setCheckable(True)
                    staticMeshItem.appendRow([material_item])
                    material_item.setData(asset.get_path_name(), Qt.UserRole)
                self.model.appendRow(staticMeshItem)

        #Expand all groups
        self.treeView.expandAll()

    ##TODO: the following four functions are pretty much copies of each other. these need to be combined. sorry ran out of time
    def openContextMenu(self, position):
        indexes = self.treeView.selectedIndexes()
        if indexes:
            menu = QtWidgets.QMenu(self)
            findAction = menu.addAction("Find in Content Browser")
            findAction.triggered.connect(self.findInContentBrowser)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))
 
    def findInContentBrowser(self):
        indexes = self.treeView.selectedIndexes()
        if indexes:
            index = indexes[0]
            static_mesh = self.model.itemFromIndex(index).data(Qt.UserRole)
            print (static_mesh)
            static_mesh_path = static_mesh.split('.')[0]
            print (static_mesh_path)
            unreal.EditorAssetLibrary.sync_browser_to_objects([static_mesh_path])

    def showShaderContextMenu(self, position):
        contextMenu = QtWidgets.QMenu(self)
        copyAction = contextMenu.addAction('Find in Content Browser')
        copyAction.triggered.connect(self.findShaderInContentBrowser)
        contextMenu.exec_(QtGui.QCursor.pos())

    def findShaderInContentBrowser(self):
        indexes = self.treeView.selectedIndexes()
        shader = self.loaderShaderName.property('material_path')
        print (shader)
        shaderPath = shader.split('.')[0]
        print (shaderPath)
        unreal.EditorAssetLibrary.sync_browser_to_objects([shaderPath])

    def getSelectedShader(self):
        # Get the selected assets from the content browser
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        if selected_assets:
            material = selected_assets[0]
            if isinstance(material, (unreal.Material, unreal.MaterialInstance)):
                material_name = material.get_name()
                material_path = material.get_path_name()
                self.loaderShaderName.setText(material_name)
                self.loaderShaderName.setProperty('material_path', material_path)
                self.loaderShaderName.setStyleSheet("QLineEdit { font-weight: bold; color: rgb(80, 153, 255); }")

    def remapShaders(self):
        selected_paths = []
        for i in range(self.model.rowCount()):
            static_mesh_item = self.model.item(i)
            for j in range(static_mesh_item.rowCount()):
                material_item = static_mesh_item.child(j, 0)
                if material_item.checkState() == Qt.Checked:
                    static_mesh_path = material_item.data(Qt.UserRole)
                    static_mesh_path = static_mesh_path.split('.')[0]
                    loadedShaderPath = self.loaderShaderName.property('material_path')
                    loadedShaderPath = loadedShaderPath.split('.')[0]
                    # Load the static mesh
                    static_mesh = unreal.EditorAssetLibrary.load_asset(static_mesh_path)
                    # Load the material instance
                    material_instance = unreal.EditorAssetLibrary.load_asset(loadedShaderPath)
                    # Find the material slot index
                    slot_index = static_mesh.get_material_index(material_item.text())
                    # Apply the material instance to the slot
                    static_mesh.set_material(slot_index, material_instance)
                    #unreal.EditorAssetLibrary.save_asset(static_mesh_path)

    def toggleAll(self):
        # Iterate over all rows (parent items)
        for row in range(self.model.rowCount()):
            parent_item = self.model.item(row, 0)
            # Iterate over all children of the parent item
            for child_index in range(parent_item.rowCount()):
                child_item = parent_item.child(child_index)
                if child_item.checkState() == QtCore.Qt.Checked:
                    child_item.setCheckState(QtCore.Qt.Unchecked)
                else:
                    child_item.setCheckState(QtCore.Qt.Checked)

    # Clear all existing items
    def clearList(self):
        self.model.clear()

    # Get selected items and remove them from the model
    def removeSelectedItems(self):
        indexes = self.treeView.selectedIndexes()
        if not indexes:
            return

        # Collect the top-level rows to remove
        rows_to_remove = set()
        for index in indexes:
            if not index.parent().isValid():
                rows_to_remove.add(index.row())

        # Remove rows in reverse order to avoid affecting the remaining indices
        for row in sorted(rows_to_remove, reverse=True):
            self.model.removeRow(row)

    #helper function to make certain items bold with argument to feed in a color
    def makeItemBold(self, items, color):
        for item in items:
            font = QtGui.QFont()
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QtGui.QBrush(color))

    #funtion to check if folder exists, if not create it
    def createDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory '{path}' created.")
        else:
            print(f"Directory '{path}' already exists.")

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