import os

# Windows username
windowsUserName = os.environ.get('USERNAME')

# Directory for artist projects
userProjectsDir = 'C:/Users/{}/Documents/maya/projects/'.format(windowsUserName)

# Script folder path
baseScriptsPath = os.getenv('SAGA_MAYA_SCRIPT_PATH')
baseScriptsPath = baseScriptsPath.replace('\\', '/')

# Maya base directory
baseMayaAppPath = os.getenv('MAYA_APP_BASE_PATH')

# Paths for Maya icons
mayaShelfIconPath = baseScriptsPath + 'icons/maya/'
mzControlIconPAth = baseScriptsPath + 'icons/mz_icons/'

# Paths for Maya plugins
mayaPluginDir01 = baseMayaAppPath + 'plug-ins/fbx/plug-ins/'
mayaPluginDir02 = baseMayaAppPath + 'bin/plug-ins/'

# Downloads folder
downloadsFolder = 'c:/Users/{}/Downloads/'.format(windowsUserName)

# Stylesheet filepath
styleSheetFilepath = baseScriptsPath + 'shared/pyQtStyleSheets/'
