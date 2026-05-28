"""
Main window for TunnelUI Asset Browser.

This module contains the main application window that coordinates all UI components
and integrates with the service layer.
"""

import logging
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTabWidget,
    QLabel,
    QCompleter,
    QMessageBox,
    QMenuBar,
    QMenu,
)
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import QAction

from genTools.uiUtils import load_qss
from ui.widgets.custom_widgets import StretchedTabBar
from ui.widgets.asset_list_widget import AssetListView
from ui.widgets.image_preview_dialog import ImagePreviewDialog
from ui.settings_dialog import SettingsDialog


class TunnelMainWindow(QMainWindow):
    """Main application window for TunnelUI Asset Browser"""

    def __init__(self, asset_service, image_service, config_manager, environment, parent=None):
        super().__init__(parent)

        # Store service references
        self.asset_service = asset_service
        self.image_service = image_service
        self.config_manager = config_manager
        self.environment = environment  # Added for multi-DCC support
        self.config = config_manager.get_config()

        # UI components
        self.category_views: Dict[str, AssetListView] = {}
        self.search_field: Optional[QLineEdit] = None
        self.tabs: Optional[QTabWidget] = None
        self.asset_count_label: Optional[QLabel] = None
        self.completer: Optional[QCompleter] = None

        # Track lazy loading state
        self._search_keywords_loaded = False
        self._loaded_categories = set()

        # Logger
        self.logger = logging.getLogger(__name__)

        # Setup window
        self._setup_window()
        self._create_menu_bar()
        self._setup_ui()
        self._setup_search_completion()

        # Set window title with application name
        app_name = self.environment.get_application_display_name()
        self.setWindowTitle(f"TunnelUI Asset Browser - {app_name}")

        self.logger.info("TunnelMainWindow initialized successfully")

    def _setup_window(self):
        """Configure main window properties"""
        self.setWindowTitle("TunnelUI Asset Browser - The Better Bridge")
        self.setObjectName("TunnelUI_MainWindow")

        # Set window size from configuration
        self.resize(self.config.window_width, self.config.window_height)

        # Apply stylesheet if available
        try:
            from genTools.uiUtils import load_qss

            self.setStyleSheet(load_qss("dark.qss"))
            self.logger.info("Applied stylesheet: dark.qss")
        except Exception as e:
            self.logger.warning(f"Failed to load stylesheet: {e}")

    def _create_menu_bar(self):
        """Create application menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("File")

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        refresh_action = QAction("Refresh Library", self)
        refresh_action.triggered.connect(self._refresh_library)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        # Only add Exit for standalone mode
        if not self.environment.is_maya:
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

        # Help menu
        help_menu = self.menuBar().addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        library_info_action = QAction("Library Information", self)
        library_info_action.triggered.connect(self._show_library_info)
        help_menu.addAction(library_info_action)

    def _setup_ui(self):
        """Setup the main UI components"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search assets...")
        self.search_field.textChanged.connect(self._on_search_text_changed)
        main_layout.addWidget(self.search_field)

        # Tab widget for categories
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        # Use custom stretched tab bar
        tab_bar = StretchedTabBar()
        self.tabs.setTabBar(tab_bar)

        # Connect tab change signal
        self.tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs)

        # Asset count label
        self.asset_count_label = QLabel("Total assets: 0")
        main_layout.addWidget(self.asset_count_label)

        # Setup category tabs
        self._setup_category_tabs()

    def _setup_category_tabs(self):
        """Create tabs for each asset category"""
        try:
            categories = self.asset_service.get_categories()
            self.logger.info(f"Setting up tabs for categories: {categories}")

            for category in categories:
                # Get display name for category
                display_name = self.asset_service.get_category_display_name(category)

                # Create asset list view for this category
                list_view = AssetListView(
                    self.asset_service, self.image_service, category, parent=self
                )

                # Connect item clicked signal
                list_view.clicked.connect(self._on_item_clicked)

                # Store reference
                self.category_views[category] = list_view

                # Add tab
                self.tabs.addTab(list_view, display_name)

                self.logger.debug(
                    f"Created tab for category '{category}' - assets will load on demand"
                )

            # Load assets for the first tab immediately so it's not empty
            if categories:
                first_category = categories[0]
                first_view = self.category_views[first_category]
                first_view.model.ensure_assets_loaded()
                self._update_asset_count()
                self.logger.debug(
                    f"Loaded first tab '{first_category}' with {first_view.model.rowCount()} assets"
                )

        except Exception as e:
            self.logger.error(f"Failed to setup category tabs: {e}")
            QMessageBox.critical(self, "Setup Error", f"Failed to setup category tabs:\n{e}")

    def _setup_search_completion(self):
        """Setup search auto-completion framework (keywords loaded on first use)"""
        try:
            # Create completer framework but DON'T load keywords yet
            self.completer = QCompleter()
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)

            # Attach to search field
            self.search_field.setCompleter(self.completer)

            # Flag to track if keywords are loaded
            self._search_keywords_loaded = False

            self.logger.debug("Setup search completion framework - keywords will load on first use")

        except Exception as e:
            self.logger.warning(f"Failed to setup search completion: {e}")

    def _ensure_search_keywords_loaded(self):
        """Lazy load search keywords when actually needed"""
        if not self._search_keywords_loaded:
            try:
                self.logger.debug("Lazy loading search keywords...")
                keywords = self.asset_service.get_search_keywords()

                # Set model
                completer_model = QStringListModel()
                completer_model.setStringList(keywords)
                self.completer.setModel(completer_model)

                self._search_keywords_loaded = True
                self.logger.debug(f"Loaded {len(keywords)} search keywords on demand")

            except Exception as e:
                self.logger.error(f"Failed to load search keywords: {e}")

    def _get_current_category(self) -> Optional[str]:
        """Get the currently selected category"""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            # Find category by tab index
            categories = list(self.category_views.keys())
            if current_index < len(categories):
                return categories[current_index]
        return None

    def _get_current_list_view(self) -> Optional[AssetListView]:
        """Get the currently active list view"""
        category = self._get_current_category()
        if category:
            return self.category_views.get(category)
        return None

    def _on_search_text_changed(self, text: str):
        """Handle search text changes"""
        try:
            # Lazy load search keywords on first search
            if not self._search_keywords_loaded:
                self._ensure_search_keywords_loaded()

            current_view = self._get_current_list_view()
            if current_view:
                # Update the current tab's view with search results
                current_view.refresh_assets(text.strip() if text.strip() else None)
                self._update_asset_count()

        except Exception as e:
            self.logger.error(f"Search failed: {e}")

    def _on_tab_changed(self, index: int):
        """Handle tab changes - trigger lazy loading of assets"""
        try:
            # Get the current list view
            current_view = self._get_current_list_view()
            if current_view:
                # Trigger lazy loading of assets for this category
                current_view.model.ensure_assets_loaded()

                # Re-apply current search to new tab
                search_text = self.search_field.text() if self.search_field else ""
                if search_text.strip():
                    current_view.refresh_assets(search_text.strip())

                # Update asset count
                self._update_asset_count()

        except Exception as e:
            self.logger.error(f"Tab change failed: {e}")

    def _on_item_clicked(self, index):
        """Handle asset item clicks"""
        try:
            current_view = self._get_current_list_view()
            current_category = self._get_current_category()

            if not current_view or not current_category:
                return

            # Get clicked asset
            asset_id = current_view.get_asset_at_index(index)
            if not asset_id:
                return

            # Get all current assets for navigation
            all_assets = current_view.get_all_assets()
            clicked_index = all_assets.index(asset_id) if asset_id in all_assets else 0

            # Open image preview dialog
            dialog = ImagePreviewDialog(
                asset_service=self.asset_service,
                image_service=self.image_service,
                environment=self.environment,  # Added for multi-DCC support
                category=current_category,
                assets=all_assets,
                initial_index=clicked_index,
                parent=self,
            )
            dialog.exec()

        except Exception as e:
            self.logger.error(f"Failed to handle item click: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open asset preview:\n{e}")

    def _update_asset_count(self):
        """Update the asset count label"""
        try:
            current_view = self._get_current_list_view()
            if current_view and self.asset_count_label:
                count = current_view.model.rowCount()
                self.asset_count_label.setText(f"Total assets: {count}")
        except Exception as e:
            self.logger.error(f"Failed to update asset count: {e}")

    def _open_settings(self):
        """Open settings dialog"""
        try:
            dialog = SettingsDialog(self.config_manager, parent=self)

            if dialog.exec() == QMessageBox.Accepted:
                # Settings were applied, optionally refresh UI
                self.logger.info("Settings updated")

                # Update window title or other UI elements if needed
                updated_config = dialog.get_updated_config()
                if (
                    updated_config.window_width != self.config.window_width
                    or updated_config.window_height != self.config.window_height
                ):
                    self.resize(updated_config.window_width, updated_config.window_height)

                # Update stored config reference
                self.config = updated_config

        except Exception as e:
            self.logger.error(f"Failed to open settings: {e}")
            QMessageBox.critical(self, "Settings Error", f"Failed to open settings:\n{e}")

    def _refresh_library(self):
        """Refresh the asset library data"""
        try:
            self.logger.info("Refreshing asset library...")

            # Clear all caches to force reload
            self.asset_service.clear_all_caches()

            # Refresh category tabs to reload data
            current_tab = self.tabs.currentIndex()
            for i in range(self.tabs.count()):
                list_view = self.tabs.widget(i)
                if hasattr(list_view, "model") and list_view.model():
                    list_view.model().refresh_data()

            self.logger.info("Asset library refreshed successfully")

        except Exception as e:
            self.logger.error(f"Failed to refresh library: {e}")
            # Show error dialog
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh library:\n{e}")

    def _show_about(self):
        """Show about dialog"""
        about_text = (
            "<h3>TunnelUI Asset Browser</h3>"
            "<p><b>Version:</b> 2.0.0 (Refactored)</p>"
            "<p><b>Description:</b> Advanced asset browser for MegaScans library</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>✅ Modular architecture with dependency injection</li>"
            "<li>✅ Configurable paths and settings</li>"
            "<li>✅ High-performance threaded image loading</li>"
            "<li>✅ Advanced search with auto-completion</li>"
            "<li>✅ Maya and standalone mode support</li>"
            "</ul>"
            "<p><b>Environment:</b> "
            + f"{'Maya ' + self.environment.maya_version if self.environment.is_maya else 'Standalone'}"
            + "</p>"
        )

        QMessageBox.about(self, "About TunnelUI", about_text)

    def _show_library_info(self):
        """Show library information dialog"""
        try:
            stats = self.asset_service.get_library_statistics()

            info_text = f"""
<h3>Asset Library Information</h3>
<p><b>Total Assets:</b> {stats.get('total_assets', 0):,}</p>
<p><b>Categories:</b> {stats.get('total_categories', 0)}</p>

<h4>Assets by Category:</h4>
"""

            for category, count in stats.get("category_counts", {}).items():
                display_name = self.asset_service.get_category_display_name(category)
                info_text += f"<p>• <b>{display_name}:</b> {count:,} assets</p>"

            search_stats = stats.get("search_statistics", {})
            info_text += f"""
<h4>Search Statistics:</h4>
<p>• <b>Keywords:</b> {search_stats.get('total_keywords', 0):,}</p>
<p>• <b>Cached Searches:</b> {search_stats.get('cached_searches', 0)}</p>

<h4>Configuration:</h4>
<p>• <b>Metadata Path:</b> {self.config.metadata_path}</p>
<p>• <b>Assets Path:</b> {self.config.assets_path}</p>
"""

            QMessageBox.information(self, "Library Information", info_text)

        except Exception as e:
            self.logger.error(f"Failed to show library info: {e}")
            QMessageBox.warning(
                self, "Library Info Error", f"Failed to get library information:\n{e}"
            )

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.logger.info("Main window closing")

            # Clear image caches
            for view in self.category_views.values():
                view.clear_cache()

            # Accept the close event
            event.accept()

        except Exception as e:
            self.logger.error(f"Error during window close: {e}")
            event.accept()  # Close anyway
