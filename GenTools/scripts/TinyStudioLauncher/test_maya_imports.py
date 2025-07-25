"""
Test script to check if Maya can import pymel

This script should be run from within Maya to verify that pymel can be imported.
"""

import sys
import os
import traceback


def test_imports():
    """Test importing key modules needed for Maya tools"""

    print("\n===== Testing Maya Module Imports =====\n")

    # Print Python environment info
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"PYTHONPATH:")
    for path in sys.path:
        print(f"  - {path}")

    # Test importing key modules
    modules_to_test = ["maya.cmds", "pymel.core", "numpy"]

    for module in modules_to_test:
        try:
            print(f"\nAttempting to import {module}...")
            __import__(module)
            print(f"✓ Successfully imported {module}")
        except ImportError as e:
            print(f"✗ Failed to import {module}: {e}")
            print("\nTraceback:")
            traceback.print_exc()

    print("\n===== Environment Variables =====\n")
    # Print key environment variables
    env_vars = [
        "MAYA_APP_DIR",
        "MAYA_SCRIPT_PATH",
        "PYTHONPATH",
        "MAYA_MODULE_PATH",
        "MAYA_PLUG_IN_PATH",
    ]

    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"{var}:")
            for path in value.split(os.pathsep):
                print(f"  - {path}")
        else:
            print(f"{var}: Not set")

    print("\n===== Test Complete =====\n")


# Run the test when executed in Maya
if __name__ == "__main__":
    # Check if running in Maya
    try:
        import maya.cmds

        test_imports()
    except ImportError:
        print("This script should be run from within Maya.")
