# Maya Shelf Button System - Example Tool Updates

This document provides examples of how to update existing tools with the new metadata-driven approach.

## Example 1: Updating the Cubinate Tool

### Before:

```python
def cubinate(objects=None, doTransfer=True, deleteSourceMesh=False, keepHistory=True, smoothCube=0, preScale=0, subdivisionsX=3, subdivisionsY=3, subdivisionsZ=3):
    import maya.cmds as mc

    cubes = []

    objects = objects or mc.ls(sl=True, l=True)

    if not objects:
        raise RuntimeError('No Objects')

    for obj in objects:

        # record the pivot of the object for later
        oldPiv = mc.xform(obj, q=True, ws=True, piv=True)[:3]

        # center the pivot and record the position
        mc.xform(obj, cp=True)
        piv = mc.xform(obj, q=True, ws=True, piv=True)[:3]

        # add a cube at the centered location
        cube = mc.polyCube(n=obj + '_cube', subdivisionsX=subdivisionsX, subdivisionsY=subdivisionsY, subdivisionsZ=subdivisionsZ);
        mc.xform(cube,t = piv)

        # get the name of the transform created and add it to the return list
        cubeTransform = mc.ls(cube, transforms=True)[0]
        cubes.append(cubeTransform)

        # return the objects pivot
        mc.xform(obj, piv=oldPiv, ws=True)

        # record the bounding box of the object
        bounds = mc.xform(obj, bb=True, q=True, ws=True)

        # apply the bounding box to the cube
        sx = abs(bounds[0] - bounds[3])
        sy = abs(bounds[1] - bounds[4])
        sz = abs(bounds[2] - bounds[5])
        mc.setAttr(cubeTransform + ".scaleX", sx + preScale)
        mc.setAttr(cubeTransform + ".scaleY", sy + preScale)
        mc.setAttr(cubeTransform + ".scaleZ", sz + preScale)

        # add a smooth node to the mesh, good for spherical objects, True or False
        if smoothCube:
            mc.polySmooth(cube, dv=smoothCube, kb=False, ksb=False, ch=True)

        # transfer the vertex positions of the cube to the object below, True or False
        if doTransfer:
            mc.transferAttributes(obj, cubeTransform, uvs=0, pos=1, nml=0, spa=0)

        # keep construction history, True or False
        if not keepHistory:
            mc.delete(cube, ch=True)

        # remove the source mesh, True or False
        if deleteSourceMesh:
            if keepHistory and doTransfer:
                print ('WARNING: cannot keep history when deleting source mesh and transfering attributes')
                mc.delete(cube, ch=True)
            mc.delete(obj)

    # select and return the new cube meshes
    mc.select(cubes)
    return cubes
```

### After:

