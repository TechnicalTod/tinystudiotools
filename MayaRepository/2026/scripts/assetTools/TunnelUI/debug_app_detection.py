# Debug Application Detection - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_src_path = Path(__file__).resolve().parent / "src"
if str(tunnel_src_path) not in sys.path:
    sys.path.insert(0, str(tunnel_src_path))

print("=== DEBUG APPLICATION DETECTION ===")

try:
    # 1. Test environment detection
    print("\n1. Testing Environment Detection:")
    from configuration.config_models import AppEnvironment, DCCApplication

    env = AppEnvironment()
    env.detect_all_applications()
    active_app = env.get_active_application()
    active_caps = env.get_active_capabilities()

    print(f"   Active app: {active_app}")
    print(f"   Active app value: {active_app.value}")
    print(f"   Active app name: {active_caps.name if active_caps else 'None'}")
    print(f"   Is Maya? {active_app == DCCApplication.MAYA}")
    print(f"   Is Standalone? {active_app == DCCApplication.STANDALONE}")

    # 2. Test the exact logic from ImagePreviewDialog.import_asset()
    print("\n2. Testing ImagePreviewDialog Logic:")
    app_name = active_app.value
    print(f"   app_name = active_app.value = '{app_name}'")

    if app_name == "standalone":
        print("   -> Would call _open_zip_file() ❌")
    elif app_name == "maya":
        print("   -> Would call _import_to_maya() ✅")
    elif app_name == "unreal":
        print("   -> Would call _import_to_unreal()")
    else:
        print(f"   -> Would fallback to _open_zip_file() ❌ (unknown app: '{app_name}')")

    # 3. Test application creation
    print("\n3. Testing Application Creation:")
    from application import TunnelUIApplication

    app = TunnelUIApplication()
    print(f"   App created: {app is not None}")
    print(f"   Maya service: {app.maya_import_service is not None}")

    # 4. Test capabilities
    print("\n4. Testing Capabilities:")
    capabilities = app.asset_service.get_import_capabilities()
    maya_available = capabilities.get("maya_available", False)
    print(f"   Maya available: {maya_available}")

    # 5. Test the full import decision logic
    print("\n5. Full Import Decision Logic:")
    if app_name == "maya" and maya_available:
        print("   ✅ Maya detected AND available - should import to Maya")
    elif app_name == "maya" and not maya_available:
        print("   ❌ Maya detected but NOT available - would show warning")
    elif app_name == "standalone":
        print("   ❌ Standalone detected - would open zip file")
    else:
        print(f"   ❌ Unknown app '{app_name}' - would fallback to zip file")

    # 6. Check if there are any issues with the environment detection
    print("\n6. Environment Detection Details:")
    available_apps = env.available_applications
    print(f"   Available apps: {[app.value for app in available_apps.keys()]}")

    for app_enum, caps in available_apps.items():
        print(f"   - {app_enum.value}: {caps.name}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n=== DEBUG COMPLETE ===")
