import sys
import json
import os
import mayaFilePaths
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QLineEdit, QTabWidget, QListView, QAction, QMessageBox,
    QStyledItemDelegate, QStyle, QCompleter, QDialog, QLabel, QTabBar, QSizePolicy  # Added QCompleter
)
from PySide2.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QSize,
    QThreadPool, QRunnable, QEvent, QRect, QStringListModel  # Added QStringListModel
)
from PySide2.QtGui import QPixmap, QIcon, QPainter, QFontMetrics

metadataFolderPath = r"A:\megaScansMetadata"
megaScansZipsPath = r"M:\Zips"

class StretchedTabBar(QTabBar):
    def __init__(self):
        super().__init__()
        self.setExpanding(True)

    def tabSizeHint(self, index):
        # Get the default size hint and adjust the width so each tab takes equal space
        size = super().tabSizeHint(index)
        if self.parent():
            total_width = self.parent().width()  # Total width of the parent widget
            tab_count = self.count()  # Number of tabs
            if tab_count > 0:
                size.setWidth(total_width // tab_count)  # Divide the width by the number of tabs
        return size

class ImageLoadedEvent(QEvent):
    def __init__(self, asset_id, pixmap):
        super().__init__(QEvent.User)
        self.asset_id = asset_id
        self.pixmap = pixmap

class ImageLoader(QRunnable):
    def __init__(self, asset_id, image_path, callback):
        super().__init__()
        self.asset_id = asset_id
        self.image_path = image_path
        self.callback = callback

    def run(self):
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(150, 150)
            pixmap.fill(Qt.gray)
        # Post the event to the main thread
        QApplication.postEvent(
            self.callback,
            ImageLoadedEvent(self.asset_id, pixmap)
        )

class AssetListModel(QAbstractListModel):
    def __init__(self, assets, image_directory, inverted_index, parent=None):
        super().__init__(parent)
        self.assets = assets  # List of asset IDs
        self.image_directory = image_directory  # Directory for images in this tab
        self.inverted_index = inverted_index  # Reference to the inverted index to get asset names
        self.asset_pixmaps = {}  # Cache for loaded pixmaps
        self.thread_pool = QThreadPool()
        self.parent_widget = parent  # Reference to the main window

    def rowCount(self, parent=QModelIndex()):
        return len(self.assets)

    def data(self, index, role):
        if not index.isValid():
            return None

        asset_id = self.assets[index.row()]

        if role == Qt.DisplayRole:
            # Get asset name from the inverted index (fall back to asset_id if not found)
            asset_info = self.inverted_index.get(asset_id, {})
            asset_name = next(iter(asset_info.values()), asset_id)  # Get asset name or fallback to asset_id
            return asset_name
        elif role == Qt.DecorationRole:
            pixmap = self.asset_pixmaps.get(asset_id)
            if pixmap:
                return QIcon(pixmap)
            else:
                # Start loading the image
                self.load_image(asset_id)
                return QIcon(QPixmap(150, 150))  # Placeholder
        elif role == Qt.SizeHintRole:
            return QSize(150, 170)  # Adjust height to include text
        return None

    def load_image(self, asset_id):
        if asset_id in self.asset_pixmaps:
            return  # Already loading or loaded

        # Build image path using the directory and asset ID
        image_filename = f"{asset_id}_Preview_thumbnail.png"  # Assuming this naming convention
        image_path = os.path.join(self.image_directory, image_filename)

        # Start image loading in a separate thread
        loader = ImageLoader(asset_id, image_path, self)
        self.thread_pool.start(loader)

    def customEvent(self, event):
        if isinstance(event, ImageLoadedEvent):
            self.asset_pixmaps[event.asset_id] = event.pixmap
            index = self.assets.index(event.asset_id)
            model_index = self.index(index)
            self.dataChanged.emit(model_index, model_index, [Qt.DecorationRole])

class AssetItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        asset_name = index.data(Qt.DisplayRole)  # This gets the asset name
        icon = index.data(Qt.DecorationRole)  # This gets the image thumbnail (icon)
        rect = option.rect

        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        # Draw the image (thumbnail)
        if icon:
            icon_rect = QRect(rect.left(), rect.top(), rect.width(), rect.height() - 20)
            icon.paint(painter, icon_rect, Qt.AlignCenter)

        # Draw the asset name
        text_rect = QRect(rect.left(), rect.bottom() - 20, rect.width(), 20)
        painter.drawText(
            text_rect,
            Qt.AlignCenter,
            asset_name
        )

    def sizeHint(self, option, index):
        return QSize(150, 170)  # Adjust size to include the thumbnail and asset name

class ImageDialog(QDialog):
    def __init__(self, assets, current_index, parent=None, zip_index=None):
        super().__init__(parent)
        self.assets = assets  # List of asset IDs
        self.current_index = current_index  # Start with the current index
        self.parent = parent
        self.zip_index = zip_index  # Store the zip index

        self.setFixedSize(800, 800)
        # Initialize UI elements
        self.image_label = QLabel()
        self.asset_info_label = QLabel()
        self.import_button = QPushButton("Import Asset")
        self.import_button.clicked.connect(self.import_asset)

        # Buttons for navigation
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")

        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)

        # Layout setup
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)

        main_layout = QVBoxLayout(self)
        main_layout.addStretch(1)
        main_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        main_layout.addStretch(1)
        main_layout.addWidget(self.asset_info_label, alignment=Qt.AlignCenter)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.import_button)

        # Load the initial image
        self.load_image_by_index()

    def load_image_by_index(self):
        """Load the image based on the current index."""
        asset_id = self.assets[self.current_index]
        asset_info = self.parent.inverted_index.get(asset_id, {})
        asset_name = next(iter(asset_info.values()), asset_id)  # Get asset name or fallback to asset_id

        # Get the current tab's directory mapping dynamically
        current_tab_index = self.parent.tabs.currentIndex()  # Get the current tab index
        current_tab_name = self.parent.tabs.tabText(current_tab_index)  # Get the tab name

        # Find the internal tab name
        internal_tab_name = None
        for key, value in self.parent.tab_display_names.items():
            if value == current_tab_name:
                internal_tab_name = key
                break

        if internal_tab_name is None:
            QMessageBox.warning(self, "Error", "Current tab could not be determined.")
            return

        # Update image path based on the current asset and tab
        image_directory = self.parent.tab_directory_mapping[internal_tab_name]
        thumbnail_image_path = os.path.join(image_directory, f"{asset_id}_Preview_thumbnail.png")
        full_image_path = thumbnail_image_path.replace("_thumbnail", "")

        if os.path.exists(full_image_path):
            self.update_image(asset_id, asset_name, full_image_path)
        else:
            QMessageBox.warning(self, "Error", f"Full image for asset {asset_id} not found.")

        # Update the import button to point to the correct asset
        self.import_button.clicked.disconnect()  # Remove previous connections
        self.import_button.clicked.connect(self.import_asset)

    def update_image(self, asset_id, asset_name, full_image_path):
        """Update the dialog with the new image and asset information."""
        full_image = QPixmap(full_image_path)
        if full_image.width() > full_image.height():
            full_image = full_image.scaledToWidth(700, Qt.SmoothTransformation)
        else:
            full_image = full_image.scaledToHeight(700, Qt.SmoothTransformation)

        self.image_label.setPixmap(full_image)

        # Update the asset info label
        self.asset_info_label.setText(f"Asset Name: {asset_name}\nAsset ID: {asset_id}")

        # Adjust the size of the dialog to fit the new image
        #self.resize(full_image.width(), full_image.height() + 100)

    def show_previous_image(self):
        """Show the previous image in the list."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image_by_index()

    def show_next_image(self):
        """Show the next image in the list."""
        if self.current_index < len(self.assets) - 1:
            self.current_index += 1
            self.load_image_by_index()

    def import_asset(self):
        """Simulate importing the asset by finding the zip file."""
        asset_id = self.assets[self.current_index]

        # Use the zip index to find the corresponding zip file name
        zip_file_name = self.zip_index.get(asset_id, None)

        if zip_file_name:
            zip_file_path = os.path.join(megaScansZipsPath, zip_file_name)
            print(f"Importing asset from: {zip_file_path}")
        else:
            print(f"No zip file found for asset ID: {asset_id}")

class Tunnel(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set window properties
        with open("{}/dark.qss".format(mayaFilePaths.styleSheetFilepath), "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowTitle("Tunnel 4K - The Better Bridge")

        self.resize(900, 800)

        # Load the zip index from the JSON file
        with open(f"{metadataFolderPath}/zip_index.json", 'r') as f:
            self.zip_index = json.load(f)  # Store the zip index

        # Internal tab names and corresponding display names
        self.tabs_list = ["3d", "3dplant", "atlas", "decals", "brush", "surface"]
        self.tab_display_names = {
            "3d": "3D Assets",
            "3dplant": "Plants",
            "atlas": "Atlas",
            "decals": "Decals",
            "brush": "Brushes",
            "surface": "Surfaces"
        }

        # Load inverted index from JSON file
        with open(f"{metadataFolderPath}/inverted_index_combined.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Extract 'index' and 'AssetGrouping'
            self.inverted_index = data['index']
            self.asset_groupings = data['AssetGrouping']

        # Create the menu bar with Settings and About
        self.create_menu()

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Search field at the top
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search assets...")
        self.search_field.textChanged.connect(self.on_search_text_changed)
        main_layout.addWidget(self.search_field)

        # Tabs for different categories
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        tab_bar = StretchedTabBar()
        self.tabs.setTabBar(tab_bar)
        # Stretch the tab widget to fill the window
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.currentChanged.connect(self.on_tab_changed)  # Connect tab change signal
        main_layout.addWidget(self.tabs)

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_field.setCompleter(self.completer)
        all_keywords = list(self.inverted_index.keys())
        self.completer_model = QStringListModel()
        self.completer_model.setStringList(all_keywords)
        self.completer.setModel(self.completer_model)

        # Create QLabel for showing asset count (ensure this is created before the first tab change)
        self.asset_count_label = QLabel("Total assets: 0")
        main_layout.addWidget(self.asset_count_label)  # Add this label at the bottom of the layout

        # Set the central widget
        self.setCentralWidget(main_widget)

        # Initialize the tab views after creating the asset_count_label
        self.setup_tabs_and_views()

    def setup_tabs_and_views(self):
        # Tab to directory mapping
        self.tab_directory_mapping = {
            "3d": f"{metadataFolderPath}/3d",
            "3dplant": f"{metadataFolderPath}/3dplant",
            "atlas": f"{metadataFolderPath}/atlas",
            "decals": f"{metadataFolderPath}/decals",
            "brush": f"{metadataFolderPath}/brush",
            "surface": f"{metadataFolderPath}/surface"
        }

        # Ensure that directories use proper OS-specific path separators
        for tab, path in self.tab_directory_mapping.items():
            self.tab_directory_mapping[tab] = os.path.normpath(path)

        # Build assets per tab
        self.assets_per_tab = {tab: set() for tab in self.tabs_list}
        self.build_assets_per_tab()

        # Keep a reference to the models and views for each tab
        self.models = {}
        self.views = {}

        # Create the tabs and list views
        for tab_name in self.tabs_list:
            list_view = QListView()
            list_view.setViewMode(QListView.IconMode)
            list_view.setIconSize(QSize(150, 150))
            list_view.setResizeMode(QListView.Adjust)
            list_view.setSpacing(10)
            list_view.setUniformItemSizes(True)
            list_view.setWordWrap(True)

            # Connect the click signal
            list_view.clicked.connect(self.on_item_clicked)

            # Get assets for this tab
            assets = list(self.assets_per_tab.get(tab_name, []))
            image_directory = self.tab_directory_mapping.get(tab_name, "")

            # Pass inverted_index to the model
            model = AssetListModel(assets, image_directory, self.inverted_index, parent=self)
            list_view.setModel(model)

            delegate = AssetItemDelegate()
            list_view.setItemDelegate(delegate)

            self.models[tab_name] = model
            self.views[tab_name] = list_view

            # Use the display name for the tab
            display_name = self.tab_display_names.get(tab_name, tab_name)
            self.tabs.addTab(list_view, display_name)

    def build_assets_per_tab(self):
        # Populate the assets for each tab using the asset groupings
        for tab_name, asset_ids in self.asset_groupings.items():
            if tab_name in self.assets_per_tab:
                self.assets_per_tab[tab_name].update(asset_ids)
            else:
                self.assets_per_tab[tab_name] = set(asset_ids)

            # Sort the assets alphabetically and store them back in the tab
            self.assets_per_tab[tab_name] = sorted(self.assets_per_tab[tab_name])

    def create_menu(self):
        # Create the menu bar
        menu_bar = self.menuBar()

        # Create the main menu
        menu = menu_bar.addMenu('Menu')

        # Create actions
        settings_action = QAction('Settings', self)
        about_action = QAction('About', self)

        # Connect actions to methods
        settings_action.triggered.connect(self.open_settings)
        about_action.triggered.connect(self.show_about)

        # Add actions to the menu
        menu.addAction(settings_action)
        menu.addAction(about_action)

    def open_settings(self):
        # Implement your settings dialog here
        QMessageBox.information(self, 'Settings', 'Settings dialog not implemented.')

    def show_about(self):
        # Implement your about dialog here
        QMessageBox.information(self, 'About', 'Tunnel Asset Browser - The better bridge!!!! 2024')

    def on_search_text_changed(self, text):
        text = text.lower().strip()
        current_tab_index = self.tabs.currentIndex()
        current_tab_name = self.tabs.tabText(current_tab_index)

        # Find internal tab name using display name
        internal_tab_name = None
        for key, value in self.tab_display_names.items():
            if value == current_tab_name:
                internal_tab_name = key
                break

        if not internal_tab_name:
            return

        model = self.models[internal_tab_name]

        if not text:
            # Reset model to show all assets in the current tab, sorted alphabetically
            assets = sorted(list(self.assets_per_tab.get(internal_tab_name, [])))
        else:
            # Split the search text into individual terms
            search_terms = text.split()

            # Initialize a set to hold matching assets
            matching_assets = set()

            for term in search_terms:
                # Search top-level keys
                for top_level_key, assets_dict in self.inverted_index.items():
                    if term in top_level_key.lower():  # Case-insensitive match
                        # Add all asset IDs associated with this top-level key
                        matching_assets.update(assets_dict.keys())

            # Filter assets that are in the current tab
            assets_in_tab = set(self.assets_per_tab.get(internal_tab_name, []))
            filtered_assets = assets_in_tab.intersection(matching_assets)

            # Sort the filtered assets alphabetically by their name (not the ID)
            assets = sorted(filtered_assets, key=lambda asset_id: next(iter(self.inverted_index.get(asset_id, {}).values()), asset_id).lower())

            print("Filtered Assets: ", assets)

        # Reset the model with the filtered and sorted asset list
        model.beginResetModel()
        model.assets = assets  # Update the filtered asset list with the correct mapping
        model.asset_pixmaps.clear()  # Clear cached pixmaps to reload new assets
        model.endResetModel()

        self.asset_count_label.setText(f"Total assets: {len(assets)}")  # Update the asset count

    def on_tab_changed(self, index):
        # Clear the search field
        search_text = self.search_field.text()
        self.on_search_text_changed(search_text)

    def on_item_clicked(self, index):
        # Get the current tab
        current_tab_index = self.tabs.currentIndex()
        current_tab_name = self.tabs.tabText(current_tab_index)

        # Find internal tab name using display name
        internal_tab_name = None
        for key, value in self.tab_display_names.items():
            if value == current_tab_name:
                internal_tab_name = key
                break

        if not internal_tab_name:
            return

        model = self.models[internal_tab_name]

        # Retrieve the asset ID from the filtered model, not the original list
        filtered_assets = model.assets  # Ensure we are using the model's filtered assets list
        clicked_asset_index = index.row()  # Get the index of the clicked item

        # Open the ImageDialog with the filtered list and the clicked asset index
        dialog = ImageDialog(filtered_assets, clicked_asset_index, self, zip_index=self.zip_index)
        dialog.exec_()  # This will block until the dialog is closed

def launch():
     global win
     win = Tunnel()
     win.raise_()
     win.activateWindow()
     win.show()

launch()
