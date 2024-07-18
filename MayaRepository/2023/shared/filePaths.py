import os

# Windows username
windowsUserName = os.environ.get('USERNAME')
libDir = os.environ.get('SAGA_LIB_DIR')
showDir = os.environ.get('SAGA_SHOW_DIR')

# Directory for artist assets
artistDir = '{}Artist/{}/'.format(libDir, windowsUserName)

# Script folder path
baseScriptsPath = os.getenv('SAGA_MAYA_SCRIPT_PATH')
baseScriptsPath = baseScriptsPath.replace('\\', '/')

# Maya base directory
baseMayaAppPath = os.getenv('MAYA_APP_BASE_PATH')

# Paths for Maya icons
mayaShelfIconPath = baseScriptsPath + 'icons/'
mzControlIconPAth = baseScriptsPath + 'icons/mz_icons/'

# Paths for Maya plugins
mayaPluginDir01 = baseMayaAppPath + 'plug-ins/fbx/plug-ins/'
mayaPluginDir02 = baseMayaAppPath + 'bin/plug-ins/'

# Downloads folder
downloadsFolder = 'c:/Users/{}/Downloads/'.format(windowsUserName)

# Stylesheet filepath
styleSheetFilepath = baseScriptsPath + 'shared/pyQtStyleSheets/'
