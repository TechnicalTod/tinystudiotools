import os

# Windows username
windowsUserName = os.environ.get("USERNAME")
libDir = os.environ.get("TINYSTUDIO_LIB_DIR")
showDir = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR")

# Directory for artist assets
artistDir = "{}Artist/{}/".format(libDir, windowsUserName) if libDir else None

# Script folder path
baseScriptsPath = os.getenv("MAYA_REPO")
baseScriptsPath = baseScriptsPath.replace("\\", "/") if baseScriptsPath else None

# Maya base directory
baseMayaAppPath = os.getenv("MAYA_APP_BASE_PATH")
baseMayaAppPath = baseMayaAppPath.replace("\\", "/") if baseMayaAppPath else None

# Paths for Maya icons
mayaShelfIconPath = baseScriptsPath + "/icons/" if baseScriptsPath else None
mzControlIconPAth = baseScriptsPath + "/icons/mz_icons/" if baseScriptsPath else None

# Paths for Maya plugins
mayaPluginDir01 = baseMayaAppPath + "plug-ins/fbx/plug-ins/" if baseMayaAppPath else None
mayaPluginDir02 = baseMayaAppPath + "bin/plug-ins/" if baseMayaAppPath else None

# Downloads folder
downloadsFolder = "c:/Users/{}/Downloads/".format(windowsUserName) if windowsUserName else None

# Stylesheet filepath
styleSheetFilepath = baseScriptsPath + "/shared/pyQtStyleSheets/" if baseScriptsPath else None
