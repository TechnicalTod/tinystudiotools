#!/usr/bin/env python3
"""
Quick Maya Validation Test

Run this in Maya Script Editor to test validation steps.
"""


def test_maya_validation():
    print("=== Quick Maya Validation Test ===\n")

    try:
        import maya.cmds as cmds
        import pymel.core as pm

        # Test 1: Node creation
        try:
            test_node = cmds.createNode("transform", name="validation_test")
            cmds.delete(test_node)
            print("✅ Node creation/deletion: PASSED")
        except Exception as e:
            print(f"❌ Node creation/deletion: FAILED - {e}")

        # Test 2: Scene info access
        try:
            scene_exists = cmds.file(query=True, exists=True)
            print(f"✅ Scene info access: PASSED (exists: {scene_exists})")
        except Exception as e:
            print(f"❌ Scene info access: FAILED - {e}")

        # Test 3: USD Preview Surface check
        try:
            usd_available = cmds.nodeType("usdPreviewSurface", isTypeName=True)
            print(f"✅ USD Preview Surface: PASSED (available: {usd_available})")
        except Exception as e:
            print(f"❌ USD Preview Surface: FAILED - {e}")

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"❌ Test failed: {e}")


# Run the test
test_maya_validation()
