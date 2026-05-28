"""
Asset import repository implementation for TunnelUI Asset Browser.

This module handles zip file access and asset import operations.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any

from .base_repository import AssetImportRepository


class FileSystemImportRepository(AssetImportRepository):
    """File system based implementation of asset import repository"""

    def __init__(self, config):
        super().__init__(config)
        self.assets_path = Path(config.assets_path)
        self.metadata_path = Path(config.metadata_path)

        # Cached zip index
        self._zip_index: Optional[Dict[str, str]] = None

    def load_zip_index(self) -> Dict[str, str]:
        """Load zip index from JSON file"""
        if self._zip_index is None:
            try:
                zip_index_path = self.metadata_path / "zip_index.json"
                self.logger.info(f"Loading zip index from {zip_index_path}")

                with open(zip_index_path, "r") as f:
                    self._zip_index = json.load(f)

                self.logger.info(f"Loaded zip index with {len(self._zip_index)} entries")

            except Exception as e:
                self._handle_error("load zip index", e)
                self._zip_index = {}

        return self._zip_index

    def get_asset_zip_path(self, asset_id: str, zip_filename: str) -> Optional[Path]:
        """Get full path to asset zip file"""
        try:
            zip_path = self.assets_path / zip_filename
            return zip_path if zip_path.exists() else None
        except Exception as e:
            self._handle_error(f"get zip path for {asset_id}", e)
            return None

    def validate_asset_exists(self, asset_id: str, zip_filename: str) -> bool:
        """Check if asset zip file exists"""
        zip_path = self.get_asset_zip_path(asset_id, zip_filename)
        return zip_path is not None

    def get_asset_info(self, asset_id: str, zip_filename: str) -> Dict[str, Any]:
        """Get asset information for import"""
        try:
            zip_path = self.get_asset_zip_path(asset_id, zip_filename)

            if not zip_path:
                return {
                    "asset_id": asset_id,
                    "zip_filename": zip_filename,
                    "zip_path": "",
                    "file_size": 0,
                    "exists": False,
                    "error": "Zip file not found",
                }

            file_size = zip_path.stat().st_size if zip_path.exists() else 0

            return {
                "asset_id": asset_id,
                "zip_filename": zip_filename,
                "zip_path": str(zip_path),
                "file_size": file_size,
                "exists": zip_path.exists(),
                "error": None,
            }

        except Exception as e:
            self._handle_error(f"get asset info for {asset_id}", e)
            return {
                "asset_id": asset_id,
                "zip_filename": zip_filename,
                "zip_path": "",
                "file_size": 0,
                "exists": False,
                "error": str(e),
            }

    def find_asset_zip(self, asset_id: str) -> Optional[str]:
        """Find zip filename for a given asset ID"""
        zip_index = self.load_zip_index()
        return zip_index.get(asset_id)

    def prepare_asset_for_import(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Prepare asset for import by finding and validating zip file"""
        try:
            # Find zip filename
            zip_filename = self.find_asset_zip(asset_id)
            if not zip_filename:
                self.logger.warning(f"No zip file found for asset {asset_id}")
                return None

            # Get asset information
            asset_info = self.get_asset_info(asset_id, zip_filename)

            if not asset_info["exists"]:
                self.logger.warning(f"Zip file does not exist for asset {asset_id}: {zip_filename}")
                return None

            self.logger.info(f"Asset {asset_id} ready for import from {zip_filename}")
            return asset_info

        except Exception as e:
            self._handle_error(f"prepare asset {asset_id} for import", e)
            return None

    def validate_zip_library(self) -> Dict[str, Any]:
        """Validate the zip library integrity"""
        validation_results = {
            "assets_path_exists": self.assets_path.exists(),
            "zip_index_loaded": False,
            "total_zip_entries": 0,
            "existing_zip_files": 0,
            "missing_zip_files": [],
            "validation_errors": [],
        }

        try:
            # Load zip index
            zip_index = self.load_zip_index()
            validation_results["zip_index_loaded"] = True
            validation_results["total_zip_entries"] = len(zip_index)

            # Check if zip files exist
            existing_count = 0
            missing_files = []

            for asset_id, zip_filename in zip_index.items():
                zip_path = self.assets_path / zip_filename
                if zip_path.exists():
                    existing_count += 1
                else:
                    missing_files.append(zip_filename)

            validation_results["existing_zip_files"] = existing_count
            validation_results["missing_zip_files"] = missing_files[:10]  # Limit to first 10

            self.logger.info(
                f"Zip library validation: {existing_count}/{len(zip_index)} files found"
            )

        except Exception as e:
            validation_results["validation_errors"].append(str(e))
            self._handle_error("validate zip library", e)

        return validation_results

    def refresh_cache(self) -> None:
        """Clear cached data to force reload"""
        self.logger.info("Refreshing import repository cache")
        self._zip_index = None
