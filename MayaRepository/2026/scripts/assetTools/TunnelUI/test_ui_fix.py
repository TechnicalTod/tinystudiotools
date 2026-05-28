# Test UI Fix - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI to path
tunnel_path = Path(__file__).resolve().parent
src_path = tunnel_path / "src"
sys.path.insert(0, str(src_path))

print("=== Testing UI Fix ===")

# Force reload to pick up UI changes
modules_to_reload = ["ui", "application", "configuration", "services"]
for module_name in list(sys.modules.keys()):
    if any(keyword in module_name for keyword in modules_to_reload):
        if "TunnelUI" in str(sys.modules.get(module_name, "")):
            if module_name in sys.modules:
                print("Removing cached module: " + module_name)
                del sys.modules[module_name]

try:
    print("\n1. Testing UI import logic simulation...")

    # Simulate what ImagePreviewDialog.import_asset() now does
    from configuration.config_models import AppEnvironment, DCCApplication

    fresh_environment = AppEnvironment()
    fresh_environment.detect_all_applications()
    active_app = fresh_environment.get_active_application()

    print("   Fresh environment active app: " + str(active_app.value))
    print("   Is Maya? " + str(active_app == DCCApplication.MAYA))
    print("   Button text: " + fresh_environment.get_import_button_text())

    if active_app == DCCApplication.MAYA:
        print("   -> UI will call _import_to_maya() ✅")
    else:
        print("   -> UI will call _open_zip_file() ❌")

    print("\n2. Testing button text...")
    # Simulate button text creation
    fresh_env = AppEnvironment()
    fresh_env.detect_all_applications()
    button_text = fresh_env.get_import_button_text()
    print("   Button text will be: '" + button_text + "'")

    print("\n3. Testing full TunnelUI launch...")
    from application import TunnelUIApplication

    app = TunnelUIApplication()

    print("   Maya service initialized: " + str(app.maya_import_service is not None))
    capabilities = app.asset_service.get_import_capabilities()
    print("   Maya available: " + str(capabilities.get("maya_available", False)))

    if app.maya_import_service and capabilities.get("maya_available", False):
        print("   ✅ Backend ready for Maya import")
    else:
        print("   ❌ Backend not ready")

    print("\n✅ UI fix should now work! Try opening an asset in TunnelUI.")

except Exception as e:
    print("ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