```python
"""
SAGA_TOOL_CONFIG:
{
    "label": "Cubinate",
    "tooltip": "Convert selected objects to cubes",
    "icon": "cubinate.png",
    "category": "modelling",
    "entry_point": "cubinate",
    "shelf_button": true,
    "menu_group": "Tools"
}
"""
def cubinate(objects=None, doTransfer=True, deleteSourceMesh=False, keepHistory=True, smoothCube=0, preScale=0, subdivisionsX=3, subdivisionsY=3, subdivisionsZ=3):
    """
    Convert selected objects to cube representations

    SAGA_TOOL_CONFIG:
    {
        "label": "Cubinate Selected",
        "tooltip": "Convert selected objects to cubes for optimization"
    }
    """
    import maya.cmds as mc

    cubes = []

    objects = objects or mc.ls(sl=True, l=True)

    if not objects:
        raise RuntimeError('No Objects')

    for obj in objects:

        # record the pivot of the object for later
        oldPiv = mc.xform(obj, q=True, ws=True, piv=True)[:3]

        # center the pivot and record the position
        mc.xform(obj, cp=True)
        piv = mc.xform(obj, q=True, ws=True, piv=True)[:3]

        # add a cube at the centered location
        cube = mc.polyCube(n=obj + '_cube', subdivisionsX=subdivisionsX, subdivisionsY=subdivisionsY, subdivisionsZ=subdivisionsZ);
        mc.xform(cube,t = piv)

        # get the name of the transform created and add it to the return list
        cubeTransform = mc.ls(cube, transforms=True)[0]
        cubes.append(cubeTransform)

        # return the objects pivot
        mc.xform(obj, piv=oldPiv, ws=True)

        # record the bounding box of the object
        bounds = mc.xform(obj, bb=True, q=True, ws=True)

        # apply the bounding box to the cube
        sx = abs(bounds[0] - bounds[3])
        sy = abs(bounds[1] - bounds[4])
        sz = abs(bounds[2] - bounds[5])
        mc.setAttr(cubeTransform + ".scaleX", sx + preScale)
        mc.setAttr(cubeTransform + ".scaleY", sy + preScale)
        mc.setAttr(cubeTransform + ".scaleZ", sz + preScale)

        # add a smooth node to the mesh, good for spherical objects, True or False
        if smoothCube:
            mc.polySmooth(cube, dv=smoothCube, kb=False, ksb=False, ch=True)

        # transfer the vertex positions of the cube to the object below, True or False
        if doTransfer:
            mc.transferAttributes(obj, cubeTransform, uvs=0, pos=1, nml=0, spa=0)

        # keep construction history, True or False
        if not keepHistory:
            mc.delete(cube, ch=True)

        # remove the source mesh, True or False
        if deleteSourceMesh:
            if keepHistory and doTransfer:
                print ('WARNING: cannot keep history when deleting source mesh and transfering attributes')
                mc.delete(cube, ch=True)
            mc.delete(obj)

    # select and return the new cube meshes
    mc.select(cubes)
    return cubes
```

## Example 2: Updating the Create Asset Directory Tool

### Before:

```python
import os
import subprocess
from genTools.genUtils import warningPopup
from PySide6 import QtGui, QtWidgets, QtCore
import mayaFilePaths
import maya.OpenMayaUI as OMUI
import shiboken2


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Get Maya's main window
        mayaWin = OMUI.MQtUtil.mainWindow()
        self.mayaWin = shiboken2.wrapInstance(int(mayaWin), QtWidgets.QWidget)

        # Parent your window to Maya's main window
        self.setParent(self.mayaWin)
        self.setWindowFlags(QtCore.Qt.Window)
        self.initUI()

    def initUI(self):
        # window prefs
        self.resize(600, 50)
        self.setWindowTitle('Create asset directories')
        self.setFocus()
        self.style_sheet_file_loc = mayaFilePaths.styleSheetFilepath
        with open("{}/dark.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.center()
        self.show()

        # text field widget
        self.getAssetName = QtWidgets.QLineEdit(self)
        self.getAssetName.setPlaceholderText("Asset Name")

        # button widget
        button = QtWidgets.QPushButton('Create folder structure', self)
        button.clicked.connect(self.makeAssetDir)

        # radio widget
        self.AssetDirRadioButton = QtWidgets.QRadioButton('Asset Directory')
        self.techvisDirRadioButton = QtWidgets.QRadioButton(
            'Techvis Directory')

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.AssetDirRadioButton, 0, 0)
        self.grid.addWidget(self.techvisDirRadioButton, 0, 1)
        self.grid.addWidget(self.getAssetName, 1, 0, 1, 2)
        self.grid.addWidget(button, 2, 0, 1, 2)
        self.AssetDirRadioButton.setChecked(True)
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when button is pressed
    def makeAssetDir(self):
        folderName = None

        if self.AssetDirRadioButton.isChecked():
            folderName = 'assets/'
        if self.techvisDirRadioButton.isChecked():
            folderName = 'techvis/'

        assetname = self.getAssetName.text()

        if not assetname:
            warningPopup('No asset name specified')
        else:
            baseUserDir = mayaFilePaths.artistDir + folderName

            dirList = []

            dirList.append(mayaFilePaths.artistDir)
            dirList.append(baseUserDir)
            dirList.append(baseUserDir + assetname)
            dirList.append(baseUserDir + assetname + '/scenes')
            dirList.append(baseUserDir + assetname + '/sourceimages')
            dirList.append(baseUserDir + assetname + '/sourceimages/ref')
            dirList.append(baseUserDir + assetname + '/sourceimages/textures')
            dirList.append(baseUserDir + assetname + '/tempOBJ')

            print (baseUserDir + assetname)

            for dir in dirList:
                try:
                    os.mkdir(dir)
                except:
                    print ('looks like {0} already exists...skipping'.format(dir))

            fileList = []

            fileList.append(baseUserDir + assetname +
                            '/scenes/{0}_workingMayaFile_V001.ma'.format(assetname))
            fileList.append(baseUserDir + assetname +
                            '/scenes/{0}_workingSubstanceFile_V001.spp'.format(assetname))

            for fileName in fileList:
                with open(fileName, 'a'):
                    os.utime(fileName, None)

# definition to open UI

def launch():
     global win
     win = MainWindow()
     win.raise_()
     win.activateWindow()
     win.show()
```

