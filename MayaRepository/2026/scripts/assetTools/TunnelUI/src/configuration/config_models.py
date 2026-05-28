"""
Configuration models for TunnelUI Asset Browser.

This module defines the configuration data structures used throughout the application.
Enhanced with multi-DCC application support for Maya, Unreal, Blender, and standalone modes.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum
import json
import os
import logging
import subprocess


class DCCApplication(Enum):
    """Enumeration of supported DCC applications"""

    MAYA = "maya"
    UNREAL = "unreal"
    BLENDER = "blender"
    STANDALONE = "standalone"


@dataclass
class DCCCapabilities:
    """Defines what capabilities a DCC application supports"""

    name: str
    version: Optional[str] = None
    python_api_available: bool = False
    supported_formats: List[str] = field(default_factory=list)
    import_types: List[str] = field(default_factory=list)  # mesh, material, texture, scene
    export_types: List[str] = field(default_factory=list)
    has_scene_graph: bool = True
    has_material_editor: bool = True
    has_asset_browser: bool = False

    # Maya-specific import capabilities
    maya_import_ready: bool = False
    usd_support: bool = False
    imagemagick_available: bool = False


@dataclass
class MayaImportSettings:
    """Enhanced Maya-specific import settings"""

    # Core import settings (existing)
    import_materials: bool = True
    import_textures: bool = True
    import_animations: bool = False
    import_as_reference: bool = False

    # Maya importer specific settings
    material_type: str = "usd_preview_surface"  # usd_preview_surface only for now
    texture_format: str = "png"  # png, exr, jpg
    texture_resolution: str = "2K"  # 1K, 2K, 4K, original
    create_shading_groups: bool = True
    organize_in_groups: bool = True

    # Cache settings
    use_import_cache: bool = True
    cache_location: str = "{library_root}/TunnelUI_Import_Cache/"
    cache_max_size_gb: float = 10.0
    cache_cleanup_days: int = 30  # 0 = never auto-clear
    validate_cache_on_startup: bool = True
    auto_cleanup_enabled: bool = True
    cleanup_threshold_gb: float = 8.0

    # Texture processing
    imagemagick_path: str = "auto"  # auto-detect or explicit path
    process_textures: bool = True
    standardize_naming: bool = True

    # Texture type selections (which texture types to import)
    enabled_texture_types: Dict[str, bool] = field(
        default_factory=lambda: {
            "diffuse": True,
            "normal": True,
            "roughness": True,
            "metallic": True,
            "ao": True,
            "displacement": True,
            "emissive": True,
            "opacity": True,
        }
    )

    # Material creation
    create_materials: bool = True
    material_naming_template: str = "M_{asset_name}_{asset_id}"
    override_existing_materials: bool = False

    # Import behavior
    group_naming_template: str = "{asset_name}_{asset_id}_GRP"
    import_at_origin: bool = True
    replace_existing_assets: bool = False


@dataclass
class UnrealImportSettings:
    """Unreal Engine-specific import settings"""

    import_materials: bool = True
    import_textures: bool = True
    import_animations: bool = False
    generate_lods: bool = True
    create_material_instances: bool = True
    target_content_path: str = "/Game/ImportedAssets"
    combine_meshes: bool = False


@dataclass
class StandaloneSettings:
    """Standalone mode settings"""

    default_action: str = "open_file"  # open_file, open_explorer
    open_with_system_app: bool = True
    show_file_location: bool = False


@dataclass
class ImportCacheConfig:
    """Import cache management configuration"""

    cache_root: str = "{library_root}/TunnelUI_Import_Cache/"
    max_cache_size_gb: float = 10.0
    cleanup_strategy: str = "lru"  # lru, age, manual
    compression_enabled: bool = False
    cache_index_file: str = "import_cache_index.json"
    auto_cleanup_enabled: bool = True
    cleanup_threshold_gb: float = 8.0  # Start cleanup when cache exceeds this


@dataclass
class AssetLibraryConfig:
    """Enhanced configuration with multi-DCC support"""

    # Core paths (maintained for compatibility)
    metadata_path: str = r"L:\megaScansMetadata"
    assets_path: str = r"B:\MegascansLib\Zips"

    # UI settings
    thumbnail_size: int = 150
    grid_spacing: int = 10
    window_width: int = 900
    window_height: int = 800

    # Performance settings
    max_concurrent_loads: int = 10
    cache_size: int = 100

    # Maya integration (maintained for compatibility)
    maya_mode: bool = True
    stylesheet_path: Optional[str] = None

    # Advanced settings
    debug_mode: bool = False
    log_level: str = "INFO"

    # Multi-DCC application settings
    target_application: str = "auto"  # auto, maya, unreal, blender, standalone
    application_override: Optional[str] = None

    # Application-specific settings
    maya_settings: MayaImportSettings = field(default_factory=MayaImportSettings)
    unreal_settings: UnrealImportSettings = field(default_factory=UnrealImportSettings)
    standalone_settings: StandaloneSettings = field(default_factory=StandaloneSettings)

    # UI behavior settings
    show_application_status: bool = True
    remember_import_options: bool = True
    confirm_destructive_imports: bool = True


@dataclass
class AppEnvironment:
    """Enhanced environment detection for multi-DCC support"""

    # Current detection (maintained for compatibility)
    is_maya: bool = field(default=False)
    maya_version: Optional[str] = field(default=None)

    # Enhanced multi-DCC detection
    detected_application: DCCApplication = field(default=DCCApplication.STANDALONE)
    user_override: Optional[DCCApplication] = field(default=None)
    available_applications: Dict[DCCApplication, DCCCapabilities] = field(default_factory=dict)

    # Application state
    app_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    config_path: Path = field(default=None)

    def __post_init__(self):
        if self.config_path is None:
            self.config_path = self.app_root / "config" / "tunnel_config.json"

        # Initialize logger for this environment
        self.logger = logging.getLogger(__name__)

    def detect_maya_environment(self) -> bool:
        """Legacy Maya detection method for backward compatibility"""
        try:
            import maya.cmds as cmds

            self.is_maya = True
            self.maya_version = cmds.about(version=True)
            return True
        except ImportError:
            self.is_maya = False
            self.maya_version = None
            return False

    def detect_all_applications(self) -> Dict[DCCApplication, DCCCapabilities]:
        """Detect all available DCC applications and their capabilities"""
        capabilities = {}

        # Maya Detection
        maya_caps = self._detect_maya()
        if maya_caps:
            capabilities[DCCApplication.MAYA] = maya_caps
            # Maintain backward compatibility
            self.is_maya = True
            self.maya_version = maya_caps.version

        # Unreal Detection
        unreal_caps = self._detect_unreal()
        if unreal_caps:
            capabilities[DCCApplication.UNREAL] = unreal_caps

        # Blender Detection
        blender_caps = self._detect_blender()
        if blender_caps:
            capabilities[DCCApplication.BLENDER] = blender_caps

        # Standalone always available
        capabilities[DCCApplication.STANDALONE] = self._get_standalone_capabilities()

        self.available_applications = capabilities

        # Set primary detected application
        if DCCApplication.MAYA in capabilities:
            self.detected_application = DCCApplication.MAYA
        elif DCCApplication.UNREAL in capabilities:
            self.detected_application = DCCApplication.UNREAL
        elif DCCApplication.BLENDER in capabilities:
            self.detected_application = DCCApplication.BLENDER
        else:
            self.detected_application = DCCApplication.STANDALONE

        self.logger.info(f"Detected applications: {list(capabilities.keys())}")
        self.logger.info(f"Primary application: {self.detected_application.value}")

        return capabilities

    def _detect_maya(self) -> Optional[DCCCapabilities]:
        """Detect Maya environment and capabilities for import operations"""
        try:
            import maya.cmds as cmds
            import pymel.core as pm

            version = cmds.about(version=True)
            self.logger.info(f"Maya detected: {version}")

            # Enhanced capability detection for Maya importer
            maya_capabilities = DCCCapabilities(
                name="Autodesk Maya",
                version=version,
                python_api_available=True,
                supported_formats=[".ma", ".mb", ".fbx", ".obj", ".abc", ".usd", ".usda", ".usdz"],
                import_types=[
                    "mesh",
                    "material",
                    "texture",
                    "scene",
                    "animation",
                    "usd_preview_surface",
                ],
                export_types=["mesh", "material", "texture", "scene", "animation"],
                has_scene_graph=True,
                has_material_editor=True,
                has_asset_browser=False,
            )

            # Detect additional Maya import capabilities
            maya_capabilities.maya_import_ready = self._validate_maya_import_environment(cmds, pm)
            maya_capabilities.usd_support = self._check_maya_usd_support(cmds)
            maya_capabilities.imagemagick_available = self._check_imagemagick_availability()

            self.logger.info(
                f"Maya capabilities detected - import ready: {maya_capabilities.maya_import_ready}"
            )
            return maya_capabilities
        except ImportError as e:
            self.logger.warning(f"Maya import detection failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in Maya detection: {e}")
            return None

    def _validate_maya_import_environment(self, cmds, pm) -> bool:
        """Validate Maya environment is ready for import operations"""
        try:
            # Check if we can create basic nodes
            test_node = cmds.createNode("transform", name="tunnelui_test_node")
            cmds.delete(test_node)

            # Check if we can access scene information
            cmds.file(query=True, exists=True)

            # USD Preview Surface check is optional - don't fail if not available
            try:
                usd_available = cmds.nodeType("usdPreviewSurface", isTypeName=True)
                self.logger.debug(f"USD Preview Surface available: {usd_available}")
            except Exception as usd_error:
                self.logger.debug(f"USD Preview Surface not available (non-critical): {usd_error}")

            return True
        except Exception as e:
            self.logger.warning(f"Maya import environment validation failed: {e}")
            return False

    def _check_maya_usd_support(self, cmds) -> bool:
        """Check if Maya has USD support"""
        try:
            # Check if USD Preview Surface node type exists
            return cmds.nodeType("usdPreviewSurface", isTypeName=True)
        except Exception:
            return False

    def _check_imagemagick_availability(self) -> bool:
        """Check if ImageMagick is available for texture processing"""
        try:
            import subprocess

            # Try common ImageMagick paths
            possible_paths = [
                "magick",
                "magick.exe",
                r"C:\Program Files\ImageMagick\magick.exe",
                r"C:\Program Files\Autodesk\Maya2023\bin\magick.exe",
                r"C:\Program Files\Autodesk\Maya2024\bin\magick.exe",
                r"C:\Program Files\Autodesk\Maya2025\bin\magick.exe",
                r"C:\Program Files\Autodesk\Maya2026\bin\magick.exe",
            ]

            for path in possible_paths:
                try:
                    # Hide console window on Windows
                    kwargs = {"capture_output": True, "timeout": 5, "text": True}
                    if os.name == "nt":  # Windows
                        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                    result = subprocess.run([path, "--version"], **kwargs)
                    if result.returncode == 0:
                        self.logger.debug(f"ImageMagick found at: {path}")
                        return True
                except Exception:
                    continue

            return False
        except Exception:
            return False

    def _detect_unreal(self) -> Optional[DCCCapabilities]:
        """Detect Unreal Engine environment and capabilities"""
        try:
            import unreal

            version = unreal.SystemLibrary.get_engine_version()

            return DCCCapabilities(
                name="Unreal Engine",
                version=version,
                python_api_available=True,
                supported_formats=[".fbx", ".uasset", ".png", ".exr", ".hdr"],
                import_types=["static_mesh", "material", "texture"],
                export_types=["static_mesh", "material", "texture"],
                has_scene_graph=True,
                has_material_editor=True,
                has_asset_browser=True,
            )
        except ImportError:
            return None

    def _detect_blender(self) -> Optional[DCCCapabilities]:
        """Detect Blender environment and capabilities"""
        try:
            import bpy

            version = bpy.app.version_string

            return DCCCapabilities(
                name="Blender",
                version=version,
                python_api_available=True,
                supported_formats=[".blend", ".fbx", ".obj", ".gltf"],
                import_types=["mesh", "material", "texture", "scene", "animation"],
                export_types=["mesh", "material", "texture", "scene", "animation"],
                has_scene_graph=True,
                has_material_editor=True,
                has_asset_browser=False,
            )
        except ImportError:
            return None

    def _get_standalone_capabilities(self) -> DCCCapabilities:
        """Get capabilities for standalone mode"""
        return DCCCapabilities(
            name="Standalone Mode",
            version="1.0",
            python_api_available=False,
            supported_formats=[],  # All formats supported (just opened)
            import_types=["file_open"],
            export_types=["file_copy"],
            has_scene_graph=False,
            has_material_editor=False,
            has_asset_browser=True,
        )

    def get_active_application(self) -> DCCApplication:
        """Get the currently active application (considering user override)"""
        if self.user_override and self.user_override in self.available_applications:
            return self.user_override
        return self.detected_application

    def get_active_capabilities(self) -> DCCCapabilities:
        """Get capabilities for the currently active application"""
        active_app = self.get_active_application()
        return self.available_applications.get(active_app, self._get_standalone_capabilities())

    def set_user_override(self, application: DCCApplication) -> bool:
        """Set user override for application selection"""
        if application in self.available_applications:
            self.user_override = application
            self.logger.info(f"User override set to: {application.value}")
            return True
        self.logger.warning(f"Cannot set override to unavailable application: {application.value}")
        return False

    def clear_user_override(self):
        """Clear user override and return to auto-detection"""
        self.user_override = None
        self.logger.info("User override cleared, returning to auto-detection")

    def get_application_display_name(self) -> str:
        """Get display name for active application"""
        caps = self.get_active_capabilities()
        active_app = self.get_active_application()

        if caps.version:
            return f"{caps.name} {caps.version}"
        return caps.name

    def get_import_button_text(self) -> str:
        """Get appropriate import button text for active application"""
        active_app = self.get_active_application()

        button_texts = {
            DCCApplication.MAYA: "Import to Maya",
            DCCApplication.UNREAL: "Import to Unreal",
            DCCApplication.BLENDER: "Import to Blender",
            DCCApplication.STANDALONE: "Open File",
        }

        return button_texts.get(active_app, "Import Asset")

    def get_maya_main_window(self):
        """Get Maya main window for proper parenting (backward compatibility)"""
        if not self.is_maya:
            return None

        try:
            import maya.OpenMayaUI as OMUI
            import shiboken6
            from PySide6.QtWidgets import QWidget

            maya_win = OMUI.MQtUtil.mainWindow()
            return shiboken6.wrapInstance(int(maya_win), QWidget)
        except Exception as e:
            self.logger.error(f"Failed to get Maya main window: {e}")
            return None

    def get_maya_stylesheet_path(self) -> Optional[str]:
        """Get Maya stylesheet path if available (backward compatibility)"""
        if not self.is_maya:
            return None

        try:
            import mayaFilePaths

            return f"{mayaFilePaths.styleSheetFilepath}/dark.qss"
        except (ImportError, AttributeError):
            return None
