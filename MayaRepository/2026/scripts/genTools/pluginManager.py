import os
from PySide6 import QtGui, QtWidgets, QtCore
import maya.cmds as mc
import mayaFilePaths

WINDOW = None


def getPluginLoaded(plugin):

    return mc.pluginInfo(plugin, q=True, loaded=True)


def getPluginAutoLoad(plugin):

    return mc.pluginInfo(plugin, q=True, autoload=True)


def getAllPluginPaths(existingOnly=True):

    allPaths = os.environ.get("MAYA_PLUG_IN_PATH")
    allPaths = allPaths.split(";") if allPaths else None
    if existingOnly:
        return [i for i in allPaths if os.path.exists(i)]
    else:
        return allPaths


def getPluginsforPath(path):

    fileFilters = [".py", ".so", ".mll"]  # filter by these file types

    if os.path.exists(path):
        pluginFiles = os.listdir(path)
    else:
        return None

    plugins = [i for i in pluginFiles if any(j for j in fileFilters if i.endswith(j))]
    plugins = [i for i in plugins if not "__" in i]
    return plugins or None


def getAllPluginsAndPluginPaths():

    output = dict()

    for path in getAllPluginPaths():
        plugins = getPluginsforPath(path)
        if plugins:
            output[path] = plugins
        else:
            output[path] = None

    return output


class MainWindow(QtWidgets.QWidget):

    def __init__(self):

        QtWidgets.QWidget.__init__(self)

        self.setGeometry(100, 100, 700, 650)
        self.setWindowTitle("Plugin Manager")
        self.centralLayout = QtWidgets.QVBoxLayout(self)

        self.filterBox = FilterBox()
        self.filterBox.editingFinished.connect(self.filterBoxCallback)
        self.centralLayout.addWidget(self.filterBox)

        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.centralLayout.addWidget(self.scrollArea)

        self.pluginsArea = PluginContents()
        self.scrollArea.setWidget(self.pluginsArea)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        button = QtWidgets.QPushButton()
        button.setText("Browse")
        button.released.connect(self.browseButtonCallback)
        self.horizontalLayout.addWidget(button)

        button = QtWidgets.QPushButton()
        button.setText("Refresh")
        button.released.connect(self.refreshButtonCallback)
        self.horizontalLayout.addWidget(button)

        button = QtWidgets.QPushButton()
        button.setText("Close")
        button.released.connect(self.closeButtonCallback)
        self.horizontalLayout.addWidget(button)

        self.centralLayout.addLayout(self.horizontalLayout)

    def browseButtonCallback(self):

        fileTypeMsg = None
        msg = ""
        default = ""
        fileName, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(
            None, msg, default, fileTypeMsg
        )
        if fileName:
            mc.loadPlugin(fileName)

    def refreshButtonCallback(self):

        self.pluginsArea = None
        self.pluginsArea = PluginContents()
        self.scrollArea.setWidget(None)
        self.scrollArea.setWidget(self.pluginsArea)

    def closeButtonCallback(self):

        self.close()

    def filterBoxCallback(self):

        text = self.filterBox.editBox.text()

        if self.filterBox.modeCheckboxClicked:
            self.pluginsArea.filterWidgets(textFilter=text, includeCommandsInFilter=True)
        else:
            self.pluginsArea.filterWidgets(textFilter=text, includeCommandsInFilter=False)


