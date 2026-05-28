"""
Maya Import Service

High-level Maya import orchestration service.
Coordinates cache, texture processing, and Maya bridge services.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Callable, List

# Add crash logger import (optional)
import sys

try:
    sys.path.append(
        str(Path(__file__).parent.parent.parent.parent)
    )  # Go up 4 levels to TunnelUI root
    from crash_logger import crash_logger
except ImportError:
    # Fallback logger if crash_logger import fails
    class FallbackLogger:
        def log(self, message):
            print(f"🔍 {message}")

    crash_logger = FallbackLogger()

from services.asset_management_service import AssetManagementService
from configuration.config_manager import ConfigurationManager
from .import_cache_service import ImportCacheService
from .texture_processing_service import TextureProcessingService
from .maya_bridge_service import MayaBridgeService
from .import_models import (
    ImportResult,
    ImportPreview,
    AssetInfo,
    TunnelUIImportError,
    MayaEnvironmentError,
    ImportStep,
)


class MayaImportService:
    """High-level Maya import orchestration service"""

    def __init__(
        self,
        asset_service: AssetManagementService,
        cache_service: ImportCacheService,
        maya_bridge: MayaBridgeService,
        texture_processor: TextureProcessingService,
        config_manager: ConfigurationManager,
    ):
        """
        Initialize Maya import service

        Args:
            asset_service: Asset management service
            cache_service: Import cache service
            maya_bridge: Maya bridge service
            texture_processor: Texture processing service
            config_manager: Configuration manager
        """
        self.asset_service = asset_service
        self.cache_service = cache_service
        self.maya_bridge = maya_bridge
        self.texture_processor = texture_processor
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    async def import_asset_to_maya(
        self, asset_id: str, progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> ImportResult:
        """
        Complete asset import workflow:
        1. Check cache for existing processed asset
        2. If not cached: extract → process textures → cache
        3. Import to Maya with material creation

        Args:
            asset_id: Asset identifier
            progress_callback: Optional progress callback function

        Returns:
            ImportResult with import details
        """
        start_time = time.time()
        result = ImportResult(success=False, asset_id=asset_id)

        try:
            # Step 1: Validation
            if progress_callback:
                progress_callback("Validating environment...", 5)

            if not self.validate_maya_environment():
                raise MayaEnvironmentError("Maya environment not ready for import")

            result.processing_steps.append("Environment validated")

            # Step 2: Get asset information
            if progress_callback:
                progress_callback("Loading asset information...", 10)

            asset_info = await self._get_asset_info(asset_id)
            if not asset_info:
                raise TunnelUIImportError(f"Asset {asset_id} not found")

            result.processing_steps.append("Asset info loaded")

            # Step 3: Check cache
            if progress_callback:
                progress_callback("Checking import cache...", 15)

            cache_entry = None
            if self.cache_service.is_asset_cached(asset_id):
                cache_entry = self.cache_service.get_cached_asset_entry(asset_id)
                result.processing_steps.append("Found in cache")
            else:
                result.processing_steps.append("Not in cache")

            # Step 4: Process textures if not cached
            if cache_entry is None:
                if progress_callback:
                    progress_callback("Processing textures...", 20)

                processed_result = await self._process_asset_textures(asset_info, progress_callback)

                if not processed_result.success:
                    raise TunnelUIImportError(
                        f"Texture processing failed: {processed_result.error_details}"
                    )

                # Cache the processed asset
                cache_entry = self.cache_service.cache_processed_asset(
                    asset_id=asset_id,
                    source_info=asset_info,
                    processed_files=processed_result.processed_textures,
                    geometry_files=processed_result.geometry_files,
                    metadata_file=None,  # TODO: Handle metadata file
                )

                result.processing_steps.append("Textures processed and cached")
            else:
                result.processing_steps.append("Using cached textures")

            # Step 5: Import to Maya
            if progress_callback:
                progress_callback("Importing geometry to Maya...", 70)

            crash_logger.log("CHECKPOINT A: Starting geometry import...")
            imported_objects = await self._import_geometry_to_maya(cache_entry, asset_info)
            result.imported_objects = imported_objects
            result.processing_steps.append(f"Imported {len(imported_objects)} objects")
            crash_logger.log(
                f"CHECKPOINT A: Geometry import completed - {len(imported_objects)} objects"
            )

            # Step 6: Create materials
            if progress_callback:
                progress_callback("Creating materials...", 85)

            crash_logger.log("CHECKPOINT B: Starting material creation...")
            created_materials = await self._create_maya_materials(
                cache_entry, asset_info, imported_objects
            )
            result.created_materials = created_materials
            result.processing_steps.append(f"Created {len(created_materials)} materials")
            crash_logger.log(
                f"CHECKPOINT B: Material creation completed - {len(created_materials)} materials"
            )

            # Success! (Skip scene organization since grouping is disabled)
            result.success = True
            result.cache_entry = cache_entry
            result.import_duration = time.time() - start_time

            if progress_callback:
                progress_callback("Import complete!", 100)

            crash_logger.log(
                f"CHECKPOINT D: Import workflow completed successfully in {result.import_duration:.2f}s"
            )

            self.logger.info(
                f"Successfully imported asset {asset_id} in {result.import_duration:.2f}s"
            )

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.import_duration = time.time() - start_time
            self.logger.error(f"Failed to import asset {asset_id}: {e}")

        return result

    def validate_maya_environment(self) -> bool:
        """
        Validate Maya is available and ready for import

        Returns:
            True if Maya environment is valid
        """
        try:
            if not self.maya_bridge.maya_available:
                self.logger.error("Maya bridge not available")
                return False

            if not self.maya_bridge.validate_maya_environment():
                self.logger.error("Maya environment validation failed")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Maya environment validation error: {e}")
            return False

    def get_import_preview(self, asset_id: str) -> ImportPreview:
        """
        Generate preview of what will be imported

        Args:
            asset_id: Asset identifier

        Returns:
            ImportPreview with import details
        """
        try:
            # Get asset info
            # Note: This would need to be made async in real implementation
            asset_info = AssetInfo(asset_id=asset_id, asset_name=f"Asset_{asset_id}")

            # Check if cached
            will_use_cache = self.cache_service.is_asset_cached(asset_id)

            # Estimate import time
            if will_use_cache:
                estimated_time = 5.0  # Fast cached import
            else:
                estimated_time = 30.0  # Full processing

            # Generate material and group names
            config = self.config_manager.get_config()
            material_name = config.maya_settings.material_naming_template.format(
                asset_name=asset_info.asset_name, asset_id=asset_id
            )
            group_name = config.maya_settings.group_naming_template.format(
                asset_name=asset_info.asset_name, asset_id=asset_id
            )

            return ImportPreview(
                asset_info=asset_info,
                will_use_cache=will_use_cache,
                estimated_import_time=estimated_time,
                material_name=material_name,
                group_name=group_name,
            )

        except Exception as e:
            self.logger.error(f"Failed to generate import preview for {asset_id}: {e}")
            # Return basic preview on error
            return ImportPreview(
                asset_info=AssetInfo(asset_id=asset_id, asset_name=f"Asset_{asset_id}"),
                will_use_cache=False,
                estimated_import_time=30.0,
                warnings=[f"Preview generation failed: {e}"],
            )

    async def _get_asset_info(self, asset_id: str) -> Optional[AssetInfo]:
        """Get asset information from asset service"""
        try:
            # Get asset zip path
            zip_path = self.asset_service.get_asset_zip_path(asset_id)
            if not zip_path:
                return None

            # Get asset metadata if available
            metadata = {}  # TODO: Get from asset service

            # Create asset info
            asset_info = AssetInfo(
                asset_id=asset_id,
                asset_name=asset_id,  # TODO: Get proper name from metadata
                zip_path=zip_path,
                metadata=metadata,
            )

            return asset_info

        except Exception as e:
            self.logger.error(f"Failed to get asset info for {asset_id}: {e}")
            return None

    async def _process_asset_textures(
        self,
        asset_info: AssetInfo,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        """Process asset textures using texture processing service"""
        try:
            # Create output directory for this asset
            config = self.config_manager.get_config()
            cache_root = Path(
                config.maya_settings.cache_location.replace("{library_root}", config.metadata_path)
            )
            output_dir = cache_root / f"{asset_info.asset_name}_{asset_info.asset_id}"

            # Process textures
            def texture_progress(step: str, percentage: float):
                if progress_callback:
                    # Map texture processing progress to overall progress (20-70%)
                    overall_progress = 20 + (percentage / 100.0) * 50
                    progress_callback(step, overall_progress)

            result = self.texture_processor.extract_and_process_textures(
                zip_path=asset_info.zip_path,
                output_directory=output_dir,
                asset_info=asset_info,
                progress_callback=texture_progress,
            )

            return result

        except Exception as e:
            self.logger.error(f"Failed to process textures for {asset_info.asset_id}: {e}")
            raise

    async def _import_geometry_to_maya(self, cache_entry, asset_info: AssetInfo) -> List[str]:
        """Import geometry files to Maya (LOD0 only)"""
        imported_objects = []

        try:
            crash_logger.log("🔍 GEO-1: Starting geometry import method...")
            config = self.config_manager.get_config().maya_settings

            crash_logger.log("🔍 GEO-2: Starting LOD0 filtering...")
            # Filter to LOD0 files only (even from cached files)
            lod0_files = []
            for geometry_file in cache_entry.geometry_files:
                if "LOD0" in geometry_file.name:
                    lod0_files.append(geometry_file)

            if lod0_files:
                geometry_files_to_import = lod0_files
                self.logger.info(f"Using LOD0 files only: {[f.name for f in lod0_files]}")
                crash_logger.log(
                    f"🔍 GEO-2: LOD0 filtering completed - {len(lod0_files)} files selected"
                )
            elif cache_entry.geometry_files:
                # Fallback: use first geometry file if no LOD0 found
                geometry_files_to_import = [cache_entry.geometry_files[0]]
                self.logger.info(
                    f"No LOD0 found, using first geometry file: {cache_entry.geometry_files[0].name}"
                )
                crash_logger.log(f"🔍 GEO-2: LOD0 filtering completed - using fallback file")
            else:
                self.logger.warning("No geometry files found in cache")
                crash_logger.log("🔍 GEO-2: LOD0 filtering completed - no files found")
                return []

            crash_logger.log(
                f"🔍 GEO-3: Starting import of {len(geometry_files_to_import)} geometry files..."
            )

            # Import each selected geometry file
            for i, geometry_file in enumerate(geometry_files_to_import):
                crash_logger.log(f"🔍 GEO-4.{i}: Processing file {geometry_file.name}...")

                if geometry_file.exists():
                    crash_logger.log(
                        f"🔍 GEO-5.{i}: File exists, calling maya_bridge.import_geometry..."
                    )

                    objects = self.maya_bridge.import_geometry(
                        file_path=geometry_file,
                        asset_name=asset_info.asset_name,
                        import_settings=config,
                    )

                    crash_logger.log(
                        f"🔍 GEO-6.{i}: import_geometry returned {len(objects)} objects"
                    )
                    imported_objects.extend(objects)
                    crash_logger.log(
                        f"🔍 GEO-7.{i}: Extended imported_objects, total now: {len(imported_objects)}"
                    )
                else:
                    self.logger.warning(f"Geometry file does not exist: {geometry_file}")
                    crash_logger.log(f"🔍 GEO-4.{i}: File does not exist - skipping")

            crash_logger.log(
                f"🔍 GEO-8: Geometry import loop completed, returning {len(imported_objects)} objects"
            )
            return imported_objects

        except Exception as e:
            crash_logger.log(f"GEO-ERROR: Exception in geometry import: {e}")
            self.logger.error(f"Failed to import geometry for {asset_info.asset_id}: {e}")
            raise

    async def _create_maya_materials(
        self, cache_entry, asset_info: AssetInfo, imported_objects: List[str]
    ) -> List[str]:
        """Create Maya materials and assign to objects"""
        created_materials = []

        try:
            crash_logger.log("🔍 MAT-1: Starting material creation...")
            config = self.config_manager.get_config().maya_settings

            # FIX: Use the correct attribute name - processed_files (not processed_textures)
            texture_files = (
                cache_entry.processed_files if hasattr(cache_entry, "processed_files") else {}
            )
            crash_logger.log(f"MAT-2: Config loaded, processing {len(texture_files)} textures...")

            # Check if cache_entry has processed_files attribute (correct name)
            if hasattr(cache_entry, "processed_files") and cache_entry.processed_files:
                crash_logger.log("MAT-3: About to call maya_bridge.create_usd_preview_material...")

                # Generate material name
                material_name_to_create = f"M_{asset_info.asset_name}"
                crash_logger.log(f"MAT-3.1: Creating material with name: {material_name_to_create}")

                material_name = self.maya_bridge.create_usd_preview_material(
                    material_name=material_name_to_create,
                    texture_paths=cache_entry.processed_files,  # FIX: Use correct attribute
                    asset_info=asset_info,
                )

                crash_logger.log(f"MAT-4: Material created: {material_name}")
                created_materials.append(material_name)

                crash_logger.log(
                    f"MAT-5: About to assign material to {len(imported_objects)} objects..."
                )

                # Assign material to imported objects
                self.maya_bridge.assign_material_to_objects(
                    material_name=material_name, object_names=imported_objects
                )

                crash_logger.log("MAT-6: Material assignment completed")

            else:
                crash_logger.log("MAT-3: No processed_files found, skipping material creation")
                crash_logger.log(
                    f"MAT-3.1: cache_entry attributes: {dir(cache_entry) if cache_entry else 'None'}"
                )

            crash_logger.log(
                f"MAT-7: Material creation completed, returning {len(created_materials)} materials"
            )
            return created_materials

        except Exception as e:
            crash_logger.log(f"MAT-ERROR: Exception in material creation: {e}")
            self.logger.error(f"Failed to create materials for {asset_info.asset_id}: {e}")
            raise