### After:

```python
"""
SAGA_TOOL_CONFIG:
{
    "label": "Create Asset Directories",
    "tooltip": "Create standardized asset directory structure",
    "icon": "createAssetDir.png",
    "category": "asset",
    "entry_point": "launch",
    "primary": true,
    "shelf_button": true
}
"""
import os
import subprocess
from genTools.genUtils import warningPopup
from PySide6 import QtGui, QtWidgets, QtCore
import mayaFilePaths
import maya.OpenMayaUI as OMUI
import shiboken2


class MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Get Maya's main window
        mayaWin = OMUI.MQtUtil.mainWindow()
        self.mayaWin = shiboken2.wrapInstance(int(mayaWin), QtWidgets.QWidget)

        # Parent your window to Maya's main window
        self.setParent(self.mayaWin)
        self.setWindowFlags(QtCore.Qt.Window)
        self.initUI()

    def initUI(self):
        # window prefs
        self.resize(600, 50)
        self.setWindowTitle('Create asset directories')
        self.setFocus()
        self.style_sheet_file_loc = mayaFilePaths.styleSheetFilepath
        with open("{}/dark.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.center()
        self.show()

        # text field widget
        self.getAssetName = QtWidgets.QLineEdit(self)
        self.getAssetName.setPlaceholderText("Asset Name")

        # button widget
        button = QtWidgets.QPushButton('Create folder structure', self)
        button.clicked.connect(self.makeAssetDir)

        # radio widget
        self.AssetDirRadioButton = QtWidgets.QRadioButton('Asset Directory')
        self.techvisDirRadioButton = QtWidgets.QRadioButton(
            'Techvis Directory')

        # layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to layout
        self.grid.addWidget(self.AssetDirRadioButton, 0, 0)
        self.grid.addWidget(self.techvisDirRadioButton, 0, 1)
        self.grid.addWidget(self.getAssetName, 1, 0, 1, 2)
        self.grid.addWidget(button, 2, 0, 1, 2)
        self.AssetDirRadioButton.setChecked(True)
        self.setLayout(self.grid)

    # definition that sets UI to be created in center (used in window prefs)
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # definition called when button is pressed
    def makeAssetDir(self):
        folderName = None

        if self.AssetDirRadioButton.isChecked():
            folderName = 'assets/'
        if self.techvisDirRadioButton.isChecked():
            folderName = 'techvis/'

        assetname = self.getAssetName.text()

        if not assetname:
            warningPopup('No asset name specified')
        else:
            baseUserDir = mayaFilePaths.artistDir + folderName

            dirList = []

            dirList.append(mayaFilePaths.artistDir)
            dirList.append(baseUserDir)
            dirList.append(baseUserDir + assetname)
            dirList.append(baseUserDir + assetname + '/scenes')
            dirList.append(baseUserDir + assetname + '/sourceimages')
            dirList.append(baseUserDir + assetname + '/sourceimages/ref')
            dirList.append(baseUserDir + assetname + '/sourceimages/textures')
            dirList.append(baseUserDir + assetname + '/tempOBJ')

            print (baseUserDir + assetname)

            for dir in dirList:
                try:
                    os.mkdir(dir)
                except:
                    print ('looks like {0} already exists...skipping'.format(dir))

            fileList = []

            fileList.append(baseUserDir + assetname +
                            '/scenes/{0}_workingMayaFile_V001.ma'.format(assetname))
            fileList.append(baseUserDir + assetname +
                            '/scenes/{0}_workingSubstanceFile_V001.spp'.format(assetname))

            for fileName in fileList:
                with open(fileName, 'a'):
                    os.utime(fileName, None)


def launch():
    """
    Launch the Create Asset Directory UI

    SAGA_TOOL_CONFIG:
    {
        "label": "Create Asset Directories",
        "tooltip": "Create standardized asset directory structure",
        "icon": "createAssetDir.png",
        "category": "asset",
        "shelf_button": true
    }
    """
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()
```

