"""
Import Cache Service

Manages the TunnelUI import cache system for processed assets.
Handles cache validation, cleanup, and statistics.
"""

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .import_models import (
    CacheEntry,
    CacheStatistics,
    ValidationResult,
    ImportCacheConfig,
    AssetInfo,
    CacheError,
)


class ImportCacheService:
    """Manages the TunnelUI import cache system"""

    def __init__(self, cache_config: ImportCacheConfig):
        """
        Initialize cache service with configuration

        Args:
            cache_config: Cache configuration settings
        """
        self.cache_config = cache_config
        self.cache_index: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(__name__)

        # Ensure cache root is Path object
        if isinstance(cache_config.cache_root, str):
            self.cache_root = Path(cache_config.cache_root)
        else:
            self.cache_root = cache_config.cache_root

        self.cache_index_path = self.cache_root / cache_config.cache_index_file

        # Initialize cache directory and load index
        self._initialize_cache()
        self._load_cache_index()

    def _initialize_cache(self) -> None:
        """Initialize cache directory structure"""
        try:
            self.cache_root.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Cache directory initialized: {self.cache_root}")
        except Exception as e:
            raise CacheError(f"Failed to initialize cache directory: {e}")

    def _load_cache_index(self) -> None:
        """Load cache index from disk"""
        try:
            if self.cache_index_path.exists():
                with open(self.cache_index_path, "r", encoding="utf-8") as f:
                    index_data = json.load(f)

                # Convert dict data back to CacheEntry objects
                for asset_id, entry_data in index_data.items():
                    try:
                        # Convert string paths back to Path objects
                        entry_data["cache_directory"] = Path(entry_data["cache_directory"])
                        entry_data["processed_files"] = {
                            k: Path(v) for k, v in entry_data.get("processed_files", {}).items()
                        }
                        entry_data["geometry_files"] = [
                            Path(p) for p in entry_data.get("geometry_files", [])
                        ]
                        if entry_data.get("metadata_file"):
                            entry_data["metadata_file"] = Path(entry_data["metadata_file"])

                        # Convert timestamps
                        entry_data["creation_time"] = datetime.fromisoformat(
                            entry_data["creation_time"]
                        )
                        entry_data["last_accessed"] = datetime.fromisoformat(
                            entry_data["last_accessed"]
                        )

                        self.cache_index[asset_id] = CacheEntry(**entry_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to load cache entry for {asset_id}: {e}")

                self.logger.info(f"Loaded {len(self.cache_index)} cache entries")
            else:
                self.logger.info("No existing cache index found, starting fresh")

        except Exception as e:
            self.logger.error(f"Failed to load cache index: {e}")
            self.cache_index = {}

    def _save_cache_index(self) -> None:
        """Save cache index to disk"""
        try:
            # Convert CacheEntry objects to serializable format
            index_data = {}
            for asset_id, entry in self.cache_index.items():
                entry_data = {
                    "asset_id": entry.asset_id,
                    "asset_name": entry.asset_name,
                    "cache_directory": str(entry.cache_directory),
                    "processed_files": {k: str(v) for k, v in entry.processed_files.items()},
                    "geometry_files": [str(p) for p in entry.geometry_files],
                    "metadata_file": str(entry.metadata_file) if entry.metadata_file else None,
                    "creation_time": entry.creation_time.isoformat(),
                    "last_accessed": entry.last_accessed.isoformat(),
                    "file_size_mb": entry.file_size_mb,
                    "asset_type": entry.asset_type,
                }
                index_data[asset_id] = entry_data

            # Write to temporary file first, then rename for atomic operation
            temp_path = self.cache_index_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
            temp_path.replace(self.cache_index_path)

        except Exception as e:
            raise CacheError(f"Failed to save cache index: {e}")

    def is_asset_cached(self, asset_id: str) -> bool:
        """
        Check if asset is already processed and cached

        Args:
            asset_id: Asset identifier

        Returns:
            True if asset is cached and valid
        """
        if asset_id not in self.cache_index:
            return False

        entry = self.cache_index[asset_id]

        # Check if cache directory exists
        if not entry.cache_directory.exists():
            self.logger.warning(f"Cache directory missing for {asset_id}, removing from index")
            del self.cache_index[asset_id]
            return False

        # Check if all files exist
        all_files_exist = all(file_path.exists() for file_path in entry.processed_files.values())

        if not all_files_exist:
            self.logger.warning(f"Some cache files missing for {asset_id}")
            return False

        # Update access time
        entry.update_access_time()
        return True

    def get_cached_asset_path(self, asset_id: str) -> Optional[Path]:
        """
        Get path to cached asset files

        Args:
            asset_id: Asset identifier

        Returns:
            Path to cached asset directory or None if not cached
        """
        if not self.is_asset_cached(asset_id):
            return None

        return self.cache_index[asset_id].cache_directory

    def get_cached_asset_entry(self, asset_id: str) -> Optional[CacheEntry]:
        """
        Get complete cache entry for asset

        Args:
            asset_id: Asset identifier

        Returns:
            CacheEntry object or None if not cached
        """
        if not self.is_asset_cached(asset_id):
            return None

        return self.cache_index[asset_id]

    def cache_processed_asset(
        self,
        asset_id: str,
        source_info: AssetInfo,
        processed_files: Dict[str, Path],
        geometry_files: List[Path],
        metadata_file: Optional[Path] = None,
    ) -> CacheEntry:
        """
        Add newly processed asset to cache

        Args:
            asset_id: Asset identifier
            source_info: Original asset information
            processed_files: Dictionary of texture_type -> processed_file_path
            geometry_files: List of geometry file paths
            metadata_file: Optional metadata file path

        Returns:
            Created CacheEntry
        """
        try:
            # Create cache directory
            cache_dir = self.cache_root / f"{source_info.asset_name}_{asset_id}"
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Calculate total file size
            total_size = 0
            for file_path in processed_files.values():
                if file_path.exists():
                    total_size += file_path.stat().st_size
            for file_path in geometry_files:
                if file_path.exists():
                    total_size += file_path.stat().st_size
            if metadata_file and metadata_file.exists():
                total_size += metadata_file.stat().st_size

            # Create cache entry
            cache_entry = CacheEntry(
                asset_id=asset_id,
                asset_name=source_info.asset_name,
                cache_directory=cache_dir,
                processed_files=processed_files.copy(),
                geometry_files=geometry_files.copy(),
                metadata_file=metadata_file,
                file_size_mb=total_size / (1024 * 1024),
                asset_type=source_info.asset_type,
            )

            # Add to index
            self.cache_index[asset_id] = cache_entry

            # Save index
            self._save_cache_index()

            self.logger.info(f"Cached asset {asset_id} in {cache_dir}")
            return cache_entry

        except Exception as e:
            raise CacheError(f"Failed to cache asset {asset_id}: {e}")

    def clear_cache(self, asset_ids: Optional[List[str]] = None) -> bool:
        """
        Clear cache (all assets or specific assets)

        Args:
            asset_ids: Optional list of specific asset IDs to clear.
                      If None, clears entire cache.

        Returns:
            True if successful
        """
        try:
            if asset_ids is None:
                # Clear entire cache
                if self.cache_root.exists():
                    shutil.rmtree(self.cache_root)
                self.cache_index.clear()
                self._initialize_cache()
                self.logger.info("Cleared entire import cache")
            else:
                # Clear specific assets
                for asset_id in asset_ids:
                    if asset_id in self.cache_index:
                        entry = self.cache_index[asset_id]
                        if entry.cache_directory.exists():
                            shutil.rmtree(entry.cache_directory)
                        del self.cache_index[asset_id]
                        self.logger.info(f"Cleared cache for asset {asset_id}")

                self._save_cache_index()

            return True

        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False

    def get_cache_statistics(self) -> CacheStatistics:
        """
        Get cache size, entry count, etc.

        Returns:
            CacheStatistics object
        """
        try:
            total_size = sum(entry.file_size_mb for entry in self.cache_index.values())
            entry_count = len(self.cache_index)

            oldest_entry = None
            newest_entry = None

            if self.cache_index:
                creation_times = [entry.creation_time for entry in self.cache_index.values()]
                oldest_entry = min(creation_times)
                newest_entry = max(creation_times)

            return CacheStatistics(
                cache_location=self.cache_root,
                entry_count=entry_count,
                total_size_mb=total_size,
                oldest_entry=oldest_entry,
                newest_entry=newest_entry,
                hit_rate=0.0,  # TODO: Implement hit rate tracking
            )

        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return CacheStatistics(cache_location=self.cache_root)

    def validate_cache_integrity(self) -> ValidationResult:
        """
        Validate cache entries and repair if needed

        Returns:
            ValidationResult with details of validation
        """
        result = ValidationResult(valid=True, total_entries=len(self.cache_index))

        corrupted_entries = []
        missing_files = []
        repaired_entries = []

        try:
            for asset_id, entry in list(self.cache_index.items()):
                entry_valid = True

                # Check if cache directory exists
                if not entry.cache_directory.exists():
                    corrupted_entries.append(f"{asset_id}: Missing cache directory")
                    entry_valid = False

                # Check if all processed files exist
                for texture_type, file_path in entry.processed_files.items():
                    if not file_path.exists():
                        missing_files.append(f"{asset_id}: Missing {texture_type} file")
                        entry_valid = False

                # Check geometry files
                for file_path in entry.geometry_files:
                    if not file_path.exists():
                        missing_files.append(f"{asset_id}: Missing geometry file")
                        entry_valid = False

                if not entry_valid:
                    # Remove invalid entry
                    del self.cache_index[asset_id]
                    repaired_entries.append(asset_id)
                else:
                    result.valid_entries += 1

            result.corrupted_entries = corrupted_entries
            result.missing_files = missing_files
            result.repaired_entries = repaired_entries
            result.valid = len(corrupted_entries) == 0 and len(missing_files) == 0

            # Save cleaned index
            if repaired_entries:
                self._save_cache_index()
                self.logger.info(f"Repaired cache: removed {len(repaired_entries)} invalid entries")

        except Exception as e:
            result.valid = False
            result.errors.append(str(e))
            self.logger.error(f"Cache validation failed: {e}")

        return result

    def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        """
        Clean up cache entries older than specified days

        Args:
            max_age_days: Maximum age in days for cache entries

        Returns:
            Number of entries removed
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0

        try:
            to_remove = []
            for asset_id, entry in self.cache_index.items():
                if entry.last_accessed < cutoff_date:
                    to_remove.append(asset_id)

            if to_remove:
                self.clear_cache(to_remove)
                removed_count = len(to_remove)
                self.logger.info(f"Cleaned up {removed_count} old cache entries")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old entries: {e}")

        return removed_count

    def cleanup_by_size(self, target_size_gb: float) -> int:
        """
        Clean up cache entries to reach target size using LRU strategy

        Args:
            target_size_gb: Target cache size in GB

        Returns:
            Number of entries removed
        """
        current_stats = self.get_cache_statistics()

        if current_stats.size_gb <= target_size_gb:
            return 0

        # Sort entries by last accessed time (LRU)
        sorted_entries = sorted(self.cache_index.items(), key=lambda x: x[1].last_accessed)

        removed_count = 0
        current_size_gb = current_stats.size_gb

        try:
            for asset_id, entry in sorted_entries:
                if current_size_gb <= target_size_gb:
                    break

                self.clear_cache([asset_id])
                current_size_gb -= entry.file_size_mb / 1024
                removed_count += 1

            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} cache entries to reach target size")

        except Exception as e:
            self.logger.error(f"Failed to cleanup by size: {e}")

        return removed_count
