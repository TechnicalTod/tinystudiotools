#!/usr/bin/env python3
"""
Quick Maya Debug Script - Run this in Maya Script Editor

This script will quickly debug why Maya import services aren't initializing.
"""

import sys
from pathlib import Path

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

print("=== Quick Maya Debug - TunnelUI ===\n")

try:
    # Step 1: Basic Maya detection
    print("1. Basic Maya Detection:")
    try:
        import maya.cmds as cmds

        maya_version = cmds.about(version=True)
        print("   SUCCESS: Maya detected: " + str(maya_version))
    except ImportError:
        print("   ERROR: Maya NOT detected - not in Maya environment")
        sys.exit(1)

    # Step 2: Environment Detection
    print("\n2. Environment Detection:")
    from configuration.config_models import AppEnvironment

    environment = AppEnvironment()
    available_apps = environment.detect_all_applications()
    active_app = environment.get_active_application()
    active_capabilities = environment.get_active_capabilities()

    print("   Available apps: " + str([app.value for app in available_apps.keys()]))
    print("   Active app: " + str(active_app.value))
    print("   Active capabilities: " + str(active_capabilities.name))

    if hasattr(active_capabilities, "maya_import_ready"):
        print("   Maya import ready: " + str(active_capabilities.maya_import_ready))
    else:
        print("   ERROR: maya_import_ready attribute missing!")

    # Step 3: Test Application Initialization
    print("\n3. Application Initialization:")
    try:
        from application import TunnelUIApplication

        app = TunnelUIApplication()
        print("   App created: " + str(app is not None))
        print("   Maya service: " + str(app.maya_import_service))
        print("   Asset service: " + str(app.asset_service))
    except Exception as init_error:
        print("   ERROR during app initialization: " + str(init_error))
        import traceback

        traceback.print_exc()
        raise

    # Step 4: Check Import Capabilities
    print("\n4. Import Capabilities:")
    capabilities = app.asset_service.get_import_capabilities()
    print("   Capabilities: " + str(capabilities))
    maya_available = capabilities.get("maya_available", False)
    print("   Maya available: " + str(maya_available))

    if maya_available:
        print("\nSUCCESS: Maya import services are working!")
    else:
        print("\nPROBLEM: Maya services not initialized")
        print("   This is why you're seeing the error dialog.")

except Exception as e:
    print("\nERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
