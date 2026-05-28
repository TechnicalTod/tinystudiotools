# Debug Maya Detection - Run this from within Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_src_path = Path(__file__).resolve().parent / "src"
if str(tunnel_src_path) not in sys.path:
    sys.path.insert(0, str(tunnel_src_path))

print("=== DEBUG MAYA DETECTION (Run from Maya) ===")

try:
    # 1. Test basic Maya availability
    print("\n1. Testing Basic Maya Availability:")
    import maya.cmds as cmds
    import pymel.core as pm

    maya_version = cmds.about(version=True)
    print(f"   Maya version: {maya_version}")
    print(f"   Maya cmds available: {cmds is not None}")
    print(f"   PyMEL available: {pm is not None}")

    # 2. Test environment detection
    print("\n2. Testing Environment Detection:")
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

    # 3. Test the exact logic from ImagePreviewDialog.import_asset()
    print("\n3. Testing ImagePreviewDialog Logic:")
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

    # 4. Test application creation
    print("\n4. Testing Application Creation:")
    from application import TunnelUIApplication

    app = TunnelUIApplication()
    print(f"   App created: {app is not None}")
    print(f"   Maya service: {app.maya_import_service is not None}")

    # 5. Test capabilities
    print("\n5. Testing Capabilities:")
    capabilities = app.asset_service.get_import_capabilities()
    maya_available = capabilities.get("maya_available", False)
    print(f"   Maya available: {maya_available}")

    # 6. Test the full import decision logic
    print("\n6. Full Import Decision Logic:")
    if app_name == "maya" and maya_available:
        print("   ✅ Maya detected AND available - should import to Maya")
    elif app_name == "maya" and not maya_available:
        print("   ❌ Maya detected but NOT available - would show warning")
    elif app_name == "standalone":
        print("   ❌ Standalone detected - would open zip file")
    else:
        print(f"   ❌ Unknown app '{app_name}' - would fallback to zip file")

    # 7. Check if there are any issues with the environment detection
    print("\n7. Environment Detection Details:")
    available_apps = env.available_applications
    print(f"   Available apps: {[app.value for app in available_apps.keys()]}")

    for app_enum, caps in available_apps.items():
        print(
            f"   - {app_enum.value}: {caps.name} (import ready: {getattr(caps, 'maya_import_ready', 'N/A')})"
        )

    # 8. Test Maya bridge service directly
    print("\n8. Testing Maya Bridge Service:")
    from services.maya.maya_bridge_service import MayaBridgeService

    maya_bridge = MayaBridgeService()
    print(f"   Maya bridge available: {maya_bridge.maya_available}")
    print(f"   Maya bridge validation: {maya_bridge.validate_maya_environment()}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n=== DEBUG COMPLETE ===")
