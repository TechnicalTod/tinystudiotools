# Trace Import Issue - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI to path
tunnel_path = Path(__file__).resolve().parent
src_path = tunnel_path / "src"
sys.path.insert(0, str(src_path))

print("=== Tracing Import Issue ===")

# Force reload
modules_to_reload = ["ui", "application", "services"]
for module_name in list(sys.modules.keys()):
    if any(keyword in module_name for keyword in modules_to_reload):
        if "TunnelUI" in str(sys.modules.get(module_name, "")):
            if module_name in sys.modules:
                del sys.modules[module_name]

try:
    # 1. Verify backend is still working
    print("1. Backend Status Check:")
    from application import TunnelUIApplication

    app = TunnelUIApplication()

    print("   Maya service: " + str(app.maya_import_service is not None))
    capabilities = app.asset_service.get_import_capabilities()
    maya_available = capabilities.get("maya_available", False)
    print("   Maya available: " + str(maya_available))

    # 2. Test environment logic
    print("\n2. Environment Logic Check:")
    from configuration.config_models import AppEnvironment, DCCApplication

    env = app.environment  # Use the same environment as the app
    active_app = env.get_active_application()

    print("   Active app from app.environment: " + str(active_app.value))
    print("   Is Maya? " + str(active_app == DCCApplication.MAYA))

    # 3. Test UI import logic path
    print("\n3. UI Import Logic Path:")
    asset_id = "thruaanda"  # Use the asset you tried to import

    # Simulate what happens in ImagePreviewDialog.import_asset()
    if active_app == DCCApplication.STANDALONE:
        print("   -> Would call _open_zip_file() ❌")
    elif active_app == DCCApplication.MAYA:
        print("   -> Would call _import_to_maya() ✅")

        # Test what _import_to_maya does
        capabilities = app.asset_service.get_import_capabilities()
        if not capabilities.get("maya_available", False):
            print("      -> Maya not available - would show warning ❌")
        else:
            print("      -> Maya available - would create ImportProgressDialog ✅")

            # Test ImportProgressDialog logic
            print("      -> ImportProgressDialog would:")
            print("         1. Check asset_service: " + str(app.asset_service is not None))
            print(
                "         2. Check maya_available: "
                + str(capabilities.get("maya_available", False))
            )
            print("         3. Create ImportWorker")
            print("         4. Call asset_service.import_asset_to_maya()")

            # Test if the import method exists
            has_import_method = hasattr(app.asset_service, "import_asset_to_maya")
            print("         5. import_asset_to_maya exists: " + str(has_import_method))

            if has_import_method:
                print("         6. Maya import should work! ✅")
            else:
                print("         6. Maya import method missing! ❌")
    else:
        print("   -> Would fallback to _open_zip_file() ❌")

    # 4. Check for any error conditions
    print("\n4. Error Condition Checks:")

    # Check if there are any issues with the asset service
    print("   Asset service type: " + str(type(app.asset_service)))
    print("   Has maya_import_service: " + str(hasattr(app.asset_service, "maya_import_service")))
    if hasattr(app.asset_service, "maya_import_service"):
        print("   maya_import_service value: " + str(app.asset_service.maya_import_service))

    print("\n=== Diagnosis Complete ===")
    print("\nPOSSIBLE ISSUES:")
    print("1. Maya import is working but progress dialog has issues")
    print("2. ImportProgressDialog.Accepted attribute missing (we saw this error)")
    print("3. Import succeeds but dialog doesn't close properly")
    print("4. Error in import causes fallback to zip opening")

    print("\nNEXT STEPS:")
    print("1. Check ImportProgressDialog for Accepted attribute")
    print("2. Add error handling in _import_to_maya")
    print("3. Test actual import with progress tracking")

except Exception as e:
    print("ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
