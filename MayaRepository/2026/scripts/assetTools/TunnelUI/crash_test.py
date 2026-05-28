# Minimal crash test to isolate import issues
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_src_path = Path(__file__).resolve().parent / "src"
if str(tunnel_src_path) not in sys.path:
    sys.path.insert(0, str(tunnel_src_path))

print("=== CRASH TEST: Isolating Import Issues ===")

# Test 1: Basic Maya commands
print("\n1. Testing basic Maya commands...")
try:
    import maya.cmds as mc

    # Test basic non-selection commands
    mc.sphere(name="test_sphere")
    mc.delete("test_sphere")
    print("✅ Basic Maya commands work")
except Exception as e:
    print(f"❌ Basic Maya commands failed: {e}")

# Test 2: Selection commands (the problematic ones)
print("\n2. Testing selection commands...")
try:
    import maya.cmds as mc

    mc.select(clear=True)
    print("✅ Select clear works")
except Exception as e:
    print(f"❌ Select clear failed: {e}")

try:
    result = mc.ls(selection=True)
    print(f"✅ ls selection works: {result}")
except Exception as e:
    print(f"❌ ls selection failed: {e}")

# Test 3: FBX import (without any selection handling)
print("\n3. Testing basic FBX import...")
try:
    import maya.cmds as mc

    # Create a simple test - just try to load FBX plugin
    mc.loadPlugin("fbxmaya", quiet=True)
    print("✅ FBX plugin loaded")
except Exception as e:
    print(f"❌ FBX plugin failed: {e}")

# Test 4: Bridge service with minimal import
print("\n4. Testing bridge service import method...")
try:
    from services.maya.maya_bridge_service import MayaBridgeService

    bridge = MayaBridgeService()
    print("✅ Bridge service created")

    # Test if we can call the problematic import method
    # But let's try with a non-existent file first to see if it handles errors
    from pathlib import Path

    fake_path = Path("nonexistent.fbx")

    print("Testing with fake file (should fail gracefully)...")
    try:
        result = bridge.import_geometry(fake_path, "test_asset")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error with fake file: {e}")

except Exception as e:
    print(f"❌ Bridge service import test failed: {e}")

print("\n=== CRASH TEST COMPLETE ===")
