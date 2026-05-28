# Simple ASCII-only crash test for Maya compatibility
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_src_path = Path(__file__).resolve().parent / "src"
if str(tunnel_src_path) not in sys.path:
    sys.path.insert(0, str(tunnel_src_path))

print("=== SIMPLE CRASH TEST ===")

# Test 1: Environment
print("\n1. Testing environment...")
try:
    from configuration.config_models import AppEnvironment

    environment = AppEnvironment()
    environment.detect_all_applications()
    print("SUCCESS: Environment created")
    active_app = environment.get_active_application()
    print("Active app: " + str(active_app.value))
    caps = environment.get_active_capabilities()
    print("Maya ready: " + str(caps.maya_import_ready))
except Exception as e:
    print("ERROR in environment: " + str(e))
    exit()

# Test 2: TunnelUI App
print("\n2. Testing TunnelUI app...")
try:
    from application import TunnelUIApplication

    app = TunnelUIApplication()
    print("SUCCESS: TunnelUI app created")

    # Access maya_import_service as attribute, not method
    maya_service = app.maya_import_service
    if maya_service:
        print("SUCCESS: Maya service found")
        print("Service type: " + str(type(maya_service)))
    else:
        print("ERROR: Maya service is None")
        exit()
except Exception as e:
    print("ERROR in TunnelUI app: " + str(e))
    import traceback

    print("Traceback:")
    traceback.print_exc()
    exit()

# Test 3: Import method
print("\n3. Testing import method...")
try:
    fake_asset_data = {"id": "test_asset", "name": "Test Asset", "type": "3d"}

    result = maya_service.import_asset("fake_asset_id", fake_asset_data)
    print("SUCCESS: Import method called")
    print("Result: " + str(result))

except Exception as e:
    print("ERROR in import: " + str(e))
    import traceback

    print("Traceback:")
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
