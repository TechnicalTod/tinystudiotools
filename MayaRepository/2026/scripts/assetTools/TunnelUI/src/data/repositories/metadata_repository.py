"""
File System implementation of the Asset Metadata Repository.

This module provides concrete implementation for metadata access using
the local file system and JSON files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_repository import AssetMetadataRepository


class FileSystemMetadataRepository(AssetMetadataRepository):
    """File system based implementation of asset metadata repository"""

    def __init__(self, config):
        super().__init__(config)
        self.metadata_path = Path(config.metadata_path)

        # Cached data
        self._inverted_index: Optional[Dict] = None
        self._asset_groupings: Optional[Dict] = None

        # Category to directory mapping
        self.category_directories = {
            "3d": "3d",
            "3dplant": "3dplant",
            "atlas": "atlas",
            "decals": "decals",
            "brush": "brush",
            "surface": "surface",
        }

    def load_inverted_index(self) -> Dict[str, Dict[str, str]]:
        """Load inverted index from JSON file"""
        if self._inverted_index is None:
            try:
                index_path = self.metadata_path / "inverted_index_combined.json"
                self.logger.info(f"Loading inverted index from {index_path}")

                with open(index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._inverted_index = data.get("index", {})

                self.logger.info(f"Loaded {len(self._inverted_index)} index entries")

            except Exception as e:
                self._handle_error("load inverted index", e)
                self._inverted_index = {}

        return self._inverted_index

    def load_asset_groupings(self) -> Dict[str, List[str]]:
        """Load asset groupings from JSON file"""
        if self._asset_groupings is None:
            try:
                index_path = self.metadata_path / "inverted_index_combined.json"
                self.logger.info(f"Loading asset groupings from {index_path}")

                with open(index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._asset_groupings = data.get("AssetGrouping", {})

                # Log category counts
                for category, assets in self._asset_groupings.items():
                    self.logger.info(f"Category '{category}': {len(assets)} assets")

            except Exception as e:
                self._handle_error("load asset groupings", e)
                self._asset_groupings = {}

        return self._asset_groupings

    def get_asset_image_path(
        self, asset_id: str, category: str, thumbnail: bool = True
    ) -> Optional[Path]:
        """Get path to asset image file"""
        try:
            # Get the directory for this category
            category_dir = self.category_directories.get(category, category)

            # Build filename
            suffix = "_thumbnail" if thumbnail else ""
            filename = f"{asset_id}_Preview{suffix}.png"

            # Build full path
            image_path = self.metadata_path / category_dir / filename

            # Check if file exists
            if image_path.exists():
                return image_path
            else:
                if self.config.debug_mode:
                    self.logger.debug(f"Image not found: {image_path}")
                return None

        except Exception as e:
            self._handle_error(f"get image path for {asset_id}", e)
            return None

    def get_asset_metadata(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific asset"""
        try:
            # Look through all categories to find the asset
            for category_dir in self.metadata_path.iterdir():
                if category_dir.is_dir():
                    metadata_file = category_dir / f"{asset_id}_Metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            return metadata

            # Asset not found in any category
            self.logger.warning(f"Metadata not found for asset: {asset_id}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to load metadata for asset {asset_id}: {e}")
            return None

    def get_category_asset_count(self, category: str) -> int:
        """Get the number of assets in a category"""
        groupings = self.load_asset_groupings()
        return len(groupings.get(category, []))

    def get_all_categories(self) -> List[str]:
        """Get list of all available categories"""
        groupings = self.load_asset_groupings()
        return list(groupings.keys())

    def get_categories(self) -> List[str]:
        """Get list of available asset categories"""
        return self.get_all_categories()

    def get_category_assets(self, category: str, limit: Optional[int] = None) -> List[str]:
        """Get asset IDs for a specific category"""
        try:
            category_dir = self.metadata_path / category
            if not category_dir.exists():
                return []

            asset_ids = []
            for metadata_file in category_dir.glob("*_Metadata.json"):
                asset_id = metadata_file.stem.replace("_Metadata", "")
                asset_ids.append(asset_id)

                # Apply limit if specified
                if limit and len(asset_ids) >= limit:
                    break

            return asset_ids

        except Exception as e:
            self.logger.error(f"Failed to get assets for category {category}: {e}")
            return []

    def validate_metadata_integrity(self) -> Dict[str, bool]:
        """Validate the integrity of metadata files and directories"""
        validation_results = {}

        # Check if metadata path exists
        validation_results["metadata_path_exists"] = self.metadata_path.exists()

        # Check required JSON files
        required_files = ["inverted_index_combined.json"]
        for file_name in required_files:
            file_path = self.metadata_path / file_name
            validation_results[f"{file_name}_exists"] = file_path.exists()

        # Check category directories
        for category, dir_name in self.category_directories.items():
            dir_path = self.metadata_path / dir_name
            validation_results[f"{category}_directory_exists"] = dir_path.exists()

        return validation_results

    def refresh_cache(self) -> None:
        """Clear cached data to force reload"""
        self.logger.info("Refreshing metadata cache")
        self._inverted_index = None
        self._asset_groupings = None