## Example 3: Creating a MEL Command Wrapper Module

### New File: `MayaRepository/2023/scripts/genTools/melWrappers.py`

```python
"""
MEL command wrapper utilities for Maya

SAGA_TOOL_CONFIG:
{
    "category": "utility",
    "label": "MEL Wrappers",
    "tooltip": "Python wrappers for common MEL commands"
}
"""

import maya.mel as mm

def movePivotBA():
    """
    Move pivot from B to A

    SAGA_TOOL_CONFIG:
    {
        "label": "Move Pivot B to A",
        "tooltip": "Move pivot from object B to object A",
        "icon": "movePivotBA.png",
        "category": "transform",
        "shelf_button": true
    }
    """
    mm.eval('movePivotBA();')

def movePivotToOrigin():
    """
    Move pivot to origin

    SAGA_TOOL_CONFIG:
    {
        "label": "Move Pivot To Origin",
        "tooltip": "Move pivot to world origin",
        "icon": "movePivotToOrigin.png",
        "category": "transform",
        "shelf_button": true
    }
    """
    mm.eval('movePivotToOrigin();')

def selectNthEdge():
    """
    Select every Nth edge in edge ring

    SAGA_TOOL_CONFIG:
    {
        "label": "Select Nth Edge",
        "tooltip": "Select every other edge in an edge ring",
        "icon": "selectNthEdge.png",
        "category": "selection",
        "shelf_button": false,
        "menu_group": "Selection"
    }
    """
    mm.eval('polySelectEdgesEveryN "edgeRing" 2;')

def detachDuplicateComponents():
    """
    Detach and duplicate selected components

    SAGA_TOOL_CONFIG:
    {
        "label": "Duplicate Components",
        "tooltip": "Detach and duplicate selected components",
        "icon": "duplicateComponents.png",
        "category": "modelling",
        "shelf_button": false,
        "menu_group": "Components"
    }
    """
    mm.eval('detachDuplicateComponents();')

def sortOutliner():
    """
    Sort outliner alphabetically

    SAGA_TOOL_CONFIG:
    {
        "label": "Sort Outliner",
        "tooltip": "Sort outliner alphabetically",
        "icon": "sortOutliner.png",
        "category": "ui",
        "shelf_button": false,
        "menu_group": "UI"
    }
    """
    mm.eval('sortOutliner();')

def cometRename():
    """
    Launch Comet rename tool

    SAGA_TOOL_CONFIG:
    {
        "label": "Comet Rename",
        "tooltip": "Launch Comet rename tool",
        "icon": "cometRename.png",
        "category": "utility",
        "shelf_button": false,
        "menu_group": "Utilities"
    }
    """
    mm.eval('cometRename();')

def randomVertCol():
    """
    Apply random vertex colors to selection

    SAGA_TOOL_CONFIG:
    {
        "label": "Random Vertex Color",
        "tooltip": "Apply random vertex colors to selection",
        "icon": "randomVertCol.png",
        "category": "shading",
        "shelf_button": false,
        "menu_group": "Vertex Colors"
    }
    """
    mm.eval('randomVertCol();')

def doraSkinWeight():
    """
    Launch Dora Skin Weight tool

    SAGA_TOOL_CONFIG:
    {
        "label": "Dora Skin Weight",
        "tooltip": "Launch Dora Skin Weight tool",
        "icon": "doraSkinWeight.png",
        "category": "rigging",
        "shelf_button": false,
        "menu_group": "Skinning"
    }
    """
    mm.eval('DoraSkinWeightImpExp();')
```

