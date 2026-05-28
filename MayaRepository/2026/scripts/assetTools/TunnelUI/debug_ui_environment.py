# Debug UI Environment - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI to path
tunnel_path = Path(__file__).resolve().parent
src_path = tunnel_path / "src"
sys.path.insert(0, str(src_path))

print("=== Debug UI Environment ===")

# Force reload
modules_to_reload = ["ui", "application", "configuration"]
for module_name in list(sys.modules.keys()):
    if any(keyword in module_name for keyword in modules_to_reload):
        if "TunnelUI" in str(sys.modules.get(module_name, "")):
            if module_name in sys.modules:
                del sys.modules[module_name]

try:
    from application import TunnelUIApplication

    app = TunnelUIApplication()

    # Check the environment object that the application created
    print("1. Application Environment Object:")
    print("   Type: " + str(type(app.environment)))

    # Check what the environment object contains
    active_app = app.environment.get_active_application()
    active_caps = app.environment.get_active_capabilities()

    print("   Active app: " + str(active_app.value))
    print("   Active caps name: " + str(active_caps.name))
    print("   Maya ready: " + str(getattr(active_caps, "maya_import_ready", "MISSING")))

    # This is what the UI will see when it does import_asset()
    print("\n2. UI Import Logic Simulation:")
    from configuration.config_models import DCCApplication

    if active_app == DCCApplication.MAYA:
        print("   -> UI will call _import_to_maya() ✅")

        # This is what _import_to_maya checks
        capabilities = app.asset_service.get_import_capabilities()
        maya_available = capabilities.get("maya_available", False)
        print("   -> Maya available check: " + str(maya_available))

        if maya_available:
            print("   -> Would show ImportProgressDialog ✅")
        else:
            print("   -> Would show 'Maya Import Not Available' warning ❌")
    else:
        print("   -> UI will call _open_zip_file() ❌")

    # Compare backend vs UI environment
    print("\n3. Backend vs UI Environment:")
    print("   Backend Maya service: " + str(app.maya_import_service is not None))
    print("   UI environment Maya ready: " + str(getattr(active_caps, "maya_import_ready", False)))

    # Check if they match
    backend_working = app.maya_import_service is not None
    ui_maya_ready = getattr(active_caps, "maya_import_ready", False)

    if backend_working and ui_maya_ready:
        print("   Status: ✅ Backend and UI both ready")
    elif backend_working and not ui_maya_ready:
        print("   Status: ❌ Backend ready but UI thinks Maya not ready")
    elif not backend_working and ui_maya_ready:
        print("   Status: ❌ UI thinks Maya ready but backend not initialized")
    else:
        print("   Status: ❌ Both backend and UI think Maya not ready")

    print("\n4. Button Text Check:")
    button_text = app.environment.get_import_button_text()
    print("   UI button text: '" + button_text + "'")

    if "Import to Maya" in button_text:
        print("   Button: ✅ Correct")
    else:
        print("   Button: ❌ Wrong (should be 'Import to Maya')")

except Exception as e:
    print("ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
