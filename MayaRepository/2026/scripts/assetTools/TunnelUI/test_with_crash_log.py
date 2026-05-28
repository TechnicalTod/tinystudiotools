# Test TunnelUI with persistent crash logging
import sys
from pathlib import Path
import os

print("=== MAYA CRASH LOGGING TEST ===")
print("Crash log will be written to: C:\\temp\\maya_crash_debug.log")
print("If Maya crashes, check that file to see the last checkpoint!")
print()

# Clear the crash log file for a fresh start
crash_log_file = r"C:\temp\maya_crash_debug.log"
if os.path.exists(crash_log_file):
    os.remove(crash_log_file)
    print("Cleared previous crash log")

tunnel_path = Path(__file__).resolve().parent
if str(tunnel_path) not in sys.path:
    sys.path.insert(0, str(tunnel_path))

# Clear cached modules to get the updated services with crash logging
modules_to_clear = ["maya_import_service", "maya_bridge_service", "crash_logger"]
for module_name in list(sys.modules.keys()):
    if any(x in module_name for x in modules_to_clear):
        if module_name in sys.modules:
            del sys.modules[module_name]
            print(f"Cleared cached module: {module_name}")

print()
print("Starting TunnelUI with crash logging...")
print("If Maya crashes, run this in a new Maya session to check the log:")
_check_crash = Path(__file__).resolve().parent / "check_crash_log.py"
print(f"    exec(open({_check_crash!r}).read())")
print()

try:
    import TunnelUi

    TunnelUi.openWindow()
    print("TunnelUI launched successfully!")
except Exception as e:
    print(f"Error launching TunnelUI: {e}")
    print("Check the crash log at: C:\\temp\\maya_crash_debug.log")
