# Detailed Maya Debug - Copy paste this into Maya Script Editor
import sys
from pathlib import Path

# Add TunnelUI src to path
tunnel_path = Path(__file__).resolve().parent
src_path = tunnel_path / "src"
sys.path.insert(0, str(src_path))

print("=== Detailed Maya Service Debug ===")

try:
    # 1. Basic setup
    print("1. Setting up configuration...")
    from configuration import ConfigurationManager, AssetLibraryConfig, AppEnvironment
    from data import FileSystemMetadataRepository, FileSystemImportRepository
    from services import AssetManagementService, ImageLoadingService, AssetSearchService

    config_manager = ConfigurationManager()
    config = config_manager.load_config()
    environment = AppEnvironment()
    environment.detect_all_applications()
    active_capabilities = environment.get_active_capabilities()

    print("   Config loaded: " + str(config is not None))
    print("   Maya ready: " + str(active_capabilities.maya_import_ready))

    # 2. Create basic services
    print("\n2. Creating basic services...")
    metadata_repo = FileSystemMetadataRepository(config)
    import_repo = FileSystemImportRepository(config)
    search_service = AssetSearchService(metadata_repo)
    asset_service = AssetManagementService(metadata_repo, import_repo, search_service)
    print("   Basic services created")

    # 3. Test Maya imports step by step
    print("\n3. Testing Maya service imports...")

    try:
        from services.maya.import_cache_service import ImportCacheService

        print("   ImportCacheService: OK")
    except Exception as e:
        print("   ImportCacheService: FAILED - " + str(e))
        raise

    try:
        from services.maya.texture_processing_service import TextureProcessingService

        print("   TextureProcessingService: OK")
    except Exception as e:
        print("   TextureProcessingService: FAILED - " + str(e))
        raise

    try:
        from services.maya.maya_bridge_service import MayaBridgeService

        print("   MayaBridgeService: OK")
    except Exception as e:
        print("   MayaBridgeService: FAILED - " + str(e))
        raise

    try:
        from services.maya.maya_import_service import MayaImportService

        print("   MayaImportService: OK")
    except Exception as e:
        print("   MayaImportService: FAILED - " + str(e))
        raise

    try:
        from services.maya.import_models import ImportCacheConfig

        print("   ImportCacheConfig: OK")
    except Exception as e:
        print("   ImportCacheConfig: FAILED - " + str(e))
        raise

    # 4. Test cache config creation
    print("\n4. Creating cache configuration...")
    try:
        cache_config = ImportCacheConfig(
            cache_root=config.maya_settings.cache_location.replace(
                "{library_root}", config.metadata_path
            ),
            max_cache_size_gb=config.maya_settings.cache_max_size_gb,
            cleanup_strategy="lru",
            auto_cleanup_enabled=config.maya_settings.auto_cleanup_enabled,
            cleanup_threshold_gb=config.maya_settings.cleanup_threshold_gb,
        )
        print("   Cache config created: " + str(cache_config.cache_root))
    except Exception as e:
        print("   Cache config FAILED: " + str(e))
        raise

    # 5. Test individual service creation
    print("\n5. Creating individual Maya services...")

    try:
        cache_service = ImportCacheService(cache_config)
        print("   Cache service: OK")
    except Exception as e:
        print("   Cache service FAILED: " + str(e))
        raise

    try:
        texture_processor = TextureProcessingService(config.maya_settings)
        print("   Texture processor: OK")
    except Exception as e:
        print("   Texture processor FAILED: " + str(e))
        raise

    try:
        maya_bridge = MayaBridgeService()
        print("   Maya bridge: OK")
    except Exception as e:
        print("   Maya bridge FAILED: " + str(e))
        raise

    # 6. Test main service creation
    print("\n6. Creating main Maya import service...")
    try:
        maya_import_service = MayaImportService(
            asset_service=asset_service,
            cache_service=cache_service,
            maya_bridge=maya_bridge,
            texture_processor=texture_processor,
            config_manager=config_manager,
        )
        print("   Maya import service: OK")

        # 7. Test connection
        print("\n7. Connecting to asset service...")
        asset_service.set_maya_import_service(maya_import_service)
        capabilities = asset_service.get_import_capabilities()
        print("   Maya available: " + str(capabilities.get("maya_available", False)))

        if capabilities.get("maya_available", False):
            print("\nSUCCESS: All Maya services working!")
        else:
            print("\nPROBLEM: Maya service created but not available")

    except Exception as e:
        print("   Maya import service FAILED: " + str(e))
        import traceback

        traceback.print_exc()
        raise

except Exception as e:
    print("\nFINAL ERROR: " + str(e))
    import traceback

    traceback.print_exc()

print("=====================================")
