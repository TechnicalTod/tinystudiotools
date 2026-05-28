"""
Asset management service for TunnelUI Asset Browser.

This service coordinates high-level asset operations and business logic.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from data.repositories.metadata_repository import AssetMetadataRepository
from data.repositories.import_repository import AssetImportRepository
from services.asset_search_service import AssetSearchService


class AssetManagementService:
    """High-level service for managing assets and coordinating operations"""

    def __init__(
        self,
        metadata_repo: AssetMetadataRepository,
        import_repo: AssetImportRepository,
        search_service: AssetSearchService,
    ):
        self.metadata_repo = metadata_repo
        self.import_repo = import_repo
        self.search_service = search_service
        self.logger = logging.getLogger(__name__)

        # Maya import service (set later if Maya is available)
        self.maya_import_service = None

    def set_maya_import_service(self, maya_import_service) -> None:
        """Set the Maya import service for asset importing"""
        self.maya_import_service = maya_import_service
        self.logger.info("Maya import service connected to asset management")

    async def import_asset_to_maya(self, asset_id: str, progress_callback=None):
        """Import asset to Maya using the Maya import service"""
        if not self.maya_import_service:
            raise RuntimeError("Maya import service not available")

        return await self.maya_import_service.import_asset_to_maya(asset_id, progress_callback)

    def get_import_capabilities(self) -> Dict[str, Any]:
        """Get current import capabilities"""
        capabilities = {
            "maya_available": self.maya_import_service is not None,
            "cache_enabled": False,
            "supported_formats": [],
        }

        if self.maya_import_service:
            capabilities.update(
                {
                    "cache_enabled": True,
                    "supported_formats": ["fbx", "obj", "ma", "mb", "usd", "usda", "usdz"],
                    "material_creation": True,
                    "texture_processing": True,
                }
            )

        return capabilities

    def get_cache_statistics(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics if Maya import service is available"""
        if not self.maya_import_service:
            return None

        try:
            cache_stats = self.maya_import_service.cache_service.get_cache_statistics()
            return {
                "entry_count": cache_stats.entry_count,
                "total_size_mb": cache_stats.total_size_mb,
                "last_cleanup": cache_stats.last_cleanup,
                "cache_hits": cache_stats.cache_hits,
                "cache_misses": cache_stats.cache_misses,
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return None

    def clear_import_cache(self, asset_ids: Optional[List[str]] = None) -> bool:
        """Clear import cache"""
        if not self.maya_import_service:
            return False

        try:
            if asset_ids:
                return self.maya_import_service.cache_service.clear_cache(asset_ids)
            else:
                return self.maya_import_service.cache_service.clear_all_cache()
        except Exception as e:
            self.logger.error(f"Failed to clear import cache: {e}")
            return False

    # Asset Information Methods
    def get_asset_name(self, asset_id: str) -> str:
        """Get display name for an asset"""
        return self.search_service.get_asset_name(asset_id)

    def get_asset_image_path(
        self, asset_id: str, category: str, thumbnail: bool = True
    ) -> Optional[Path]:
        """Get path to asset image"""
        return self.metadata_repo.get_asset_image_path(asset_id, category, thumbnail)

    def get_asset_metadata(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific asset"""
        return self.metadata_repo.get_asset_metadata(asset_id)

    def get_asset_categories(self) -> List[str]:
        """Get list of available asset categories"""
        return self.metadata_repo.get_categories()

    def get_category_assets(self, category: str, limit: Optional[int] = None) -> List[str]:
        """Get asset IDs for a specific category"""
        return self.metadata_repo.get_category_assets(category, limit)

    # Category Management
    def get_categories(self) -> List[str]:
        """Get list of available asset categories"""
        return self.search_service.get_available_categories()

    def get_category_display_name(self, category: str) -> str:
        """Get display name for category"""
        return self.search_service.get_category_display_name(category)

    def get_category_asset_count(self, category: str) -> int:
        """Get the number of assets in a category"""
        return self.search_service.get_category_asset_count(category)

    def get_assets_in_category(self, category: str) -> List[str]:
        """Get all assets in a specific category"""
        return self.search_service.get_all_assets_in_category(category)

    # Search Operations
    def search_assets(
        self, query: str, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[str]:
        """Search for assets matching query"""
        return self.search_service.search_assets(query, category, limit)

    def get_search_keywords(self) -> List[str]:
        """Get available search keywords (lazy loaded)"""
        return self.search_service.get_search_keywords()

    def get_asset_keywords(self, asset_id: str) -> List[str]:
        """Get keywords for a specific asset"""
        return self.search_service.get_asset_keywords(asset_id)

    # Asset Import Operations
    def prepare_asset_for_import(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Prepare asset for import by validating zip file exists"""
        return self.import_repo.prepare_asset_for_import(asset_id)

    def get_asset_import_info(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get import information for an asset"""
        zip_filename = self.import_repo.find_asset_zip(asset_id)
        if zip_filename:
            return self.import_repo.get_asset_info(asset_id, zip_filename)
        return None

    # Library Management
    def validate_library_integrity(self) -> Dict[str, Any]:
        """Validate integrity of the asset library"""
        results = {
            "metadata_valid": True,
            "import_data_valid": True,
            "missing_files": [],
            "errors": [],
        }

        try:
            # Validate metadata repository
            if not self.metadata_repo.validate_metadata():
                results["metadata_valid"] = False
                results["errors"].append("Metadata validation failed")

            # Validate import repository
            if not self.import_repo.validate_zip_index():
                results["import_data_valid"] = False
                results["errors"].append("Import data validation failed")

            # Check for missing files
            categories = self.get_categories()
            for category in categories[:3]:  # Limit check to first 3 categories for performance
                assets = self.get_assets_in_category(category)
                for asset_id in assets[:10]:  # Limit to first 10 assets per category
                    image_path = self.get_asset_image_path(asset_id, category, thumbnail=True)
                    if image_path and not image_path.exists():
                        results["missing_files"].append(str(image_path))

            self.logger.info(
                f"Library integrity check completed: {len(results['errors'])} errors found"
            )

        except Exception as e:
            self.logger.error(f"Library integrity check failed: {e}")
            results["errors"].append(str(e))

        return results

    def get_library_statistics(self) -> Dict[str, Any]:
        """Get comprehensive library statistics"""
        try:
            categories = self.get_categories()
            total_assets = 0
            category_counts = {}

            for category in categories:
                count = self.get_category_asset_count(category)
                category_counts[category] = count
                total_assets += count

            return {
                "total_assets": total_assets,
                "total_categories": len(categories),
                "category_breakdown": category_counts,
                "search_keywords_count": len(self.search_service.get_search_keywords()),
            }
        except Exception as e:
            self.logger.error(f"Failed to get library statistics: {e}")
            return {"error": str(e)}

    # Search Performance
    def get_search_performance_stats(self) -> Dict[str, Any]:
        """Get search performance statistics"""
        return self.search_service.get_search_statistics()

    # Cache Management
    def clear_all_caches(self) -> None:
        """Clear all service caches"""
        self.logger.info("Clearing all caches")
        self.search_service.clear_cache()
        self.metadata_repo.refresh_cache()
        self.import_repo.refresh_cache()

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            "search_service": self.search_service.get_search_statistics(),
            "metadata_repository": "active",
            "import_repository": "active",
        }

    def get_asset_zip_path(self, asset_id: str) -> Optional[Path]:
        """
        Get the path to the zip file for a specific asset.

        Args:
            asset_id: Asset identifier

        Returns:
            Path to asset zip file, or None if not found
        """
        try:
            # First, find which zip file contains this asset
            zip_filename = self.import_repo.find_asset_zip(asset_id)
            if not zip_filename:
                self.logger.warning(f"No zip file found for asset: {asset_id}")
                return None

            # Get the full path to the zip file
            zip_path = self.import_repo.get_asset_zip_path(asset_id, zip_filename)
            return zip_path

        except Exception as e:
            self.logger.error(f"Failed to get zip path for asset {asset_id}: {e}")
            return None

    # Maya Import Integration
    def set_maya_import_service(self, maya_import_service) -> None:
        """Set the Maya import service for asset importing"""
        self.maya_import_service = maya_import_service
        self.logger.info("Maya import service connected to asset management")

    async def import_asset_to_maya(self, asset_id: str, progress_callback=None):
        """Import asset to Maya using the Maya import service"""
        if not self.maya_import_service:
            raise RuntimeError("Maya import service not available")

        return await self.maya_import_service.import_asset_to_maya(asset_id, progress_callback)

    def get_import_capabilities(self) -> Dict[str, Any]:
        """Get current import capabilities"""
        capabilities = {
            "maya_available": self.maya_import_service is not None,
            "cache_enabled": False,
            "supported_formats": [],
        }

        if self.maya_import_service:
            capabilities.update(
                {
                    "cache_enabled": True,
                    "supported_formats": ["fbx", "obj", "ma", "mb", "usd", "usda", "usdz"],
                    "material_creation": True,
                    "texture_processing": True,
                }
            )

        return capabilities

    def get_cache_statistics(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics if Maya import service is available"""
        if not self.maya_import_service:
            return None

        try:
            cache_stats = self.maya_import_service.cache_service.get_cache_statistics()
            return {
                "entry_count": cache_stats.entry_count,
                "total_size_mb": cache_stats.total_size_mb,
                "last_cleanup": cache_stats.last_cleanup,
                "cache_hits": cache_stats.cache_hits,
                "cache_misses": cache_stats.cache_misses,
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return None

    def clear_import_cache(self, asset_ids: Optional[List[str]] = None) -> bool:
        """Clear import cache"""
        if not self.maya_import_service:
            return False

        try:
            if asset_ids:
                return self.maya_import_service.cache_service.clear_cache(asset_ids)
            else:
                return self.maya_import_service.cache_service.clear_all_cache()
        except Exception as e:
            self.logger.error(f"Failed to clear import cache: {e}")
            return False
