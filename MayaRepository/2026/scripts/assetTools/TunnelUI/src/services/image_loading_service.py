"""
Image loading service for TunnelUI Asset Browser.

This service handles asynchronous image loading using Qt threads.
"""

import logging
from pathlib import Path
from typing import Set, Optional, Dict

from PySide6.QtCore import QObject, QThreadPool, QRunnable, QEvent, Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication


class ImageLoadedEvent(QEvent):
    """Custom event for signaling when an image has been loaded"""

    def __init__(self, asset_id: str, pixmap: QPixmap):
        super().__init__(QEvent.Type.User)
        self.asset_id = asset_id
        self.pixmap = pixmap


class ImageLoader(QRunnable):
    """Runnable for loading images in background threads"""

    def __init__(self, asset_id: str, image_path: Path, callback: QObject):
        super().__init__()
        self.asset_id = asset_id
        self.image_path = image_path
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Load image and signal completion"""
        try:
            # Load the image
            pixmap = QPixmap(str(self.image_path))

            if not pixmap.isNull():
                # Scale to thumbnail size while maintaining aspect ratio
                pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logger.debug(f"Successfully loaded image for asset {self.asset_id}")
            else:
                # Create placeholder for failed loads
                pixmap = self._create_placeholder()
                self.logger.warning(
                    f"Failed to load image for asset {self.asset_id}, using placeholder"
                )

            # Post event to main thread
            QApplication.postEvent(self.callback, ImageLoadedEvent(self.asset_id, pixmap))

        except Exception as e:
            self.logger.error(f"Error loading image for asset {self.asset_id}: {e}")
            # Post placeholder on error
            placeholder = self._create_placeholder()
            QApplication.postEvent(self.callback, ImageLoadedEvent(self.asset_id, placeholder))

    def _create_placeholder(self) -> QPixmap:
        """Create placeholder pixmap for failed loads"""
        pixmap = QPixmap(150, 150)
        pixmap.fill(Qt.gray)
        return pixmap


class ImageLoadingService(QObject):
    """Service for managing asynchronous image loading"""

    # Signal emitted when an image is loaded (for direct callback style)
    image_loaded = Signal(str, QPixmap)  # asset_id, pixmap

    def __init__(self, max_threads: int = 10):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(max_threads)
        self._loading_cache: Set[str] = set()
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"Image loading service initialized with {max_threads} threads")

    def load_image(self, asset_id: str, image_path: Path, callback: Optional[QObject] = None):
        """
        Queue image for loading

        Args:
            asset_id: Unique identifier for the asset
            image_path: Path to the image file
            callback: Optional callback object to receive ImageLoadedEvent
        """
        if asset_id in self._loading_cache:
            self.logger.debug(f"Image already loading for asset {asset_id}")
            return  # Already loading

        if not image_path or not image_path.exists():
            self.logger.warning(f"Image path does not exist: {image_path}")
            # Create placeholder immediately
            placeholder = self._create_placeholder()
            if callback:
                QApplication.postEvent(callback, ImageLoadedEvent(asset_id, placeholder))
            else:
                self.image_loaded.emit(asset_id, placeholder)
            return

        # Mark as loading
        self._loading_cache.add(asset_id)

        # Use provided callback or self for event handling
        event_target = callback if callback else self

        # Create and start loader
        loader = ImageLoader(asset_id, image_path, event_target)
        self.thread_pool.start(loader)

        self.logger.debug(f"Queued image loading for asset {asset_id}")

    def load_asset_image(
        self,
        asset_id: str,
        category: str,
        metadata_repo,
        thumbnail: bool = True,
        callback: Optional[QObject] = None,
    ):
        """
        Convenience method to load an asset image using the metadata repository

        Args:
            asset_id: Asset identifier
            category: Asset category
            metadata_repo: Metadata repository to get image path
            thumbnail: Whether to load thumbnail or full image
            callback: Optional callback object
        """
        try:
            image_path = metadata_repo.get_asset_image_path(asset_id, category, thumbnail)
            if image_path:
                self.load_image(asset_id, image_path, callback)
            else:
                self.logger.warning(f"No image found for asset {asset_id} in category {category}")
                # Emit placeholder
                placeholder = self._create_placeholder()
                if callback:
                    QApplication.postEvent(callback, ImageLoadedEvent(asset_id, placeholder))
                else:
                    self.image_loaded.emit(asset_id, placeholder)
        except Exception as e:
            self.logger.error(f"Failed to load asset image {asset_id}: {e}")

    def customEvent(self, event):
        """Handle custom image loaded events when using self as callback"""
        if isinstance(event, ImageLoadedEvent):
            # Remove from loading cache
            self._loading_cache.discard(event.asset_id)
            # Emit signal for any connected slots
            self.image_loaded.emit(event.asset_id, event.pixmap)

    def clear_cache(self) -> None:
        """Clear loading cache"""
        self.logger.info("Clearing image loading cache")
        self._loading_cache.clear()

    def get_loading_status(self) -> Dict[str, int]:
        """Get current loading status"""
        return {
            "currently_loading": len(self._loading_cache),
            "thread_pool_active": self.thread_pool.activeThreadCount(),
            "thread_pool_max": self.thread_pool.maxThreadCount(),
        }

    def set_max_threads(self, max_threads: int) -> None:
        """Update maximum number of loading threads"""
        self.thread_pool.setMaxThreadCount(max_threads)
        self.logger.info(f"Updated max threads to {max_threads}")

    def _create_placeholder(self) -> QPixmap:
        """Create placeholder pixmap for failed loads"""
        pixmap = QPixmap(150, 150)
        pixmap.fill(Qt.gray)
        return pixmap

    def shutdown(self) -> None:
        """Clean shutdown of the image loading service"""
        self.logger.info("Shutting down image loading service")
        self.thread_pool.waitForDone(5000)  # Wait up to 5 seconds
        self.clear_cache()
