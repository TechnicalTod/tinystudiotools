"""
Test different FBX import methods to find one that works reliably
Run this in Maya's script editor to test various approaches
"""

import maya.cmds as mc
import pymel.core as pm
import maya.mel as mel
from pathlib import Path
import traceback

# Test FBX file path (use one from the cache)
test_fbx = Path(
    "L:/megaScansMetadata/TunnelUI_Import_Cache/thxtai3da_thxtai3da/geometry/thxtai3da_LOD0.fbx"
)

print("=== FBX IMPORT METHOD TESTING ===")
print(f"Test file: {test_fbx}")
print(f"File exists: {test_fbx.exists()}")

if test_fbx.exists():
    print(f"File size: {test_fbx.stat().st_size} bytes")
else:
    print("❌ Test file not found - update the path above")
    exit()


def get_scene_objects():
    """Get current scene object count"""
    return len(mc.ls(type="transform"))


def test_method(name, test_func):
    """Test a specific import method"""
    print(f"\n{'='*50}")
    print(f"TESTING: {name}")
    print(f"{'='*50}")

    try:
        before_count = get_scene_objects()
        print(f"Objects before: {before_count}")

        # Run the test
        result = test_func()

        after_count = get_scene_objects()
        imported_count = after_count - before_count

        print(f"Objects after: {after_count}")
        print(f"Imported: {imported_count} objects")
        print(f"✅ {name} - SUCCESS")
        return True, imported_count

    except Exception as e:
        print(f"❌ {name} - FAILED")
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return False, 0


# Test Method 1: Basic mc.file()
def test_mc_file_basic():
    print("Using: mc.file() with basic parameters")
    mc.file(str(test_fbx), i=True, type="FBX")


# Test Method 2: mc.file() with ignore version
def test_mc_file_ignore_version():
    print("Using: mc.file() with ignoreVersion")
    mc.file(str(test_fbx), i=True, type="FBX", ignoreVersion=True)


# Test Method 3: PyMel importFile
def test_pymel_import():
    print("Using: pm.importFile()")
    pm.importFile(str(test_fbx), type="FBX")


# Test Method 4: PyMel with ignore version
def test_pymel_import_ignore():
    print("Using: pm.importFile() with ignoreVersion")
    pm.importFile(str(test_fbx), type="FBX", ignoreVersion=True)


# Test Method 5: Reference instead of import
def test_reference():
    print("Using: mc.file() with reference=True")
    mc.file(str(test_fbx), r=True, type="FBX", namespace="test_ref")


# Test Method 6: MEL FBXImport command
def test_mel_fbx():
    print("Using: MEL FBXImport command")
    mel.eval("FBXResetImport")
    mel.eval(f'FBXImport -f "{str(test_fbx)}"')


# Test Method 7: MEL with specific options
def test_mel_fbx_options():
    print("Using: MEL FBXImport with options")
    mel.eval("FBXResetImport")
    mel.eval('FBXImportMode -v "add"')
    mel.eval(f'FBXImport -f "{str(test_fbx)}"')


# Test Method 8: Open file instead of import
def test_open_file():
    print("Using: mc.file() with open instead of import")
    # Save current scene first
    current_scene = mc.file(q=True, sceneName=True)
    mc.file(new=True, force=True)
    mc.file(str(test_fbx), o=True, type="FBX")
    # Note: This changes the scene, so we'd need to restore


# Run all tests
tests = [
    ("Basic mc.file()", test_mc_file_basic),
    ("mc.file() with ignoreVersion", test_mc_file_ignore_version),
    ("PyMel importFile()", test_pymel_import),
    ("PyMel importFile() with ignoreVersion", test_pymel_import_ignore),
    ("Reference instead of import", test_reference),
    ("MEL FBXImport", test_mel_fbx),
    ("MEL FBXImport with options", test_mel_fbx_options),
]

results = []
for test_name, test_func in tests:
    success, count = test_method(test_name, test_func)
    results.append((test_name, success, count))

# Summary
print(f"\n{'='*60}")
print("SUMMARY OF RESULTS")
print(f"{'='*60}")

working_methods = []
for test_name, success, count in results:
    status = "✅ WORKS" if success else "❌ FAILED"
    if success:
        working_methods.append(test_name)
    print(f"{test_name:<35} {status} ({count} objects)")

print(f"\n🎯 WORKING METHODS: {len(working_methods)}")
for method in working_methods:
    print(f"  ✅ {method}")

if working_methods:
    print(f"\n💡 RECOMMENDATION: Use '{working_methods[0]}' in TunnelUI")
else:
    print(f"\n⚠️  NO METHODS WORKED - FBX file might be corrupted or incompatible")

print(f"\n{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}")
