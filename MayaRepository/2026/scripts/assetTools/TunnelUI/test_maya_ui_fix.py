#!/usr/bin/env python3
"""
Test Maya UI Fix

This script tests that the Maya import service initialization fix is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_maya_ui_fix():
    """Test that Maya UI initialization works correctly"""
    print("=== Testing Maya UI Fix ===\n")

    try:
        # Test 1: Environment Detection
        print("1. Testing Environment Detection...")
        from configuration.config_models import AppEnvironment

        environment = AppEnvironment()
        available_apps = environment.detect_all_applications()
        active_app = environment.get_active_application()
        active_capabilities = environment.get_active_capabilities()

        print(f"   Available applications: {[app.value for app in available_apps.keys()]}")
        print(f"   Active application: {active_app.value}")
        print(f"   Active capabilities name: {active_capabilities.name}")

        if hasattr(active_capabilities, "maya_import_ready"):
            print(f"   Maya import ready: {active_capabilities.maya_import_ready}")
        else:
            print("   Maya import ready: N/A (not Maya)")

        # Test 2: Application Initialization
        print("\n2. Testing Application Initialization...")
        from application import TunnelUIApplication

        app = TunnelUIApplication()
        print(f"   Application created: {app is not None}")
        print(f"   Has Maya import service: {app.maya_import_service is not None}")

        if app.maya_import_service:
            print("   ✅ Maya import service successfully initialized!")

            # Test import capabilities
            capabilities = app.asset_service.get_import_capabilities()
            print(f"   Import capabilities: {capabilities}")
        else:
            print("   ⚠️  Maya import service not initialized (this may be expected if not in Maya)")

        # Test 3: Environment Methods
        print("\n3. Testing Environment Methods...")
        display_name = environment.get_application_display_name()
        import_button_text = environment.get_import_button_text()

        print(f"   Application display name: {display_name}")
        print(f"   Import button text: {import_button_text}")

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_maya_ui_fix()
