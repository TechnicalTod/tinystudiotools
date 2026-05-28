# Test the full import chain that the UI actually uses
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_src_path = Path(__file__).resolve().parent / "src"
if str(tunnel_src_path) not in sys.path:
    sys.path.insert(0, str(tunnel_src_path))

print("=== FULL IMPORT CHAIN TEST ===")

# Test 1: Create the app environment (like the UI does)
print("\n1. Testing app environment setup...")
try:
    from configuration.config_models import AppEnvironment

    environment = AppEnvironment()

    # Need to detect applications first
    environment.detect_all_applications()

    print(f"✅ Environment created")
    print(f"   Active app: {environment.get_active_application().value}")
    print(f"   Maya ready: {environment.get_active_capabilities().maya_import_ready}")
except Exception as e:
    print(f"❌ Environment setup failed: {e}")
    import traceback

    print(f"   Traceback: {traceback.format_exc()}")
    exit()

# Test 2: Create the main application (like TunnelUI does)
print("\n2. Testing TunnelUI application creation...")
try:
    from application import TunnelUIApplication

    app = TunnelUIApplication()
    print(f"✅ TunnelUI app created")
    print(f"   Maya service available: {app.get_maya_import_service() is not None}")
except Exception as e:
    print(f"❌ TunnelUI app creation failed: {e}")
    exit()

# Test 3: Get the Maya import service (the one the UI calls)
print("\n3. Testing Maya import service...")
try:
    maya_service = app.get_maya_import_service()
    if maya_service:
        print(f"✅ Maya import service obtained: {type(maya_service)}")
    else:
        print("❌ Maya import service is None")
        exit()
except Exception as e:
    print(f"❌ Maya service access failed: {e}")
    exit()

# Test 4: Test the import method the UI actually calls
print("\n4. Testing the UI import method...")
try:
    # This is what the UI calls: maya_service.import_asset()
    # Let's test with a fake asset to see if it handles errors gracefully

    print("Testing import_asset method with fake data...")

    # Create a minimal asset data structure
    fake_asset_data = {"id": "test_asset", "name": "Test Asset", "type": "3d"}

    # Try the import (should fail gracefully)
    result = maya_service.import_asset("fake_asset_id", fake_asset_data)
    print(f"✅ Import method called successfully: {result}")

except Exception as e:
    print(f"❌ Import method failed: {e}")
    print(f"   Error type: {type(e)}")
    import traceback

    print(f"   Traceback: {traceback.format_exc()}")

print("\n=== FULL IMPORT CHAIN TEST COMPLETE ===")
