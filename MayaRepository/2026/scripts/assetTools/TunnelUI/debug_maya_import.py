#!/usr/bin/env python3
"""
Debug Maya Import Service Initialization

This script checks why Maya import services are not being initialized.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def debug_maya_import():
    """Debug Maya import service initialization"""
    print("=== Maya Import Service Debug ===\n")

    try:
        # Step 1: Check environment detection
        print("1. Checking Environment Detection...")
        from configuration.config_models import AppEnvironment

        environment = AppEnvironment()
        available_apps = environment.detect_all_applications()
        active_app = environment.get_active_application()
        active_capabilities = environment.get_active_capabilities()

        print(f"   Available applications: {[app.value for app in available_apps.keys()]}")
        print(f"   Active application: {active_app.value if active_app else 'None'}")

        if active_capabilities:
            print(f"   Active app name: {active_capabilities.name}")
            print(f"   Has maya_import_ready: {hasattr(active_capabilities, 'maya_import_ready')}")
            if hasattr(active_capabilities, "maya_import_ready"):
                print(f"   Maya import ready: {active_capabilities.maya_import_ready}")
            if hasattr(active_capabilities, "usd_support"):
                print(f"   USD support: {active_capabilities.usd_support}")
            if hasattr(active_capabilities, "imagemagick_available"):
                print(f"   ImageMagick available: {active_capabilities.imagemagick_available}")

        # Step 2: Check configuration loading
        print("\n2. Checking Configuration Loading...")
        from configuration.config_manager import ConfigurationManager

        config_manager = ConfigurationManager()
        config = config_manager.load_config()

        print(f"   Config loaded successfully: {config is not None}")
        print(f"   Has maya_settings: {hasattr(config, 'maya_settings')}")
        if hasattr(config, "maya_settings"):
            print(f"   Maya settings type: {type(config.maya_settings)}")
            print(
                f"   Use import cache: {getattr(config.maya_settings, 'use_import_cache', 'N/A')}"
            )

        # Step 3: Check Maya service imports
        print("\n3. Checking Maya Service Imports...")
        try:
            from services.maya.import_cache_service import ImportCacheService

            print("   ✅ ImportCacheService imported")
        except Exception as e:
            print(f"   ❌ ImportCacheService import failed: {e}")

        try:
            from services.maya.texture_processing_service import TextureProcessingService

            print("   ✅ TextureProcessingService imported")
        except Exception as e:
            print(f"   ❌ TextureProcessingService import failed: {e}")

        try:
            from services.maya.maya_bridge_service import MayaBridgeService

            print("   ✅ MayaBridgeService imported")
        except Exception as e:
            print(f"   ❌ MayaBridgeService import failed: {e}")

        try:
            from services.maya.maya_import_service import MayaImportService

            print("   ✅ MayaImportService imported")
        except Exception as e:
            print(f"   ❌ MayaImportService import failed: {e}")

        # Step 4: Check AssetManagementService
        print("\n4. Checking AssetManagementService...")
        from services.asset_management_service import AssetManagementService
        from data.repositories.metadata_repository import FileSystemMetadataRepository
        from data.repositories.import_repository import FileSystemImportRepository
        from services.asset_search_service import AssetSearchService

        # Create mock services
        metadata_repo = FileSystemMetadataRepository(config)
        import_repo = FileSystemImportRepository(config)
        search_service = AssetSearchService(metadata_repo)

        asset_service = AssetManagementService(metadata_repo, import_repo, search_service)

        print(f"   AssetManagementService created: {asset_service is not None}")
        print(
            f"   Has maya_import_service attribute: {hasattr(asset_service, 'maya_import_service')}"
        )
        print(f"   Maya import service: {getattr(asset_service, 'maya_import_service', 'N/A')}")

        capabilities = asset_service.get_import_capabilities()
        print(f"   Import capabilities: {capabilities}")

        # Step 5: Simulate application initialization
        print("\n5. Simulating Application Initialization...")

        if (
            active_capabilities
            and active_capabilities.name == "Autodesk Maya"
            and hasattr(active_capabilities, "maya_import_ready")
            and active_capabilities.maya_import_ready
        ):
            print("   Maya conditions met - would initialize Maya services")

            try:
                from services.maya.import_models import ImportCacheConfig

                # Create cache configuration
                cache_config = ImportCacheConfig(
                    cache_root=config.maya_settings.cache_location.replace(
                        "{library_root}", config.metadata_path
                    ),
                    max_cache_size_gb=config.maya_settings.cache_max_size_gb,
                    cleanup_strategy="lru",
                    auto_cleanup_enabled=config.maya_settings.auto_cleanup_enabled,
                    cleanup_threshold_gb=config.maya_settings.cleanup_threshold_gb,
                )

                print("   ✅ Cache config created successfully")

                # Initialize Maya services
                cache_service = ImportCacheService(cache_config)
                texture_processor = TextureProcessingService(config.maya_settings)
                maya_bridge = MayaBridgeService()

                print("   ✅ Maya services initialized")

                # Initialize main Maya import service
                maya_import_service = MayaImportService(
                    asset_service=asset_service,
                    cache_service=cache_service,
                    maya_bridge=maya_bridge,
                    texture_processor=texture_processor,
                    config_manager=config_manager,
                )

                print("   ✅ MayaImportService created successfully")

                # Connect to asset service
                asset_service.set_maya_import_service(maya_import_service)

                # Check final capabilities
                final_capabilities = asset_service.get_import_capabilities()
                print(f"   Final capabilities: {final_capabilities}")

            except Exception as e:
                print(f"   ❌ Maya service initialization failed: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("   ❌ Maya conditions NOT met:")
            print(f"      - Active app: {active_app}")
            print(f"      - Active capabilities: {active_capabilities}")
            print(
                f"      - Active app name: {getattr(active_capabilities, 'name', 'N/A') if active_capabilities else 'N/A'}"
            )
            print(
                f"      - Has maya_import_ready: {hasattr(active_capabilities, 'maya_import_ready') if active_capabilities else False}"
            )
            print(
                f"      - Maya import ready: {getattr(active_capabilities, 'maya_import_ready', False) if active_capabilities else False}"
            )

        # Step 6: Detailed Maya validation testing
        print("\n6. Detailed Maya Import Validation Testing...")

        if active_capabilities and active_capabilities.name == "Autodesk Maya":
            try:
                import maya.cmds as cmds
                import pymel.core as pm

                print("   Testing individual validation steps:")

                # Test 1: Node creation
                try:
                    test_node = cmds.createNode("transform", name="tunnelui_validation_test")
                    cmds.delete(test_node)
                    print("   ✅ Node creation/deletion: PASSED")
                except Exception as e:
                    print(f"   ❌ Node creation/deletion: FAILED - {e}")

                # Test 2: Scene info access
                try:
                    scene_exists = cmds.file(query=True, exists=True)
                    print(f"   ✅ Scene info access: PASSED (exists: {scene_exists})")
                except Exception as e:
                    print(f"   ❌ Scene info access: FAILED - {e}")

                # Test 3: USD Preview Surface check
                try:
                    usd_available = cmds.nodeType("usdPreviewSurface", isTypeName=True)
                    print(f"   ✅ USD Preview Surface check: PASSED (available: {usd_available})")
                except Exception as e:
                    print(f"   ❌ USD Preview Surface check: FAILED - {e}")

                # Test 4: Direct validation method call
                try:
                    validation_result = environment._validate_maya_import_environment(cmds, pm)
                    print(f"   Validation method result: {validation_result}")
                except Exception as e:
                    print(f"   ❌ Validation method call: FAILED - {e}")
                    import traceback

                    traceback.print_exc()

            except ImportError as e:
                print(f"   ❌ Maya modules import failed: {e}")
        else:
            print("   Skipped - not in Maya environment")

        print("\n=== Debug Complete ===")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_maya_import()
