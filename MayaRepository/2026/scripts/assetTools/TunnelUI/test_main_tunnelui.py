# Test Main TunnelUI - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

print("=== Testing Main TunnelUI Application ===")

# Add TunnelUI to path
tunnel_path = Path(__file__).resolve().parent
if str(tunnel_path) not in sys.path:
    sys.path.insert(0, str(tunnel_path))

# Force reload of all TunnelUI modules to pick up latest changes
try:
    print("1. Clearing module cache...")
    modules_to_reload = []

    # Find all TunnelUI-related modules in cache
    for module_name in list(sys.modules.keys()):
        if any(
            keyword in module_name
            for keyword in ["application", "configuration", "services", "data", "ui"]
        ):
            if (
                "TunnelUI" in str(sys.modules.get(module_name, "")).replace("\\", "/")
                or "tunnel" in module_name.lower()
            ):
                modules_to_reload.append(module_name)

    # Remove from cache
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            print("   Removing: " + module_name)
            del sys.modules[module_name]

    print("   Cleared " + str(len(modules_to_reload)) + " cached modules")

except Exception as e:
    print("   Module cleanup error: " + str(e))

# Now test the main TunnelUI entry point
try:
    print("\n2. Testing main TunnelUI entry point...")

    # Import and call the main function (this is what users do)
    import TunnelUi

    print("   TunnelUi module imported successfully")

    # Call the main entry point
    print("   Calling TunnelUi.openWindow()...")
    window = TunnelUi.openWindow()

    print("   Window created: " + str(window is not None))

    if window:
        print("SUCCESS: TunnelUI application launched successfully!")
        print("   Window type: " + str(type(window)))

        # Check if it has Maya import capabilities
        try:
            if hasattr(window, "asset_service"):
                caps = window.asset_service.get_import_capabilities()
                maya_available = caps.get("maya_available", False)
                print("   Maya import available: " + str(maya_available))
            else:
                print("   Window doesn't have asset_service attribute")
        except Exception as e:
            print("   Could not check capabilities: " + str(e))
    else:
        print("PROBLEM: Window creation returned None")

except Exception as e:
    print("ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
