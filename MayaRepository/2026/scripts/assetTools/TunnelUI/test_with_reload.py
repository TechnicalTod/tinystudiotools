# Test with forced module reload - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_path = Path(__file__).resolve().parent
src_path = tunnel_path / "src"
sys.path.insert(0, str(src_path))

print("=== Maya Debug with Reload ===")

# Force reload of modules to pick up changes
try:
    # Remove modules from cache to force reload
    modules_to_reload = [
        "application",
        "configuration.config_models",
        "configuration.config_manager",
    ]

    for module_name in modules_to_reload:
        if module_name in sys.modules:
            print("Removing cached module: " + module_name)
            del sys.modules[module_name]

    print("Modules cleared from cache")

except Exception as e:
    print("Module cleanup error: " + str(e))

try:
    # 1. Basic Maya check
    import maya.cmds as cmds

    print("1. Maya version: " + cmds.about(version=True))

    # 2. Environment detection
    from configuration.config_models import AppEnvironment

    env = AppEnvironment()
    apps = env.detect_all_applications()
    active_app = env.get_active_application()
    active_caps = env.get_active_capabilities()

    print("2. Active app: " + active_app.value)
    print("   App name: " + active_caps.name)
    if hasattr(active_caps, "maya_import_ready"):
        print("   Maya ready: " + str(active_caps.maya_import_ready))

    # 3. Application init (should now show DEBUG messages)
    print("3. Creating TunnelUIApplication...")
    from application import TunnelUIApplication

    app = TunnelUIApplication()

    print("   App created: " + str(app is not None))
    print("   Maya service: " + str(app.maya_import_service))

    # 4. Capabilities
    caps = app.asset_service.get_import_capabilities()
    print("4. Maya available: " + str(caps.get("maya_available", False)))

    if caps.get("maya_available", False):
        print("SUCCESS: Maya services working!")
    else:
        print("PROBLEM: Maya services not initialized")

except Exception as e:
    print("ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("===============================")
