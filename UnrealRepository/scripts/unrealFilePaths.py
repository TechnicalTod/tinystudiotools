import os

# Windows username and Maya version 
UNREAL_WINDOWSUSERNAME = os.environ.get('USERNAME')

# The following variables should all populate automatically
UNREAL_BASESCRIPTFOLDER = 'X:\\UnrealRepository\\scripts\\'

UNREAL_shelfIconPath = UNREAL_BASESCRIPTFOLDER + 'icons\\'

UNREAL_downloadsFolder = 'c:\\Users\\{}\\Downloads\\'.format(UNREAL_WINDOWSUSERNAME)

UNREAL_styleSheetFilepath = UNREAL_BASESCRIPTFOLDER + 'styleSheets\\'

UNREAL_openFolderIconFilepath = UNREAL_shelfIconPath + "folder.png"