class PluginContents(QtWidgets.QWidget):

    def __init__(self):

        QtWidgets.QWidget.__init__(self)

        self.centralLayout = QtWidgets.QVBoxLayout(self)

        self.pluginWidgets = []
        self.groupBoxes = []

        for pluginPath, plugins in getAllPluginsAndPluginPaths().items():

            # Add Groups
            groupBox = QtWidgets.QGroupBox(self)
            groupBox.setTitle(str(pluginPath))
            groupBoxLayout = QtWidgets.QVBoxLayout(groupBox)
            self.centralLayout.addWidget(groupBox)

            groupBox.pluginItems = []

            if not plugins:
                self.groupBoxes.append(groupBox)
                continue

            for pluginName in plugins:

                # Add Plugin Widgets
                pluginWidget = PluginItem(str(pluginName), pluginName)
                pluginWidget.pluginName = pluginName
                self.pluginWidgets.append(pluginWidget)
                groupBox.pluginItems.append(pluginWidget)
                groupBoxLayout.addWidget(pluginWidget)

            self.groupBoxes.append(groupBox)

        spacerItem = QtWidgets.QSpacerItem(
            20, 122, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.centralLayout.addItem(spacerItem)

    def showAll(self):

        for groupBox in self.groupBoxes:
            groupBox.setVisible(True)

        for pluginWidget in self.pluginWidgets:
            pluginWidget.setVisible(True)

    def hideUnusedGroupBoxes(self):

        for groupBox in self.groupBoxes:

            if all(i.isHidden() for i in groupBox.pluginItems):
                groupBox.setVisible(False)
            else:
                groupBox.setVisible(True)

    def filterByPluginName(self, textFilter):

        for pluginWidget in self.pluginWidgets:

            if str(textFilter).lower() in str(pluginWidget.pluginName).lower():
                pluginWidget.setVisible(True)
            else:
                pluginWidget.setVisible(False)

    def filterByCommandsAndNodes(self, textFilter):

        for pluginWidget in self.pluginWidgets:

            pluginName = pluginWidget.pluginName

            if getPluginLoaded(pluginName):

                commands = mc.pluginInfo(pluginName, query=True, command=True) or []
                tools = mc.pluginInfo(pluginName, query=True, tool=True) or []
                dependNodes = mc.pluginInfo(pluginName, query=True, dependNode=True) or []

                filters = commands + tools + dependNodes

                if any([i for i in filters if textFilter.lower() in i.lower()]):
                    pluginWidget.setVisible(True)
                else:
                    pluginWidget.setVisible(False)

            else:
                pluginWidget.setVisible(False)

    def filterWidgets(self, textFilter, includeCommandsInFilter=False):

        if not textFilter:

            self.showAll()

        else:

            if not includeCommandsInFilter:

                self.filterByPluginName(textFilter)
                self.hideUnusedGroupBoxes()

            else:

                self.filterByCommandsAndNodes(textFilter)
                self.hideUnusedGroupBoxes()


class FilterBox(QtWidgets.QWidget):

    editingFinished = QtCore.Signal()
    modeCheckboxClicked = False

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.label = QtWidgets.QLabel(self)
        self.label.setText("Filter")
        self.horizontalLayout.addWidget(self.label)

        # EditBox
        self.editBox = QtWidgets.QLineEdit(self)
        self.editBox.editingFinished.connect(self.editingFinished)
        self.horizontalLayout.addWidget(self.editBox)

        # Checkbox
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setText("Filter for Commands or Nodes")
        self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.checkBoxClickedCallback)
        self.horizontalLayout.addWidget(self.checkbox)

    def checkBoxClickedCallback(self):

        if self.checkbox.isChecked():
            self.modeCheckboxClicked = True
        else:
            self.modeCheckboxClicked = False


