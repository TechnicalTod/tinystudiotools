import os

# Windows username
windowsUserName = os.environ.get("USERNAME")
libDir = os.environ.get("TINYSTUDIO_LIB_DIR")
showDir = os.environ.get("TINYSTUDIO_BASE_SHOW_DIR")

unrealProjectDir = os.environ.get("UNREAL_PROJECT_DIR") or os.environ.get("UE_PROJECT_DIR")

# Directory for artist assets
artistDir = "{}Artist/{}/".format(libDir, windowsUserName) if libDir else None

# Base repo folder
baseScriptsPath = os.getenv("UNREAL_REPO")
baseScriptsPath = baseScriptsPath.replace("\\", "/") if baseScriptsPath else None

# Paths for unreal icons
unrealIconPath = baseScriptsPath + "/icons/" if baseScriptsPath else None

# Downloads folder
downloadsFolder = "c:/Users/{}/Downloads/".format(windowsUserName) if windowsUserName else None

# Stylesheet filepath (canonical: GenTools/pyQtStyleSheets)
styleSheetFilepath = None
try:
    from genTools.studio_python_path import ensure_gen_tools_shared

    ensure_gen_tools_shared()
    from studioFilePaths import styleSheetFilepath
except ImportError:
    pass
