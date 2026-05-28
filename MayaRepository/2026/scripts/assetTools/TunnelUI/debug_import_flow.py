# Debug Import Flow - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI to path
tunnel_path = Path(__file__).resolve().parent
src_path = tunnel_path / "src"
sys.path.insert(0, str(src_path))

print("=== Debug Import Flow ===")

# Force reload to pick up latest changes
modules_to_reload = ["application", "configuration", "services", "ui"]
for module_name in list(sys.modules.keys()):
    if any(keyword in module_name for keyword in modules_to_reload):
        if "TunnelUI" in str(sys.modules.get(module_name, "")):
            if module_name in sys.modules:
                del sys.modules[module_name]

try:
    # 1. Test application and capabilities
    from application import TunnelUIApplication

    app = TunnelUIApplication()

    print("1. Application Status:")
    print("   Maya service: " + str(app.maya_import_service is not None))

    capabilities = app.asset_service.get_import_capabilities()
    maya_available = capabilities.get("maya_available", False)
    print("   Maya available: " + str(maya_available))

    # 2. Test environment detection
    from configuration.config_models import AppEnvironment

    env = AppEnvironment()
    env.detect_all_applications()
    active_app = env.get_active_application()
    active_caps = env.get_active_capabilities()

    print("\n2. Environment Status:")
    print("   Active app: " + str(active_app.value))
    print("   Maya ready: " + str(active_caps.maya_import_ready))

    # 3. Test import button logic
    print("\n3. Import Button Logic:")
    print("   Button text: " + env.get_import_button_text())

    # 4. Simulate import decision logic (from image_preview_dialog.py)
    print("\n4. Import Decision Logic:")
    from configuration.config_models import DCCApplication

    print("   Active app check: " + str(active_app))
    print("   Is Maya? " + str(active_app == DCCApplication.MAYA))
    print("   Is Standalone? " + str(active_app == DCCApplication.STANDALONE))

    if active_app == DCCApplication.MAYA:
        print("   -> Should call _import_to_maya()")

        # Test capabilities check (what _import_to_maya does)
        capabilities = app.asset_service.get_import_capabilities()
        maya_available = capabilities.get("maya_available", False)
        print("   -> Maya available in import: " + str(maya_available))

        if maya_available:
            print("   -> Would create ImportProgressDialog")
        else:
            print("   -> Would show 'Maya Import Not Available' warning")

    elif active_app == DCCApplication.STANDALONE:
        print("   -> Should call _open_zip_file()")
    else:
        print("   -> Should fallback to _open_zip_file()")

except Exception as e:
    print("ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("\n" + "=" * 40)
