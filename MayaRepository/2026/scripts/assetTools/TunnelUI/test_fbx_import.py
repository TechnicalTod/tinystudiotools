# Test just the FBX import step to isolate the crash
import maya.cmds as mc
from pathlib import Path

print("=== FBX IMPORT CRASH TEST ===")

# Test 1: Basic Maya file operations
print("\n1. Testing basic file operations...")
try:
    # Test basic ls command first
    result = mc.ls(type="transform")
    print("SUCCESS: ls command works, found " + str(len(result)) + " transforms")
except Exception as e:
    print("ERROR in ls command: " + str(e))

# Test 2: Try a simple FBX file operation
print("\n2. Testing FBX plugin...")
try:
    mc.loadPlugin("fbxmaya", quiet=True)
    print("SUCCESS: FBX plugin loaded")
except Exception as e:
    print("ERROR loading FBX plugin: " + str(e))

# Test 3: Test with a real FBX file from cache
print("\n3. Testing actual FBX import...")
try:
    # Look for an existing FBX in the cache
    cache_dir = Path("L:/megaScansMetadata/TunnelUI_Import_Cache")
    fbx_files = list(cache_dir.glob("*/geometry/*.fbx"))

    if fbx_files:
        test_fbx = fbx_files[0]  # Use first FBX found
        print("Testing with: " + str(test_fbx))

        # Store transforms before import
        print("Getting transforms before import...")
        before_import = set(mc.ls(type="transform"))
        print("Found " + str(len(before_import)) + " transforms before import")

        # Try the actual FBX import
        print("Starting FBX import...")
        mc.file(
            str(test_fbx),
            i=True,  # import
            type="FBX",
            ignoreVersion=True,
            ra=True,  # rename all
            namespace="test_asset",
        )
        print("SUCCESS: FBX import completed")

        # Check what was imported
        print("Getting transforms after import...")
        after_import = set(mc.ls(type="transform"))
        new_objects = after_import - before_import
        print("SUCCESS: Found " + str(len(new_objects)) + " new objects")

    else:
        print("No FBX files found in cache for testing")

except Exception as e:
    print("ERROR in FBX import: " + str(e))
    import traceback

    print("Traceback:")
    traceback.print_exc()

print("\n=== FBX IMPORT TEST COMPLETE ===")
