"""
Asset search service for TunnelUI Asset Browser.

This service handles all search and filtering operations for assets.
"""

import logging
from typing import List, Dict, Set, Optional


class AssetSearchService:
    """Business logic for asset searching and filtering"""

    def __init__(self, metadata_repository):
        self.metadata_repo = metadata_repository
        self.logger = logging.getLogger(__name__)
        self._search_cache: Dict[str, List[str]] = {}

    def search_assets(
        self, query: str, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[str]:
        """
        Search assets by query string with optional category filter

        Args:
            query: Search query string
            category: Optional category to filter results
            limit: Optional limit on number of results

        Returns:
            List of asset IDs matching the search criteria
        """
        # Handle empty query
        if not query.strip():
            results = self.get_all_assets_in_category(category) if category else []
            return results[:limit] if limit and limit > 0 else results

        # Create cache key
        cache_key = f"{query.lower()}:{category or 'all'}:{limit or 'no_limit'}"

        # Check cache first
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        try:
            inverted_index = self.metadata_repo.load_inverted_index()
            matching_assets = set()

            # Search through inverted index
            query_lower = query.lower()
            for keyword, assets_dict in inverted_index.items():
                if query_lower in keyword.lower():
                    matching_assets.update(assets_dict.keys())

            # Filter by category if specified
            if category:
                category_assets = set(self.get_all_assets_in_category(category))
                matching_assets = matching_assets.intersection(category_assets)

            # Convert to list and sort
            results = sorted(list(matching_assets))

            # Apply limit if specified
            if limit and limit > 0:
                results = results[:limit]

            # Cache the results
            self._search_cache[cache_key] = results

            self.logger.debug(
                f"Search '{query}' in '{category or 'all'}' returned {len(results)} assets"
            )
            return results

        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            return []

    def get_all_assets_in_category(self, category: str) -> List[str]:
        """Get all assets in a specific category, sorted alphabetically"""
        try:
            asset_groupings = self.metadata_repo.load_asset_groupings()
            assets = asset_groupings.get(category, [])

            # Sort alphabetically by asset name
            inverted_index = self.metadata_repo.load_inverted_index()
            sorted_assets = sorted(
                assets, key=lambda aid: self._get_asset_name(aid, inverted_index)
            )

            self.logger.debug(f"Category '{category}' has {len(sorted_assets)} assets")
            return sorted_assets

        except Exception as e:
            self.logger.error(f"Failed to get assets for category '{category}': {e}")
            return []

    def get_asset_name(self, asset_id: str) -> str:
        """Get display name for an asset"""
        try:
            inverted_index = self.metadata_repo.load_inverted_index()
            return self._get_asset_name(asset_id, inverted_index)
        except Exception as e:
            self.logger.error(f"Failed to get asset name for {asset_id}: {e}")
            return asset_id

    def _get_asset_name(self, asset_id: str, inverted_index: Dict) -> str:
        """Helper to get asset name from inverted index"""
        # Look through inverted index to find asset name
        for assets_dict in inverted_index.values():
            if asset_id in assets_dict:
                return assets_dict[asset_id]
        # Fallback to asset ID if not found
        return asset_id

    def get_search_keywords(self) -> List[str]:
        """Get all available search keywords for auto-completion"""
        try:
            inverted_index = self.metadata_repo.load_inverted_index()
            keywords = list(inverted_index.keys())
            self.logger.debug(f"Retrieved {len(keywords)} search keywords")
            return sorted(keywords)
        except Exception as e:
            self.logger.error(f"Failed to get search keywords: {e}")
            return []

    def get_category_display_name(self, category: str) -> str:
        """Get user-friendly display name for category"""
        display_names = {
            "3d": "3D Assets",
            "3dplant": "Plants",
            "atlas": "Atlas",
            "decals": "Decals",
            "brush": "Brushes",
            "surface": "Surfaces",
        }
        return display_names.get(category, category.title())

    def get_available_categories(self) -> List[str]:
        """Get list of available asset categories"""
        try:
            return self.metadata_repo.get_all_categories()
        except Exception as e:
            self.logger.error(f"Failed to get available categories: {e}")
            return []

    def get_category_asset_count(self, category: str) -> int:
        """Get the number of assets in a category"""
        try:
            return self.metadata_repo.get_category_asset_count(category)
        except Exception as e:
            self.logger.error(f"Failed to get asset count for category '{category}': {e}")
            return 0

    def clear_cache(self) -> None:
        """Clear search cache to force fresh results"""
        self.logger.info("Clearing search cache")
        self._search_cache.clear()

    def get_search_statistics(self) -> Dict[str, int]:
        """Get statistics about search usage"""
        return {
            "cached_searches": len(self._search_cache),
            "total_keywords": len(self.get_search_keywords()),
            "total_categories": len(self.get_available_categories()),
        }
