"""
Test script to verify texture settings are working correctly
Run this in Maya to test if displacement textures are properly disabled
"""

import sys
from pathlib import Path

# Add TunnelUI to path
tunnelui_path = Path(__file__).parent
sys.path.insert(0, str(tunnelui_path))

try:
    from src.configuration.config_manager import ConfigurationManager
    from src.configuration.config_models import MayaImportSettings

    print("=== TEXTURE SETTINGS TEST ===")

    # Test 1: Load config and check settings
    config_manager = ConfigurationManager()
    config = config_manager.get_config()

    print(f"Config loaded: {config is not None}")
    print(f"Maya settings: {config.maya_settings is not None}")

    if config.maya_settings:
        maya_settings = config.maya_settings
        print(f"Enabled texture types: {maya_settings.enabled_texture_types}")
        print(
            f"Displacement enabled: {maya_settings.enabled_texture_types.get('displacement', 'NOT_FOUND')}"
        )

        # Test 2: Test the filtering logic
        test_textures = {
            "diffuse": Path("/test/diffuse.jpg"),
            "normal": Path("/test/normal.jpg"),
            "displacement": Path("/test/displacement.exr"),
        }

        print(f"\nTest textures: {list(test_textures.keys())}")

        filtered_textures = {}
        for param_name, texture_path in test_textures.items():
            if hasattr(maya_settings, "enabled_texture_types"):
                if maya_settings.enabled_texture_types.get(param_name, True):
                    filtered_textures[param_name] = texture_path
                    print(f"✅ Including {param_name} texture")
                else:
                    print(f"❌ Skipping {param_name} texture (disabled)")
            else:
                filtered_textures[param_name] = texture_path
                print(f"⚠️ No settings found, including {param_name}")

        print(f"\nFiltered textures: {list(filtered_textures.keys())}")

        if "displacement" not in filtered_textures:
            print("✅ SUCCESS: Displacement texture properly filtered out!")
        else:
            print("❌ FAIL: Displacement texture was not filtered out!")

    else:
        print("❌ No Maya settings found")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
