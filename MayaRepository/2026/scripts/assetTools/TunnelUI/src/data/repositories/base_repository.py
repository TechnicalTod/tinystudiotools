"""
Base repository classes for TunnelUI Asset Browser.

This module defines the abstract base classes for all data repositories.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path


class BaseRepository(ABC):
    """Abstract base class for all repositories"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def _handle_error(self, operation: str, error: Exception) -> None:
        """Standard error handling for repository operations"""
        self.logger.error(f"Failed to {operation}: {error}")
        if self.config.debug_mode:
            raise error


class AssetMetadataRepository(BaseRepository):
    """Abstract base class for asset metadata access"""

    @abstractmethod
    def load_inverted_index(self) -> Dict[str, Dict[str, str]]:
        """Load the inverted index for asset search"""
        pass

    @abstractmethod
    def load_asset_groupings(self) -> Dict[str, List[str]]:
        """Load asset groupings by category"""
        pass

    @abstractmethod
    def get_asset_image_path(
        self, asset_id: str, category: str, thumbnail: bool = True
    ) -> Optional[Path]:
        """Get path to asset image file"""
        pass

    @abstractmethod
    def refresh_cache(self) -> None:
        """Clear cached data to force reload"""
        pass


class AssetImportRepository(BaseRepository):
    """Abstract base class for asset import operations"""

    @abstractmethod
    def load_zip_index(self) -> Dict[str, str]:
        """Load zip file index for asset importing"""
        pass

    @abstractmethod
    def get_asset_zip_path(self, asset_id: str, zip_filename: str) -> Optional[Path]:
        """Get full path to asset zip file"""
        pass

    @abstractmethod
    def validate_asset_exists(self, asset_id: str, zip_filename: str) -> bool:
        """Check if asset zip file exists"""
        pass

    @abstractmethod
    def get_asset_info(self, asset_id: str, zip_filename: str) -> Dict[str, Any]:
        """Get asset information for import"""
        pass