## Example 4: Creating a UI Utilities Module

### New File: `MayaRepository/2023/scripts/genTools/uiUtils.py`

```python
"""
UI utility functions for Maya

SAGA_TOOL_CONFIG:
{
    "category": "utility",
    "label": "UI Utilities",
    "tooltip": "Utility functions for Maya UI operations"
}
"""

import maya.cmds as mc
import maya.mel as mm

def openUVEditor():
    """
    Open UV Editor panel

    SAGA_TOOL_CONFIG:
    {
        "label": "UV Editor",
        "tooltip": "Open the UV Editor panel",
        "icon": "UVTools.png",
        "category": "uv",
        "primary": true,
        "shelf_button": true
    }
    """
    for panel in mc.getPanel(sty="polyTexturePlacementPanel") or []:
        mc.scriptedPanel(panel, e=True, to=True)

def toggleSelectByAngle():
    """
    Toggle select faces by angle constraint

    SAGA_TOOL_CONFIG:
    {
        "label": "Select by Angle",
        "tooltip": "Toggle selection by angle constraint",
        "icon": "selectByAngle.png",
        "category": "selection",
        "shelf_button": false,
        "menu_group": "Selection"
    }
    """
    if not mc.polySelectConstraint(query=True, ap=True) is True:
        mc.polySelectConstraint(ap=True, at=38)
    else:
        mc.polySelectConstraint(ap=False, at=0)

def copyCurrentScenePath():
    """
    Copy current Maya scene path to clipboard

    SAGA_TOOL_CONFIG:
    {
        "label": "Copy Scene Path",
        "tooltip": "Copy current scene path to clipboard",
        "icon": "clipboard.png",
        "category": "utility",
        "shelf_button": false,
        "menu_group": "Utilities"
    }
    """
    from PySide6 import QtGui
    maya_file = mc.file(sceneName=True, q=True)
    clip = QtGui.QClipboard()
    clip.setText(str(maya_file))
```

## Key Points for Updating Tools

1. **Module Docstring Metadata**:

   - Add `SAGA_TOOL_CONFIG` to the module docstring for module-level configuration
   - Specify category and other module-wide settings

2. **Function Docstring Metadata**:

   - Add `SAGA_TOOL_CONFIG` to each function that should be discovered as a tool
   - Include required metadata: label, tooltip, icon, category
   - Add optional metadata as needed: entry_point, shelf_button, menu_group, primary

3. **Metadata Location Options**:

   - **Module-level**: For settings that apply to all tools in the module
   - **Function-level**: For settings specific to individual tools
   - Both can be used together, with function-level settings overriding module-level

4. **Multiple Tool Definitions**:

   - A single file can contain multiple tool definitions
   - Each function with a `SAGA_TOOL_CONFIG` block will be discovered as a separate tool

5. **Organization Best Practices**:
   - Group related tools in logical modules
   - Use consistent naming conventions
   - Use the category field to control shelf organization
   - Use the menu_group field to organize dropdown menus
