import os
import re
import glob
import sys
import getpass
import unreal
import subprocess
from PySide6 import QtGui, QtWidgets, QtCore
from importlib import reload
import genTools.genUnrealUtils as genUnrealUtils
import genTools.genUnrealImportUtils as genUnrealImportUtils
from genTools.uiUtils import center_widget, load_qss
import assetTools.getUSDTexturePaths as getUSDTexturePaths
from assetTools.setdec_paths import (
    is_setdec_asset_folder,
    list_setdec_groups,
    setdec_group_folder,
    setdec_production_folder,
)

parameterList = {
    "USDPreviewMaterial": {
        "diffuse": {
            "suffix": "Diffuse",
            "mayaParameter": "diffuseColor",
            "fileNodeParameter": "outColor",
        },
        "emissive": {
            "suffix": "Emissive",
            "mayaParameter": "emissiveColor",
            "fileNodeParameter": "outColor",
        },
        "ao": {"suffix": "AO", "mayaParameter": "occlusion", "fileNodeParameter": "outAlpha"},
        "opacity": {
            "suffix": "Opacity.",
            "mayaParameter": "opacity",
            "fileNodeParameter": "outAlpha",
        },
        "metallic": {
            "suffix": "Metallic",
            "mayaParameter": "metallic",
            "fileNodeParameter": "outAlpha",
        },
        "roughness": {
            "suffix": "Roughness",
            "mayaParameter": "roughness",
            "fileNodeParameter": "outAlpha",
        },
        "normal": {"suffix": "Normal", "mayaParameter": "normal", "fileNodeParameter": "outColor"},
        "subsurface": {
            "suffix": "Translucency",
            "mayaParameter": "clearcoat",
            "fileNodeParameter": "outAlpha",
        },
        "displacement": {
            "suffix": "Displacement",
            "mayaParameter": "displacement",
            "fileNodeParameter": "outAlpha",
        },
    }
}


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self._current_show = self._resolve_current_show()
        self._current_user = self._resolve_current_user()
        self._base_show_dir = self._resolve_base_show_dir()
        self._setdec_root = setdec_production_folder(self._current_show)
        self.initUI()

    def initUI(self):
        # window prefs
        self.setStyleSheet(load_qss("dark.qss"))
        self.setWindowTitle("Import SetDec Assets — {}".format(self._current_show))
        self.setFocus()
        self.center()
        self.show()

        self.setGeometry(100, 100, 1400, 600)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)
        self.setLayout(outer)

        outer.addWidget(self._build_header())

        setdec_label = QtWidgets.QLabel(
            "<b>Set Dec root:</b> <code>{}</code>".format(self._setdec_root)
        )
        setdec_label.setWordWrap(True)
        setdec_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        outer.addWidget(setdec_label)

        content = QtWidgets.QHBoxLayout()
        content.setSpacing(8)
        outer.addLayout(content, 1)

        browser_panel = self._build_setdec_browser()
        content.addWidget(browser_panel, 0)

        table_panel = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(table_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        content.addWidget(table_panel, 1)

        # create table widget
        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnWidth(0, 900)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)

        self.tableWidgetHeader = self.tableWidget.horizontalHeader()
        self.tableWidgetHeader.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.tableWidget.setHorizontalHeaderLabels(
            ["Asset Path", "Variant", "Version", "Asset Type"]
        )

        # create buttons
        self.addButton = QtWidgets.QPushButton("Add Selected")
        self.addButton.clicked.connect(self.add)

        self.removeButton = QtWidgets.QPushButton("Remove")
        self.removeButton.clicked.connect(self.remove)

        self.clearButton = QtWidgets.QPushButton("Clear")
        self.clearButton.clicked.connect(self.clear)

        self.ImportButton = QtWidgets.QPushButton("Import")
        self.ImportButton.clicked.connect(self.importAsset)

        # adjust the import button style sheet
        self.ImportButton.setStyleSheet(
            """
            QPushButton
            {
            color: #b1b1b1;
            background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #015305, stop: 0.1 #015305, stop: 0.5 #014c1c, stop: 0.9 #014c1c, stop: 1 #014c1c);
            }
            QPushButton:pressed
            {
                background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
            }
        """
        )

        layout.addWidget(self.tableWidget, 0, 0, 4, 1)
        layout.addWidget(self.addButton, 0, 1)
        layout.addWidget(self.removeButton, 1, 1)
        layout.addWidget(self.clearButton, 2, 1)
        layout.addWidget(self.ImportButton, 3, 1, alignment=QtCore.Qt.AlignBottom)

        # show the window
        self.show()

    # sets UI to be created in center (used in window prefs)
    def center(self):
        center_widget(self)

    @staticmethod
    def _resolve_current_show():
        current_show = os.environ.get("SHOW_NAME", "").strip()
        if not current_show:
            raise RuntimeError(
                "SHOW_NAME is not set. Launch Unreal through TinyStudioLauncher, "
                "then reopen Import SetDec Assets."
            )
        return current_show

    @staticmethod
    def _resolve_current_user():
        return os.environ.get("USERNAME", "").strip() or getpass.getuser()

    @staticmethod
    def _resolve_base_show_dir():
        return os.environ.get("TINYSTUDIO_BASE_SHOW_DIR", "").strip() or "N/A"

    def _build_header(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        title = QtWidgets.QLabel("<b>Show:</b> {}".format(self._current_show))
        user = QtWidgets.QLabel("<b>User:</b> {}".format(self._current_user))
        drive = QtWidgets.QLabel("<b>Drive:</b> {}".format(self._base_show_dir))

        for widget in (title, user, drive):
            widget.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
            )

        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(user)
        layout.addStretch(1)
        layout.addWidget(drive)
        return frame

    def _build_setdec_browser(self):
        panel = QtWidgets.QWidget()
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(460)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        group_label = QtWidgets.QLabel("Set Dec Group")
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.currentIndexChanged.connect(self._on_group_changed)

        self.fs_model = QtWidgets.QFileSystemModel(self)
        self.fs_model.setFilter(
            QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.NoDotAndDotDot
        )
        self.fs_model.setRootPath(self._setdec_root)

        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.fs_model)
        self.tree.setHeaderHidden(True)
        for column in (1, 2, 3):
            self.tree.hideColumn(column)
        self.tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.tree.setAnimated(True)
        self.tree.setIndentation(18)

        self.browser_status = QtWidgets.QLabel()
        self.browser_status.setWordWrap(True)

        layout.addWidget(group_label)
        layout.addWidget(self.group_combo)
        layout.addWidget(QtWidgets.QLabel("Asset Folders"))
        layout.addWidget(self.tree, 1)
        layout.addWidget(self.browser_status)

        self._refresh_groups()
        return panel

    def _refresh_groups(self):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()

        if not os.path.isdir(self._setdec_root):
            self.group_combo.addItem("(setdec folder not found)")
            self.group_combo.setEnabled(False)
            self.tree.setEnabled(False)
            self.browser_status.setText(
                "Expected folder does not exist: {}".format(self._setdec_root)
            )
        else:
            groups = list_setdec_groups(self._current_show)
            if groups:
                self.group_combo.addItems(groups)
                self.group_combo.setEnabled(True)
                self.tree.setEnabled(True)
                self.browser_status.setText(
                    "Select asset folders, then click Add Selected."
                )
            else:
                self.group_combo.addItem("(no groups in setdec)")
                self.group_combo.setEnabled(False)
                self.tree.setEnabled(False)
                self.browser_status.setText(
                    "No Set Dec groups under {}.".format(self._setdec_root)
                )

        self.group_combo.blockSignals(False)
        self._on_group_changed()

    def _on_group_changed(self):
        if not self.group_combo.isEnabled():
            return

        group = self.group_combo.currentText()
        group_path = setdec_group_folder(self._current_show, group)
        if not os.path.isdir(group_path):
            return

        index = self.fs_model.index(group_path)
        self.tree.setRootIndex(index)
        self.tree.expand(index)

    def _paths_from_tree_selection(self):
        paths = []
        for index in self.tree.selectedIndexes():
            if index.column() != 0:
                continue
            path = self.fs_model.filePath(index).replace("\\", "/")
            if is_setdec_asset_folder(self._setdec_root, path) and path not in paths:
                paths.append(path)
        return paths

    # Function to add rows to table
    def add(self, pathList=None):
        # get list of selected shapes
        paths = []
        if pathList:
            paths = pathList
        else:
            paths = self._paths_from_tree_selection()
            if not paths:
                genUnrealUtils.warningPopup(
                    "Select one or more asset folders in the Set Dec browser first."
                )
                return

        # get initial row count
        init_row_number = self.tableWidget.rowCount()

        # Loop over paths from file dialog and create new rows
        for row_number, path in enumerate(paths):
            baseSetDecPath = path
            self.tableWidget.insertRow(init_row_number + row_number)
            self.tableWidget.setItem(
                init_row_number + row_number, 0, QtWidgets.QTableWidgetItem(baseSetDecPath)
            )

            # create combo box for version column
            variantComboBox = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(init_row_number + row_number, 1, variantComboBox)
            variantList = []
            # get list of variants from path dir
            for variantFolder in os.listdir(baseSetDecPath):
                variantList.append(variantFolder)
            variantComboBox.addItems(variantList)
            variantComboBox.setCurrentIndex(0)
            if len(variantList) > 1:
                variantComboBox.setStyleSheet(load_qss("qComboBoxMultiItemYellow.qss"))

            # create combo box for version column
            versionComboBox = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(init_row_number + row_number, 2, versionComboBox)
            versionList = []
            # get list of versions from path dir
            for versionFolder in os.listdir(baseSetDecPath + "/" + variantComboBox.currentText()):
                versionList.append(versionFolder)
            versionComboBox.addItems(versionList)
            versionComboBox.setCurrentIndex(len(versionList) - 1)

            # create combo box for asset type column
            assetTypeComboBox = QtWidgets.QComboBox()
            self.tableWidget.setCellWidget(init_row_number + row_number, 3, assetTypeComboBox)
            assetTypeComboBox.addItems(["Static Mesh", "Skeletal Mesh"])

            skeletalMeshParentFolder = baseSetDecPath.split("/")[-4]

            if skeletalMeshParentFolder in ("CHR", "PROP", "CRE", "VEH"):
                index = assetTypeComboBox.findText("Skeletal Mesh", QtCore.Qt.MatchFixedString)
                if index >= 0:
                    assetTypeComboBox.setCurrentIndex(index)

            # set combobox update linking
            variantComboBox.currentIndexChanged.connect(
                lambda index, row=init_row_number + row_number, column=1: self.updateVerNumOnVarChange(
                    row
                )
            )

            # set duplicate setDec names red
            self.setDuplicateInputsRed()

    # Function to remove rows to table (must remove in reverse order)
    def remove(self):
        rowList = sorted(set(index.row() for index in self.tableWidget.selectedIndexes()))
        for row in reversed(sorted(rowList)):
            self.tableWidget.removeRow(row)
        self.resetCurrentList()

    # Function to completely clear table
    def clear(self):
        self.tableWidget.setRowCount(0)

    # Function to refresh table
    def resetCurrentList(self):
        setDecPathList = []
        init_row_number = self.tableWidget.rowCount()
        # Initial sanity checks on the asset list for duplicate naming
        for row in range(init_row_number):
            # look up set Dec name from table
            setDecPath = self.tableWidget.item(row, 0)
            setDecPath = setDecPath.text()
            setDecPathList.append(setDecPath)
        self.clear()
        self.add(setDecPathList)

    def getDuplicatesInList(self):
        init_row_number = self.tableWidget.rowCount()
        # Initial sanity checks on the asset list for duplicate naming
        setDecPathList = []
        for row in range(init_row_number):
            setDecPath = self.tableWidget.item(row, 0)
            setDecPath = setDecPath.text()
            setDecPathList.append(setDecPath)
        duplicateShapeNames = set(
            [name for name in setDecPathList if setDecPathList.count(name) > 1]
        )
        return duplicateShapeNames

    def setDuplicateInputsRed(self):
        getDuplicatesInList = self.getDuplicatesInList()
        init_row_number = self.tableWidget.rowCount()
        for row in range(init_row_number):
            setDecPath = self.tableWidget.item(row, 0)
            setDecPath = setDecPath.text()
            if setDecPath in getDuplicatesInList:
                self.tableWidget.item(row, 0).setBackground(QtGui.QColor("#7D2020"))

    # Loop through all rows and collect data for import
    # then checks Asset type to start running the respective imports
    def importAsset(self):
        init_row_number = self.tableWidget.rowCount()
        for row in range(init_row_number):
            # look up asset path from table
            assetPath = self.tableWidget.item(row, 0)
            assetPath = assetPath.text()
            # look up corresponding variant from table
            variantName = self.tableWidget.cellWidget(row, 1)
            variantName = variantName.currentText()
            # look up corresponding version number from table
            versionNumber = self.tableWidget.cellWidget(row, 2)
            versionNumber = versionNumber.currentText()
            # look up corresponding asset type from table
            assetType = self.tableWidget.cellWidget(row, 3)
            assetType = assetType.currentText()

            # Run import functions
            if assetType == "Static Mesh":
                importedMesh, unrealMeshImportPath = self.importStaticMesh(
                    assetPath, variantName, versionNumber
                )
                importedTextures = self.importTextures(
                    assetPath, variantName, versionNumber, unrealMeshImportPath, assetType
                )
                self.assignMaterialInstanceToMesh(
                    importedMesh, unrealMeshImportPath, importedTextures, assetType
                )

            if assetType == "Skeletal Mesh":
                importedMesh, unrealMeshImportPath = self.importSkeletalMesh(
                    assetPath, variantName, versionNumber
                )
                importedTextures = self.importTextures(
                    assetPath, variantName, versionNumber, unrealMeshImportPath, assetType
                )
                self.assignMaterialInstanceToMesh(
                    importedMesh, unrealMeshImportPath, importedTextures, assetType
                )

    # Static mesh importer
    def importStaticMesh(self, assetPath, variantName, versionNumber):
        # Get published fbx path
        publishedFBXPath = "{}/{}/{}/fbx/".format(assetPath, variantName, versionNumber)
        # split out asset name from directory path
        assetName = assetPath.split("/")[-1]
        # split out set dec env name from directory path
        setDecEnvName = assetPath.split("/")[-2]
        # build unreal asset import directory
        unrealMeshImportPath = "/Game/01_Assets/SETDEC"
        unrealMeshImportPath = "{}/{}/{}/{}/{}".format(
            unrealMeshImportPath, setDecEnvName, assetName, variantName, versionNumber
        )
        # Get list of FBX files in publish dir and do sanity checks
        fbxList = []
        for fbx in os.listdir(publishedFBXPath):
            if fbx.endswith(".fbx"):
                fbxList.append(fbx)
        if len(fbxList) > 1:
            genUnrealUtils.warningPopup(
                "Found too many FBX files in {} publish directory".format(assetName)
            )
        if len(fbxList) == 0:
            genUnrealUtils.warningPopup(
                "No FBX files found in {} publish directory".format(assetName)
            )
        else:
            FBXAssetPath = publishedFBXPath + fbxList[0]
        # build import task and run it
        importMeshTask = genUnrealImportUtils.buildImportTask(
            FBXAssetPath, unrealMeshImportPath, genUnrealImportUtils.buildStaticMeshImportOptions()
        )
        importedMesh = genUnrealImportUtils.executeImportTasks([importMeshTask])

        return importedMesh, unrealMeshImportPath

    # Static mesh importer
    def importSkeletalMesh(self, assetPath, variantName, versionNumber):
        # Get published fbx path
        publishedFBXPath = "{}/{}/{}/unrealExport/".format(assetPath, variantName, versionNumber)
        # split out CHR/PROP/CRE/VEH name from directory path
        assetName = assetPath.split("/")[-3]
        publishDir = assetPath.split("/")[-4]
        # build unreal asset import directory
        unrealMeshImportPath = "/Game/01_Assets/{}".format(publishDir)
        unrealMeshImportPath = "{}/{}/{}/{}".format(
            unrealMeshImportPath, assetName, variantName, versionNumber
        )
        # Get list of FBX files in publish dir and do sanity checks
        fbxList = []
        for fbx in os.listdir(publishedFBXPath):
            if fbx.endswith(".fbx"):
                fbxList.append(fbx)
        if len(fbxList) > 1:
            genUnrealUtils.warningPopup(
                "Found too many FBX files in {} publish directory".format(assetName)
            )
        if len(fbxList) == 0:
            genUnrealUtils.warningPopup(
                "No FBX files found in {} publish directory".format(assetName)
            )
        else:
            FBXAssetPath = publishedFBXPath + fbxList[0]
        # build import task and run it
        importMeshTask = genUnrealImportUtils.buildImportTask(
            FBXAssetPath,
            unrealMeshImportPath,
            genUnrealImportUtils.buildSkeletalMeshImportOptions(),
        )
        importedMesh = genUnrealImportUtils.executeImportTasks([importMeshTask])
        return importedMesh, unrealMeshImportPath

    # Texture importer returns list of imported textures
    def importTextures(
        self, assetPath, variantName, versionNumber, unrealMeshImportPath, assetType
    ):
        TexList = []

        # For now with static meshes we grab all textures from the USD file
        # ideally this will be the solution for all imports but puppets are currently maya only
        if assetType == "Static Mesh":
            publishedUSDPath = "{}/{}/{}/usd/".format(assetPath, variantName, versionNumber)
            usdFile = os.listdir(publishedUSDPath)[0]
            USDShaderDict = getUSDTexturePaths.get_paths(publishedUSDPath + usdFile)

            for shaderName in USDShaderDict:
                textureDict = USDShaderDict.get(shaderName)
                for parameter in parameterList.get("USDPreviewMaterial"):
                    mayaParameterName = (
                        parameterList.get("USDPreviewMaterial").get(parameter).get("mayaParameter")
                    )
                    texture = textureDict.get(mayaParameterName)
                    if texture:
                        print(texture)
                        if texture.endswith(".<UDIM>.png"):
                            globPath = self.udimToGlobalString(texture)
                            print(globPath)
                            for tex in glob.glob(globPath):
                                print(tex)
                                TexList.append(tex)
                        else:
                            TexList.append(texture)

        # Here we will default to hard coding the skeletal mesh textures from the pub dir
        if assetType == "Skeletal Mesh":
            publishedTexPath = "{}/{}/{}/tex/".format(assetPath, variantName, versionNumber)
            for texture in os.listdir(publishedTexPath):
                if texture.endswith(".png"):
                    print(texture)
                    TexList.append(publishedTexPath + texture)

        # split out asset name from directory path
        assetName = assetPath.split("/")[-1]
        # build unreal asset import directory
        unrealTexImportPath = "{}/TEX".format(unrealMeshImportPath)
        unrealMatImportPath = "{}/MAT".format(unrealMeshImportPath)
        # Get list of Texture files in publish dir and do sanity checks

        if len(TexList) == 0:
            unreal.EditorAssetLibrary.make_directory(unrealTexImportPath)
            unreal.EditorAssetLibrary.make_directory(unrealMatImportPath)
            importedTextures = None
        else:
            texImportTaskList = []
            for sortedTexture in TexList:
                sortedTexturePath = sortedTexture
                # build import task and run it
                importMeshTask = genUnrealImportUtils.buildImportTask(
                    sortedTexturePath,
                    unrealTexImportPath,
                )
                texImportTaskList.append(importMeshTask)
            importedTextures = genUnrealImportUtils.executeImportTasks(texImportTaskList)
        return importedTextures

    def assignMaterialInstanceToMesh(
        self, importedMesh, unrealMeshImportPath, importedTextures, assetType
    ):
        assetTools = unreal.AssetToolsHelpers.get_asset_tools()
        unrealEAL = unreal.EditorAssetLibrary()
        # load imported mesh
        importedMesh = importedMesh[0].split(".")[0]
        loadedImportedMesh = unrealEAL.load_asset(importedMesh)
        # hard coded path to parent material
        loadedMasterMaterial = unrealEAL.load_asset(
            "/Game/03_Shared/MasterMaterials/M_BaseMaterial_Standard_VT"
        )
        # build unreal material import folder
        unrealMatImportPath = "{}/MAT".format(unrealMeshImportPath)
        # get all assets in folder path
        loadedTexList = []
        materialInstances = []
        if importedTextures != None:
            for texturePath in importedTextures:
                # clean up asset path
                texturePath = texturePath.split(".")[0]
                # identify newly import assets
                # load assets, located file import path, and compare to file import paths passed in from import script.
                loadedTexture = unrealEAL.load_asset(texturePath)
                loadedTexList.append(loadedTexture)

        if assetType == "Static Mesh":
            materialTypeFunction = loadedImportedMesh.static_materials
        if assetType == "Skeletal Mesh":
            materialTypeFunction = loadedImportedMesh.materials
            material_array = unreal.Array(unreal.SkeletalMaterial)

        for material in materialTypeFunction:
            # get the index of the current static material for later
            index = materialTypeFunction.index(material)
            # Adjust material name
            newMatName = "MI_" + str(material.material_slot_name).split("_", 1)[1]
            # create new material instance
            materialInstance = assetTools.create_asset(
                newMatName,
                unrealMatImportPath,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew(),
            )
            materialInstances.append(materialInstance)
            # set parent material
            materialInstance.set_editor_property("parent", loadedMasterMaterial)
            # assign new material instance to correct material slot
            if assetType == "Static Mesh":
                loadedImportedMesh.set_material(index, materialInstance)
            if assetType == "Skeletal Mesh":
                materials_to_change = {str(material.material_slot_name): materialInstance}
                new_sk_material = unreal.SkeletalMaterial()

                slot_name = material.get_editor_property("material_slot_name")
                material_interface = material.get_editor_property("material_interface")

                if materials_to_change.get(str(slot_name)):
                    material_interface = materials_to_change[str(slot_name)]

                new_sk_material.set_editor_property("material_slot_name", slot_name)
                new_sk_material.set_editor_property("material_interface", material_interface)

                material_array.append(new_sk_material)

            # iterate over textures
            if len(loadedTexList) != 0:
                for texture in loadedTexList:
                    # Loop over the USD shader dictionary and apply all textures to the correct shader/parameter
                    # identify textures associated with asset by naming convention
                    if str(material.material_slot_name) in texture.get_name():
                        # get parameter name from texture name
                        parameterName = texture.get_name().split("_")[-1]
                        # Set the utility maps to linear
                        if parameterName in ("AO", "Metallic", "Roughness"):
                            texture.set_editor_property("srgb", 0)
                        # turn on texture for material instance
                        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                            materialInstance,
                            "use{}Texture".format(parameterName),
                            True,
                        )
                        # set up material instance parameter
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                            materialInstance, parameterName, texture
                        )
            else:
                # turn on diffuse for material instance if no textures found
                unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                    materialInstance,
                    "use{}Texture".format("Diffuse"),
                    True,
                )
        # set new material/textures
        if assetType == "Skeletal Mesh":
            loadedImportedMesh.set_editor_property("materials", material_array)
            materialTypeFunction = loadedImportedMesh.materials
        # save all new assets
        newAssets = [loadedTexList, materialInstances, [loadedImportedMesh]]
        if assetType == "Skeletal Mesh":
            # Get the skeleton and physics asset associated with the skeletal mesh
            physicsAsset = loadedImportedMesh.get_editor_property("physics_asset")
            skeletonAsset = loadedImportedMesh.get_editor_property("skeleton")
            newAssets.append([physicsAsset])
            newAssets.append([skeletonAsset])
        for list in newAssets:
            for asset in list:
                assetNameClean = asset.get_path_name().split(".")[0]
                unreal.EditorAssetLibrary.save_asset(assetNameClean)

    def updateVerNumOnVarChange(self, row):
        # look up set Dec path from table
        setDecPath = self.tableWidget.item(row, 0)
        setDecPath = setDecPath.text()
        assetName = setDecPath.split("/")[-1]
        # look up corresponding variant name from table
        setDecVariant = self.tableWidget.cellWidget(row, 1)
        setDecVariant = setDecVariant.currentText()
        # look up corresponding asset type from table
        setDecCurrentVersion = self.tableWidget.cellWidget(row, 2)

        setDecCurrentVersion.clear()
        versionList = []
        # get list of versions from path dir
        for versionFolder in os.listdir(setDecPath + "/" + setDecVariant):
            versionList.append(versionFolder)
        setDecCurrentVersion.addItems(versionList)
        setDecCurrentVersion.setCurrentIndex(len(versionList) - 1)

        print("Variant changed to {}/{} finding latest versions".format(assetName, setDecVariant))

    def udimToGlobalString(self, path):
        if path is None:
            return path

        # If any of the patterns, convert the pattern
        patterns = {
            "<udim>": "<udim>",
            "<tile>": "<tile>",
            "<uvtile>": "<uvtile>",
            "#": "#",
            "u<u>_v<v>": "<u>|<v>",
            "<frame0": "<frame0\d+>",
            "<f>": "<f>",
        }

        lower = path.lower()
        has_pattern = False
        for pattern, regex_pattern in patterns.items():
            if pattern in lower:
                path = re.sub(regex_pattern, "*", path, flags=re.IGNORECASE)
                has_pattern = True

        if has_pattern:
            return path

        base = os.path.basename(path)
        matches = list(re.finditer(r"\d+", base))
        if matches:
            match = matches[-1]
            new_base = "{0}*{1}".format(base[: match.start()], base[match.end() :])
            head = os.path.dirname(path)
            return os.path.join(head, new_base)
        else:
            return path


# load UI
def openWindow():
    if QtWidgets.QApplication.instance():
        # Id any current instances of tool and destroy
        for win in QtWidgets.QApplication.allWindows():
            print(win.objectName())
            if "Import Unreal Assets" in win.objectName():
                win.destroy()
    else:
        QtWidgets.QApplication(sys.argv)
    # load UI into QApp instance
    MainWindow.window = MainWindow()
    MainWindow.window.show()
    unreal.parent_external_window_to_slate(MainWindow.window.winId())
