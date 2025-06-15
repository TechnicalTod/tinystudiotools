"""
Browse Widget - Browse published files interface
"""

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError:
    try:
        from PySide2.QtWidgets import *
        from PySide2.QtCore import *
        from PySide2.QtGui import *
    except ImportError:
        raise ImportError("Neither PySide6 nor PySide2 is available")

from datetime import datetime


class PublishTreeItem(QTreeWidgetItem):
    """Custom tree item for publish data"""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.publish_data = data
        self.item_type = "unknown"  # "show", "category", "asset", "task", "version"


class BrowseWidget(QWidget):
    """Widget for browsing published files"""

    # Signals
    refresh_requested = Signal()
    file_selected = Signal(dict)  # Emit selected file data
    show_filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the browse interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Filter controls
        self.filter_section = self.create_filter_section()
        layout.addWidget(self.filter_section)

        # Publish tree
        self.tree_section = self.create_tree_section()
        layout.addWidget(self.tree_section)

        # Details panel
        self.details_section = self.create_details_section()
        layout.addWidget(self.details_section)

    def create_filter_section(self):
        """Create the filter controls section"""
        group = QGroupBox("Filters")
        layout = QHBoxLayout(group)

        # Show filter
        layout.addWidget(QLabel("Show:"))
        self.show_filter = QComboBox()
        self.show_filter.addItem("All Shows")
        self.show_filter.setMinimumWidth(150)
        layout.addWidget(self.show_filter)

        # Asset type filter
        layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Assets", "Shots"])
        layout.addWidget(self.type_filter)

        # Search box
        layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search assets/shots...")
        layout.addWidget(self.search_box)

        layout.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh the publish list")
        layout.addWidget(self.refresh_btn)

        return group

    def create_tree_section(self):
        """Create the publish tree section"""
        group = QGroupBox("Published Files")
        layout = QVBoxLayout(group)

        # Tree widget
        self.publish_tree = QTreeWidget()
        self.publish_tree.setHeaderLabels(["Name", "Version", "Artist", "Date", "Size", "Comments"])
        self.publish_tree.setAlternatingRowColors(True)
        self.publish_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.publish_tree.setSortingEnabled(True)
        self.publish_tree.setRootIsDecorated(True)

        # Set column widths
        header = self.publish_tree.header()
        header.resizeSection(0, 200)  # Name
        header.resizeSection(1, 80)  # Version
        header.resizeSection(2, 100)  # Artist
        header.resizeSection(3, 120)  # Date
        header.resizeSection(4, 80)  # Size
        header.resizeSection(5, 200)  # Comments

        layout.addWidget(self.publish_tree)

        return group

    def create_details_section(self):
        """Create the details panel section"""
        group = QGroupBox("File Details")
        group.setMaximumHeight(120)

        layout = QFormLayout(group)

        # Details labels
        self.path_label = QLabel("No file selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("QLabel { color: #999; }")

        self.stats_label = QLabel("-")
        self.stats_label.setStyleSheet("QLabel { color: #999; }")

        # Action buttons
        self.actions_layout = QHBoxLayout()

        self.open_btn = QPushButton("📂 Open Location")
        self.open_btn.setEnabled(False)
        self.open_btn.setToolTip("Open file location in explorer")

        self.load_btn = QPushButton("📥 Load in Maya")
        self.load_btn.setEnabled(False)
        self.load_btn.setToolTip("Load this file in Maya")

        self.actions_layout.addWidget(self.open_btn)
        self.actions_layout.addWidget(self.load_btn)
        self.actions_layout.addStretch()

        # Add to layout
        layout.addRow("File Path:", self.path_label)
        layout.addRow("Stats:", self.stats_label)
        layout.addRow("Actions:", self.actions_layout)

        return group

    def setup_connections(self):
        """Setup signal connections"""
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.show_filter.currentTextChanged.connect(self.show_filter_changed.emit)
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        self.search_box.textChanged.connect(self.apply_filters)
        self.publish_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.publish_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.open_btn.clicked.connect(self.open_file_location)
        self.load_btn.clicked.connect(self.load_file_in_maya)

    def on_selection_changed(self):
        """Handle tree selection change"""
        selected_items = self.publish_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.update_details_panel(item)

            # Enable/disable buttons based on selection
            is_version = hasattr(item, "item_type") and item.item_type == "version"
            self.open_btn.setEnabled(is_version)
            self.load_btn.setEnabled(is_version)

            # Emit selection signal
            if is_version and hasattr(item, "publish_data"):
                self.file_selected.emit(item.publish_data)
        else:
            self.clear_details_panel()
            self.open_btn.setEnabled(False)
            self.load_btn.setEnabled(False)

    def on_item_double_clicked(self, item, column):
        """Handle double-click on tree item"""
        if hasattr(item, "item_type") and item.item_type == "version":
            self.load_file_in_maya()

    def update_details_panel(self, item):
        """Update the details panel with item information"""
        if not hasattr(item, "publish_data") or not item.publish_data:
            self.clear_details_panel()
            return

        data = item.publish_data

        # Update path
        file_path = data.get("file_path", "Unknown")
        self.path_label.setText(file_path)
        self.path_label.setStyleSheet("QLabel { color: #ccc; }")

        # Update stats
        size = data.get("file_size", 0)
        size_mb = size / (1024 * 1024) if size > 0 else 0

        maya_version = data.get("maya_version", "Unknown")
        stats_text = f"Size: {size_mb:.1f} MB | Maya: {maya_version}"

        self.stats_label.setText(stats_text)
        self.stats_label.setStyleSheet("QLabel { color: #ccc; }")

    def clear_details_panel(self):
        """Clear the details panel"""
        self.path_label.setText("No file selected")
        self.path_label.setStyleSheet("QLabel { color: #999; }")
        self.stats_label.setText("-")
        self.stats_label.setStyleSheet("QLabel { color: #999; }")

    def apply_filters(self):
        """Apply current filters to the tree"""
        show_filter = self.show_filter.currentText()
        type_filter = self.type_filter.currentText()
        search_text = self.search_box.text().lower()

        # Hide/show items based on filters
        root = self.publish_tree.invisibleRootItem()
        for i in range(root.childCount()):
            show_item = root.child(i)
            show_visible = self._should_show_item(show_item, show_filter, type_filter, search_text)
            show_item.setHidden(not show_visible)

    def _should_show_item(self, item, show_filter, type_filter, search_text):
        """Check if item should be visible based on filters"""
        # Show filter
        if show_filter != "All Shows" and item.text(0) != show_filter:
            return False

        # Search text filter (recursive)
        if search_text:
            if not self._item_matches_search(item, search_text):
                return False

        # Type filter
        if type_filter != "All":
            if not self._item_matches_type_filter(item, type_filter):
                return False

        return True

    def _item_matches_search(self, item, search_text):
        """Check if item or any of its children match search text"""
        # Check current item
        item_text = item.text(0).lower()
        if search_text in item_text:
            return True

        # Check children recursively
        for i in range(item.childCount()):
            child = item.child(i)
            if self._item_matches_search(child, search_text):
                return True

        return False

    def _item_matches_type_filter(self, item, type_filter):
        """Check if item matches type filter"""
        # This is a simple implementation - you might want to enhance it
        if hasattr(item, "item_type"):
            if type_filter == "Assets" and "asset" in item.item_type.lower():
                return True
            elif type_filter == "Shots" and "shot" in item.item_type.lower():
                return True

        # Check children
        for i in range(item.childCount()):
            child = item.child(i)
            if self._item_matches_type_filter(child, type_filter):
                return True

        return True  # Default to visible

    def load_publishes(self, publishes_data):
        """Load publish data into the tree"""
        self.publish_tree.clear()

        if not publishes_data:
            return

        # Group publishes by show
        shows = {}
        for publish in publishes_data:
            show_name = publish.get("show_name", "Unknown")
            if show_name not in shows:
                shows[show_name] = {"assets": {}, "shots": {}}

            asset_type = publish.get("asset_type", "asset")
            asset_id = publish.get("asset_id", "unknown")
            task = publish.get("task", "unknown")

            # Group by asset type
            asset_group = shows[show_name][asset_type + "s"]
            if asset_id not in asset_group:
                asset_group[asset_id] = {}

            if task not in asset_group[asset_id]:
                asset_group[asset_id][task] = []

            asset_group[asset_id][task].append(publish)

        # Build tree structure
        for show_name, show_data in shows.items():
            show_item = PublishTreeItem()
            show_item.setText(0, show_name)
            show_item.item_type = "show"
            self.publish_tree.addTopLevelItem(show_item)

            # Add Assets category
            if show_data["assets"]:
                assets_item = PublishTreeItem(show_item)
                assets_item.setText(0, "Assets")
                assets_item.item_type = "category"

                self._add_assets_to_tree(assets_item, show_data["assets"])

            # Add Shots category
            if show_data["shots"]:
                shots_item = PublishTreeItem(show_item)
                shots_item.setText(0, "Shots")
                shots_item.item_type = "category"

                self._add_assets_to_tree(shots_item, show_data["shots"])

        # Expand all top-level items
        self.publish_tree.expandAll()

        # Update show filter
        self.update_show_filter(list(shows.keys()))

    def _add_assets_to_tree(self, parent_item, assets_data):
        """Add assets data to tree"""
        for asset_id, tasks in assets_data.items():
            asset_item = PublishTreeItem(parent_item)
            asset_item.setText(0, asset_id)
            asset_item.item_type = "asset"

            for task, publishes in tasks.items():
                task_item = PublishTreeItem(asset_item)
                task_item.setText(0, task)
                task_item.item_type = "task"

                # Sort publishes by version (descending)
                publishes.sort(key=lambda x: x.get("version", 0), reverse=True)

                for publish in publishes:
                    version_item = PublishTreeItem(task_item)
                    version_item.item_type = "version"
                    version_item.publish_data = publish

                    # Set item data
                    version = publish.get("version", 1)
                    version_item.setText(0, f"v{version:03d}")
                    version_item.setText(1, str(version))
                    version_item.setText(2, publish.get("artist", "Unknown"))

                    # Format date
                    pub_date = publish.get("published_at")
                    if pub_date:
                        if isinstance(pub_date, str):
                            try:
                                pub_date = datetime.fromisoformat(pub_date)
                            except:
                                pub_date = None

                        if pub_date:
                            version_item.setText(3, pub_date.strftime("%Y-%m-%d %H:%M"))

                    # Format file size
                    file_size = publish.get("file_size", 0)
                    if file_size > 0:
                        size_mb = file_size / (1024 * 1024)
                        version_item.setText(4, f"{size_mb:.1f} MB")

                    version_item.setText(5, publish.get("comments", ""))

    def update_show_filter(self, shows):
        """Update the show filter dropdown"""
        current_text = self.show_filter.currentText()
        self.show_filter.clear()
        self.show_filter.addItem("All Shows")
        self.show_filter.addItems(shows)

        # Restore selection if it still exists
        index = self.show_filter.findText(current_text)
        if index >= 0:
            self.show_filter.setCurrentIndex(index)

    def open_file_location(self):
        """Open the selected file's location"""
        selected_items = self.publish_tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        if not hasattr(item, "publish_data") or not item.publish_data:
            return

        file_path = item.publish_data.get("file_path")
        if file_path:
            import os
            import subprocess

            try:
                if os.path.exists(file_path):
                    # Open file location in explorer
                    if os.name == "nt":  # Windows
                        subprocess.run(f'explorer /select,"{file_path}"', shell=True)
                    else:  # Mac/Linux
                        folder_path = os.path.dirname(file_path)
                        subprocess.run(
                            ["open", folder_path]
                            if os.name == "posix"
                            else ["xdg-open", folder_path]
                        )
                else:
                    QMessageBox.warning(
                        self, "File Not Found", f"File does not exist:\n{file_path}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file location:\n{str(e)}")

    def load_file_in_maya(self):
        """Load the selected file in Maya"""
        selected_items = self.publish_tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        if not hasattr(item, "publish_data") or not item.publish_data:
            return

        file_path = item.publish_data.get("file_path")
        if file_path:
            try:
                import maya.cmds as cmds

                # Ask user about saving current scene
                if cmds.file(query=True, modified=True):
                    reply = QMessageBox.question(
                        self,
                        "Unsaved Changes",
                        "Current scene has unsaved changes. Continue loading?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return

                # Load the file
                cmds.file(file_path, open=True, force=True)
                QMessageBox.information(self, "Success", f"Loaded file:\n{file_path}")

            except ImportError:
                QMessageBox.warning(
                    self, "Maya Not Available", "Maya is not available for file loading."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def get_selected_publish(self):
        """Get the currently selected publish data"""
        selected_items = self.publish_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if hasattr(item, "publish_data"):
                return item.publish_data
        return None