class PluginItem(QtWidgets.QWidget):

    def __init__(self, label="pluginName.so", plugin=None):

        QtWidgets.QWidget.__init__(self)

        # plugin name
        self.plugin = plugin

        # self.fullPluginPath=fullPluginPath
        loaded = getPluginLoaded(plugin)
        autoLoad = getPluginAutoLoad(plugin)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.label = QtWidgets.QLabel(self)
        self.label.setText(label)
        self.horizontalLayout.addWidget(self.label)

        # Spacer
        spacerItem = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout.addItem(spacerItem)

        # Loaded Checkbox
        self.loadedCheckbox = QtWidgets.QCheckBox()
        self.loadedCheckbox.setText("Loaded")
        self.loadedCheckbox.setChecked(loaded)
        self.loadedCheckbox.stateChanged.connect(self.loadedCheckboxCallback)
        self.horizontalLayout.addWidget(self.loadedCheckbox)

        # AutoLoad Checkbox
        self.autoLoadCheckbox = QtWidgets.QCheckBox()
        self.autoLoadCheckbox.setText("Auto Load")
        self.autoLoadCheckbox.setChecked(autoLoad)
        self.autoLoadCheckbox.stateChanged.connect(self.autoLoadCheckboxCallback)
        self.horizontalLayout.addWidget(self.autoLoadCheckbox)

        # Plugin Info Button
        self.infoButton = QtWidgets.QPushButton()
        self.infoButton.setText("info")
        self.infoButton.released.connect(self.infoButtonCallback)
        if not loaded:
            self.infoButton.setEnabled(False)
        self.horizontalLayout.addWidget(self.infoButton)

    def loadedCheckboxCallback(self):

        if self.loadedCheckbox.isChecked():
            mc.loadPlugin(self.plugin)
            if not getPluginLoaded(self.plugin):

                self.loadedCheckbox.setChecked(False)
                # raise RuntimeError ('Problem loading plug-in: ' + self.plugin)
        else:
            mc.unloadPlugin(self.plugin)
            # if getPluginLoaded(self.plugin):
            # raise RuntimeError ('Problem unloading plug-in: ' + self.plugin)

        if self.loadedCheckbox.isChecked():
            self.infoButton.setEnabled(True)
        else:
            self.infoButton.setEnabled(False)

    def autoLoadCheckboxCallback(self):

        value = self.autoLoadCheckbox.isChecked()
        if value:
            if not self.loadedCheckbox.isChecked():
                self.loadedCheckbox.setChecked(True)
                if not getPluginLoaded(self.plugin):
                    self.autoLoadCheckbox.setChecked(False)
            else:
                mc.pluginInfo(self.plugin, autoload=True, edit=True)

        else:
            mc.pluginInfo(self.plugin, autoload=False, edit=True)

    def infoButtonCallback(self):

        name = mc.pluginInfo(self.plugin, query=True, name=True)
        path = mc.pluginInfo(self.plugin, query=True, path=True)
        vendor = mc.pluginInfo(self.plugin, query=True, vendor=True)
        version = mc.pluginInfo(self.plugin, query=True, version=True)
        apiVersion = mc.pluginInfo(self.plugin, query=True, apiVersion=True)
        # unloadOk = mc.pluginInfo(self.plugin, query=True, unloadOk=True)
        command = mc.pluginInfo(self.plugin, query=True, command=True)
        tool = mc.pluginInfo(self.plugin, query=True, tool=True)
        dependNode = mc.pluginInfo(self.plugin, query=True, dependNode=True)
        dependNodeId = mc.pluginInfo(self.plugin, query=True, dependNodeId=True)
        data = mc.pluginInfo(self.plugin, query=True, data=True)
        translator = mc.pluginInfo(self.plugin, query=True, translator=True)
        iksolver = mc.pluginInfo(self.plugin, query=True, iksolver=True)
        device = mc.pluginInfo(self.plugin, query=True, device=True)
        dragAndDropBehavior = mc.pluginInfo(self.plugin, query=True, dragAndDropBehavior=True)
        userNamed = mc.pluginInfo(self.plugin, query=True, userNamed=True)
        serviceDescriptions = mc.pluginInfo(self.plugin, query=True, serviceDescriptions=True)

        text = ""
        text += "Name:\n{0}\n\n".format(name)
        text += "Path:\n{0}\n\n".format(path)
        text += "Vendor:\n{0}\n\n".format(vendor)
        text += "Version:\n{0}\n\n".format(version)
        text += "Api Version:\n{0}\n\n".format(apiVersion)
        if command:
            text += "Command(s):\n{0}\n\n".format("\n".join(command))
        if tool:
            text += "Tool(s):\n{0}\n\n".format("\n".join(tool))
        if dependNode:
            text += "Dependency Nodes(s):\n{0}\n\n".format("\n".join(dependNode))

        title = name + " Information"
        t = TextOutputForm(parent=self, text=text, width=500, height=500, title=title)
        t.show()


class TextOutputForm(QtWidgets.QDialog):

    valueChanged = QtCore.Signal(float)

    def __init__(self, parent=None, text="", width=700, height=800, title="Information"):

        QtWidgets.QDialog.__init__(self, parent)

        text = self.formatText(text)

        self.setWindowTitle(title)

        self.resize(width, height)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)

        self.plainTextEdit = QtWidgets.QPlainTextEdit(self)
        # self.plainTextEdit = MayaDropableQPlainTextEdit(self)

        self.plainTextEdit.setPlainText(text)
        self.plainTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.plainTextEdit)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)

        okButton = QtWidgets.QDialogButtonBox.Ok
        self.buttonBox.setStandardButtons(okButton)
        copyButton = self.buttonBox.addButton("Copy", QtWidgets.QDialogButtonBox.ActionRole)

        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)

        copyButton.clicked.connect(self.copyTextAction)

    def copyTextAction(self):

        QtWidgets.QApplication.clipboard().setText(self.plainTextEdit.toPlainText())
        QtWidgets.QApplication.clipboard().setText(
            self.plainTextEdit.toPlainText(), QtGui.QClipboard.Selection
        )

    def formatText(self, text):

        if isinstance(text, str):
            return str(text)
        if isinstance(text, list):
            return "\n".join([str(i) for i in text])
        return str(text)


def launch():
    global win
    win = MainWindow()
    win.raise_()
    win.activateWindow()
    win.show()
