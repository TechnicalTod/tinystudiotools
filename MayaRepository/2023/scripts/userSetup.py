import maya.cmds as mc
from importlib import reload
import warnings
import sys
import os

# Suppress PyMel warnings at the very start of Maya session
# warnings.filterwarnings("ignore")

# Get paths from Maya's environment variables
# maya_script_path = mc.internalVar(userScriptDir=True)
# maya_app_dir = mc.internalVar(userAppDir=True)

# Add paths to Python path
# paths_to_add = [
#    maya_script_path,
#    os.path.join(maya_script_path, "shared"),
#    os.path.join(maya_script_path, "melScripts"),
#    os.path.join(maya_script_path, "tools"),
# ]

# for path in paths_to_add:
#    if path not in sys.path:
#        sys.path.insert(0, path)

# ========================================
# PyMel Maya 2026 Compatibility Fix
# ========================================


def setup_pymel_compatibility():
    """Setup PyMel Maya 2026 compatibility - patches os.path.exists globally"""

    print("Setting up PyMel Maya 2026 compatibility...")

    # Patch os.path.exists to fake Maya 2026 docs existence
    original_exists = os.path.exists

    def patched_exists(path):
        if "Maya2026" in str(path) and "docs" in str(path):
            return True  # Fake that Maya 2026 docs exist
        return original_exists(path)

    os.path.exists = patched_exists
    print("PyMel compatibility patches applied")


# Apply basic compatibility setup
# setup_pymel_compatibility()

# ========================================
# End PyMel Patches
# ========================================

print("SagaTools userSetup.py loaded successfully")


def onStartUp():
    print("Starting SagaTools initialization...")

    try:
        # Import and build the shelf
        import buildSagaShelf

        buildSagaShelf.buildSagaShelf()
        print("Saga Shelf built successfully")
    except Exception as e:
        print(f"Error building Saga Shelf: {e}")

    print("##############################")
    print("##############################")
    print("###  |\/\/\/|  ###############")
    print("###  |      |  #### SAGA #####")
    print("###  |      |  #### PREVIS ###")
    print("###  | (o)(o)  #### SHELF ####")
    print("###  C      _) ###############")
    print("###   | ,___|  #### V1.0 #####")
    print("###   |   /    ###############")
    print("###  /____\    ###############")
    print("### /      \   ###############")
    print("##############################")
    print("##############################")


mc.evalDeferred(onStartUp)
