"""
Asset list widget components for TunnelUI Asset Browser.
Simplified to work like the original implementation.
"""

import logging
import os
from typing import List, Optional
from pathlib import Path

from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QListView
from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    QSize,
    QThreadPool,
    QRunnable,
    QEvent,
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFontMetrics
from PySide6.QtWidgets import QApplication


class ImageLoadedEvent(QEvent):
    """Event for when an image has been loaded"""

    def __init__(self, asset_id, pixmap):
        super().__init__(QEvent.User)
        self.asset_id = asset_id
        self.pixmap = pixmap


class SimpleImageLoader(QRunnable):
    """Simple image loader like the original"""

    def __init__(self, asset_id, image_path, callback):
        super().__init__()
        self.asset_id = asset_id
        self.image_path = image_path
        self.callback = callback

    def run(self):
        pixmap = QPixmap(str(self.image_path))
        if not pixmap.isNull():
            # Scale to thumbnail size like original
            pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # Create gray placeholder
            pixmap = QPixmap(150, 150)
            pixmap.fill(Qt.gray)

        # Post event to main thread
        QApplication.postEvent(self.callback, ImageLoadedEvent(self.asset_id, pixmap))


class AssetListModel(QAbstractListModel):
    """Simplified model that works like the original"""

    def __init__(self, asset_service, image_service, category: str, parent=None):
        super().__init__(parent)
        self.asset_service = asset_service
        self.category = category
        self.parent_widget = parent

        # Data - start empty for lazy loading
        self.assets: List[str] = []
        self.asset_pixmaps = {}  # Simple cache like original
        self.thread_pool = QThreadPool()

        # Track loading and assets loaded state
        self._assets_loaded = False

        # Logger
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Created simplified model for category '{category}'")

    def ensure_assets_loaded(self):
        """Load assets on demand"""
        if not self._assets_loaded:
            self.logger.debug(f"Loading assets for category '{self.category}'")
            try:
                self.assets = self.asset_service.get_assets_in_category(self.category)
                self._assets_loaded = True
                self.beginResetModel()
                self.endResetModel()
                self.logger.debug(
                    f"Loaded {len(self.assets)} assets for category '{self.category}'"
                )
            except Exception as e:
                self.logger.error(f"Failed to load assets for category '{self.category}': {e}")
                self.assets = []

    def rowCount(self, parent=QModelIndex()):
        if not self._assets_loaded:
            self.ensure_assets_loaded()
        return len(self.assets)

    def data(self, index, role):
        """Simple data method like original"""
        if not self._assets_loaded:
            self.ensure_assets_loaded()

        if not index.isValid() or index.row() >= len(self.assets):
            return None

        asset_id = self.assets[index.row()]

        if role == Qt.DisplayRole:
            return self.asset_service.get_asset_name(asset_id)

        elif role == Qt.DecorationRole:
            # Check cache first
            pixmap = self.asset_pixmaps.get(asset_id)
            if pixmap:
                return QIcon(pixmap)

            # Only load if not already loading (simple check)
            if asset_id not in self.asset_pixmaps:
                self.load_image_simple(asset_id)

            # Return placeholder
            return QIcon(QPixmap(150, 150))

        elif role == Qt.SizeHintRole:
            return QSize(150, 170)

        elif role == Qt.UserRole:
            return asset_id

        return None

    def load_image_simple(self, asset_id: str):
        """Simple image loading like original"""
        try:
            # Get thumbnail path directly - like original
            metadata_path = Path("L:/megaScansMetadata")
            image_path = metadata_path / self.category / f"{asset_id}_Preview_thumbnail.png"

            if image_path.exists():
                # Start loading in thread like original
                loader = SimpleImageLoader(asset_id, image_path, self)
                self.thread_pool.start(loader)
            else:
                self.logger.debug(f"Thumbnail not found: {image_path}")

        except Exception as e:
            self.logger.error(f"Failed to load image for {asset_id}: {e}")

    def customEvent(self, event):
        """Handle image loaded events like original"""
        if isinstance(event, ImageLoadedEvent):
            # Store loaded pixmap
            self.asset_pixmaps[event.asset_id] = event.pixmap

            # Update view
            try:
                asset_index = self.assets.index(event.asset_id)
                model_index = self.index(asset_index)
                self.dataChanged.emit(model_index, model_index, [Qt.DecorationRole])
            except ValueError:
                # Asset not in current list
                pass

    def refresh_assets(self, search_query: Optional[str] = None):
        """Refresh assets with optional search"""
        try:
            if search_query:
                self.assets = self.asset_service.search_assets(search_query, self.category)
            else:
                self.assets = self.asset_service.get_assets_in_category(self.category)

            # Clear cache and reset model
            self.asset_pixmaps.clear()
            self.beginResetModel()
            self.endResetModel()

        except Exception as e:
            self.logger.error(f"Failed to refresh assets: {e}")

    def get_asset_at_index(self, index: int) -> Optional[str]:
        """Get asset ID at index"""
        if 0 <= index < len(self.assets):
            return self.assets[index]
        return None

    def clear_cache(self):
        """Clear image cache"""
        self.asset_pixmaps.clear()


class AssetItemDelegate(QStyledItemDelegate):
    """Simple delegate like original"""

    def paint(self, painter, option, index):
        """Paint asset items like original"""
        asset_name = index.data(Qt.DisplayRole)
        icon = index.data(Qt.DecorationRole)
        rect = option.rect

        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        # Draw icon/image
        if icon:
            icon_rect = rect.adjusted(0, 0, 0, -20)
            icon.paint(painter, icon_rect, Qt.AlignCenter)

        # Draw text
        text_rect = rect.adjusted(0, rect.height() - 20, 0, 0)
        painter.drawText(text_rect, Qt.AlignCenter, asset_name)

    def sizeHint(self, option, index):
        """Size hint like original"""
        return QSize(150, 170)


class AssetListView(QListView):
    """Simple list view like original"""

    def __init__(self, asset_service, image_service, category: str, parent=None):
        super().__init__(parent)

        # Configure view
        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(150, 150))
        self.setResizeMode(QListView.Adjust)
        self.setSpacing(10)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)

        # Create simplified model and delegate
        self.model = AssetListModel(asset_service, image_service, category, parent=self)
        self.setModel(self.model)

        self.delegate = AssetItemDelegate()
        self.setItemDelegate(self.delegate)

        self.category = category

    def refresh_assets(self, search_query: Optional[str] = None):
        """Refresh displayed assets"""
        self.model.refresh_assets(search_query)

    def get_selected_asset(self) -> Optional[str]:
        """Get selected asset ID"""
        indexes = self.selectedIndexes()
        if indexes:
            return indexes[0].data(Qt.UserRole)
        return None

    def get_asset_at_index(self, index: QModelIndex) -> Optional[str]:
        """Get asset at model index"""
        if index.isValid():
            return index.data(Qt.UserRole)
        return None

    def get_all_assets(self) -> List[str]:
        """Get all displayed assets"""
        return self.model.assets.copy()

    def clear_cache(self):
        """Clear image cache"""
        self.model.clear_cache()
