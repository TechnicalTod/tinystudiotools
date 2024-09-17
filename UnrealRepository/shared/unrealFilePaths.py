import os

# Windows username and Maya version 
windowsUserName = os.environ.get('USERNAME')
libDir = os.environ.get('SAGA_LIB_DIR')
showDir = os.environ.get('SAGA_SHOW_DIR')

# Directory for artist assets
artistDir = '{}Artist/{}/'.format(libDir, windowsUserName)

# Base repo folder
baseScriptsPath = os.getenv('UNREAL_REPO')

# Paths for unreal icons
unrealIconPath = baseScriptsPath + 'icons/'

# Downloads folder
downloadsFolder = 'c:/Users/{}/Downloads/'.format(windowsUserName)

# Stylesheet filepath
styleSheetFilepath = baseScriptsPath + 'shared/pyQtStyleSheets/'

