# Minimal test to isolate FBX import crash
import maya.cmds as mc
from pathlib import Path

print("=== MINIMAL FBX IMPORT TEST ===")

# Use the exact same file that was working in the logs
test_fbx = Path(
    r"L:\megaScansMetadata\TunnelUI_Import_Cache\th5jahwfa_th5jahwfa\geometry\th5jahwfa_LOD0.fbx"
)

print(f"Testing FBX: {test_fbx}")
print(f"File exists: {test_fbx.exists()}")
print(f"File size: {test_fbx.stat().st_size} bytes")

# Test 1: Try the exact import command that was causing the crash
print("\n1. Testing exact import command...")
try:
    print("Before import - getting transforms...")
    before = set(mc.ls(type="transform"))
    print(f"Found {len(before)} transforms before import")

    print("Calling mc.file() for FBX import...")
    mc.file(
        str(test_fbx),
        i=True,  # import
        type="FBX",
        ignoreVersion=True,
        ra=True,  # rename all
        namespace="test_crash",
        options="fbxImportMode=add",
    )
    print("SUCCESS: FBX import completed!")

    after = set(mc.ls(type="transform"))
    new_objects = after - before
    print(f"SUCCESS: Found {len(new_objects)} new objects")

except Exception as e:
    print(f"ERROR in FBX import: {e}")
    import traceback

    print("Traceback:")
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
