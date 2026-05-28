"""
TunnelUI Asset Browser Application Factory

This module provides the main application class that coordinates all components
of the refactored TunnelUI Asset Browser.
"""

import sys
import logging
from typing import Optional

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

# Import from absolute paths (src is in sys.path)
from configuration import ConfigurationManager, AssetLibraryConfig, AppEnvironment
from data import FileSystemMetadataRepository, FileSystemImportRepository
from services import AssetManagementService, ImageLoadingService, AssetSearchService


class TunnelUIApplication:
    """
    Main application factory for TunnelUI Asset Browser.

    This class coordinates all the components and provides entry points
    for both Maya and standalone operation.
    """

    def __init__(self):
        """Initialize the application with configuration and services."""
        self.logger = logging.getLogger(__name__)

        # Initialize enhanced configuration system with multi-DCC support
        self.config_manager = ConfigurationManager()
        self.config = self.config_manager.load_config()
        self.environment = AppEnvironment()

        # Detect all available applications (replaces legacy detect_maya_environment)
        available_apps = self.environment.detect_all_applications()

        # Apply environment-specific settings
        self.config_manager.apply_environment_settings(self.environment)

        # Log enhanced application detection results
        active_app = self.environment.get_active_application()
        app_display_name = self.environment.get_application_display_name()

        self.logger.info(f"TunnelUI Application starting with {app_display_name}")
        self.logger.info(f"Available applications: {[app.value for app in available_apps.keys()]}")
        self.logger.info(f"Active application: {active_app.value}")

        if self.environment.user_override:
            self.logger.info(f"User override active: {self.environment.user_override.value}")

        # Initialize services
        self.image_service = ImageLoadingService()
        self.metadata_repo = FileSystemMetadataRepository(self.config)
        self.import_repo = FileSystemImportRepository(self.config)
        self.search_service = AssetSearchService(self.metadata_repo)
        self.asset_service = AssetManagementService(
            self.metadata_repo, self.import_repo, self.search_service
        )

        # Initialize Maya-specific services if Maya is available
        self.maya_import_service = None
        active_app = self.environment.get_active_application()
        active_capabilities = self.environment.get_active_capabilities()

        if (
            active_capabilities
            and active_capabilities.name == "Autodesk Maya"
            and hasattr(active_capabilities, "maya_import_ready")
            and active_capabilities.maya_import_ready
        ):
            self.logger.info("Maya environment detected - initializing Maya import services")

            try:
                from services.maya.import_cache_service import ImportCacheService
                from services.maya.texture_processing_service import TextureProcessingService
                from services.maya.maya_bridge_service import MayaBridgeService
                from services.maya.maya_import_service import MayaImportService
                from services.maya.import_models import ImportCacheConfig

                # Create cache configuration
                cache_config = ImportCacheConfig(
                    cache_root=self.config.maya_settings.cache_location.replace(
                        "{library_root}", self.config.metadata_path
                    ),
                    max_cache_size_gb=self.config.maya_settings.cache_max_size_gb,
                    cleanup_strategy="lru",
                    auto_cleanup_enabled=self.config.maya_settings.auto_cleanup_enabled,
                    cleanup_threshold_gb=self.config.maya_settings.cleanup_threshold_gb,
                )

                # Initialize Maya services
                cache_service = ImportCacheService(cache_config)
                texture_processor = TextureProcessingService(self.config.maya_settings)
                maya_bridge = MayaBridgeService()

                # Initialize main Maya import service
                self.maya_import_service = MayaImportService(
                    asset_service=self.asset_service,
                    cache_service=cache_service,
                    maya_bridge=maya_bridge,
                    texture_processor=texture_processor,
                    config_manager=self.config_manager,
                )

                # Connect Maya import service to asset service
                self.asset_service.set_maya_import_service(self.maya_import_service)

                self.logger.info("Maya import services initialized successfully")

            except Exception as e:
                self.logger.error(f"Failed to initialize Maya import services: {e}")
                import traceback

                self.logger.error(f"Full traceback: {traceback.format_exc()}")
                self.maya_import_service = None

        # Main window will be created when needed
        self.main_window: Optional[QWidget] = None

    def _initialize_services(self):
        """Initialize the service layer with dependency injection."""
        self.logger.info("Initializing application services...")

        # Data access layer
        self.metadata_repo = FileSystemMetadataRepository(self.config)
        self.import_repo = FileSystemImportRepository(self.config)

        # Service layer
        self.image_service = ImageLoadingService()
        self.asset_service = AssetManagementService(self.metadata_repo, self.import_repo)

        # Note: Validation is deferred for performance - called only when needed
        self.logger.info("Services initialized successfully - validation deferred for performance")

    def _create_main_window(self) -> QWidget:
        """Create and configure the main window."""
        if self.main_window is not None:
            return self.main_window

        try:
            from ui.main_window import TunnelMainWindow

            # Determine parent window for Maya integration
            parent = self.environment.get_maya_main_window() if self.environment.is_maya else None

            # Create main window with dependency injection
            self.main_window = TunnelMainWindow(
                asset_service=self.asset_service,
                image_service=self.image_service,
                config_manager=self.config_manager,
                environment=self.environment,
                parent=parent,
            )

            # Apply Maya window flags if in Maya
            if self.environment.is_maya and parent:
                self.main_window.setWindowFlags(Qt.Window)

            self.logger.info("Main window created successfully")
            return self.main_window

        except Exception as e:
            self.logger.error(f"Failed to create main window: {e}")
            raise

    def run_maya_mode(self) -> Optional[QWidget]:
        """
        Run the application in Maya mode.

        Returns:
            QWidget: The main window widget for Maya integration
        """
        self.logger.info("Starting TunnelUI in Maya mode")

        try:
            # Create and show main window
            main_window = self._create_main_window()
            main_window.show()

            return main_window

        except Exception as e:
            self.logger.error(f"Failed to start Maya mode: {e}")
            raise

    def run_standalone(self) -> int:
        """
        Run the application in standalone mode.

        Returns:
            int: Exit code for the application
        """
        self.logger.info("Starting TunnelUI in standalone mode")

        try:
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
                self.logger.info("Created new QApplication instance")

            # Create and show main window
            main_window = self._create_main_window()
            main_window.show()

            self.logger.info("Starting Qt event loop")
            return app.exec()

        except Exception as e:
            self.logger.error(f"Failed to start standalone mode: {e}")
            raise

    def get_application_info(self) -> dict:
        """
        Get comprehensive application information for debugging.

        Returns:
            dict: Application configuration and status information
        """
        try:
            library_stats = self.asset_service.get_library_statistics()
        except Exception as e:
            self.logger.warning(f"Could not get library statistics: {e}")
            library_stats = {"total_assets": 0, "total_categories": 0, "error": str(e)}

        return {
            "environment": {
                "is_maya": self.environment.is_maya,
                "maya_version": self.environment.maya_version,
                "app_root": str(self.environment.app_root),
            },
            "configuration": {
                "metadata_path": str(self.config.metadata_path),
                "assets_path": str(self.config.assets_path),
                "maya_mode": self.config.maya_mode,
                "debug_mode": self.config.debug_mode,
            },
            "library_stats": library_stats,
        }


def openWindow():
    """
    Legacy entry point for backward compatibility.

    This function maintains the same signature as the original TunnelUI
    for seamless integration with existing Maya shelves and scripts.
    """
    try:
        app = TunnelUIApplication()

        if app.environment.is_maya:
            return app.run_maya_mode()
        else:
            return app.run_standalone()

    except Exception as e:
        logging.error(f"Failed to open TunnelUI: {e}")
        try:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(None, "TunnelUI Error", f"Failed to initialize application:\n{e}")
        except Exception:
            print(f"CRITICAL ERROR: Failed to open TunnelUI: {e}")
        return None
