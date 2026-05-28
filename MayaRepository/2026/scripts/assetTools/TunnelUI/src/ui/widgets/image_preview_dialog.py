"""
Image Preview Dialog

A dialog for displaying asset previews and handling import/open operations
based on the active DCC application.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import webbrowser
import subprocess
import platform

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QSizePolicy,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QSpacerItem,
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QPixmap, QFont, QKeySequence, QShortcut, QPalette

# Add crash logger import
import sys

try:
    sys.path.append(
        str(Path(__file__).parent.parent.parent.parent.parent)
    )  # Go up 5 levels to TunnelUI root
    from crash_logger import crash_logger
except ImportError:
    # Fallback logger if crash_logger import fails
    class FallbackLogger:
        def log(self, message):
            print(f"🔍 {message}")

    crash_logger = FallbackLogger()


class ImagePreviewDialog(QDialog):
    """Dialog for previewing full-size asset images with navigation and import"""

    def __init__(
        self,
        asset_service,
        image_service,
        environment,
        category: str,
        assets: List[str],
        initial_index: int = 0,
        parent=None,
    ):
        super().__init__(parent)

        self.asset_service = asset_service
        self.image_service = image_service
        self.environment = environment  # Added environment for multi-DCC support
        self.category = category
        self.assets = assets
        self.current_index = initial_index

        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("Asset Preview")
        self.setModal(True)
        self.resize(800, 600)

        self._setup_ui()
        self._setup_shortcuts()
        self.load_current_image()

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Image display area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(700, 500)
        self.image_label.setStyleSheet(
            "QLabel { border: 1px solid gray; background-color: #2b2b2b; }"
        )
        layout.addWidget(self.image_label)

        # Asset information
        self.asset_info_label = QLabel()
        self.asset_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.asset_info_label)

        # Navigation and action buttons
        button_layout = QHBoxLayout()

        # Navigation buttons
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.previous_image)
        self.prev_button.setEnabled(len(self.assets) > 1)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setEnabled(len(self.assets) > 1)

        # Import/Open button - uses application-aware text
        import_button_text = self.environment.get_import_button_text()
        self.import_button = QPushButton(import_button_text)
        self.import_button.clicked.connect(self.import_asset)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addStretch()
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Navigation shortcuts
        prev_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        prev_shortcut.activated.connect(self.previous_image)

        next_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        next_shortcut.activated.connect(self.next_image)

        # Close shortcut
        close_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.accept)

    def previous_image(self):
        """Navigate to previous image"""
        if len(self.assets) > 1:
            self.current_index = (self.current_index - 1) % len(self.assets)
            self.load_current_image()

    def next_image(self):
        """Navigate to next image"""
        if len(self.assets) > 1:
            self.current_index = (self.current_index + 1) % len(self.assets)
            self.load_current_image()

    def load_current_image(self):
        """Load and display the current image"""
        if not self.assets:
            self._show_no_image_message("", "No assets available")
            return

        asset_id = self.assets[self.current_index]
        try:
            asset_name = self.asset_service.get_asset_name(asset_id)
            # Build image path directly like original
            metadata_path = Path("L:/megaScansMetadata")
            full_image_path = metadata_path / self.category / f"{asset_id}_Preview.png"

            if full_image_path.exists():
                self._display_image(asset_id, asset_name, full_image_path)
            else:
                self._show_no_image_message(asset_id, asset_name)
        except Exception as e:
            self.logger.error(f"Failed to load image for asset {asset_id}: {e}")

    def _display_image(self, asset_id: str, asset_name: str, image_path):
        try:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                # Simple scaling like original - only scale DOWN if too large
                if pixmap.width() > 700 or pixmap.height() > 700:
                    if pixmap.width() > pixmap.height():
                        pixmap = pixmap.scaledToWidth(700, Qt.SmoothTransformation)
                    else:
                        pixmap = pixmap.scaledToHeight(700, Qt.SmoothTransformation)

                self.image_label.setPixmap(pixmap)
            else:
                self._show_no_image_message(asset_id, asset_name)
                return
            self.asset_info_label.setText(f"Asset: {asset_name}\nID: {asset_id}")
            self.setWindowTitle(f"Asset Preview - {asset_name}")
        except Exception as e:
            self.logger.error(f"Failed to display image for {asset_id}: {e}")
            self._show_no_image_message(asset_id, asset_name)

    def _show_no_image_message(self, asset_id: str, asset_name: str):
        """Show message when no image is available"""
        placeholder = QPixmap(700, 500)
        placeholder.fill(Qt.gray)
        self.image_label.setPixmap(placeholder)

        self.asset_info_label.setText(
            f"Asset: {asset_name}\nID: {asset_id}\nNo preview image available"
        )
        self.setWindowTitle(f"Asset Preview - {asset_name} (No Image)")

    def import_asset(self):
        """Import/Open the current asset based on the active application"""
        asset_id = self.assets[self.current_index]
        active_app = self.environment.get_active_application()

        try:
            # Get zip file path
            zip_path = self.asset_service.get_asset_zip_path(asset_id)

            if not zip_path or not zip_path.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Zip file for asset {asset_id} not found.",
                )
                return

            # Handle different applications
            # Use string comparison to avoid object identity issues from module reloading
            app_name = active_app.value  # Get the string value

            if app_name == "standalone":
                # Standalone mode: Open zip file with system default application
                self._open_zip_file(zip_path, asset_id)

            elif app_name == "maya":
                # Maya mode: Import into Maya scene
                self._import_to_maya(zip_path, asset_id)

            elif app_name == "unreal":
                # Unreal mode: Import to Content Browser (future implementation)
                self._import_to_unreal(zip_path, asset_id)

            else:
                # Default fallback: Open zip file
                self._open_zip_file(zip_path, asset_id)

        except Exception as e:
            self.logger.error(f"Failed to import/open asset {asset_id}: {e}")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to open asset {asset_id}:\n{e}",
            )

    def _open_zip_file(self, zip_path: Path, asset_id: str):
        """Open zip file with system default application (standalone mode)"""
        try:
            if sys.platform == "win32":
                os.startfile(str(zip_path))
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(zip_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(zip_path)])

            self.logger.info(f"Opened zip file for asset {asset_id}: {zip_path}")
            # Removed popup notification - user doesn't want it

        except Exception as e:
            self.logger.error(f"Failed to open zip file {zip_path}: {e}")
            QMessageBox.warning(
                self,
                "Open Error",
                f"Failed to open zip file:\n{e}",
            )

    def _import_to_maya(self, zip_path: Path, asset_id: str):
        """Import asset to Maya using the Maya import service"""
        try:
            crash_logger.log("PREVIEW-1: Maya import method started")
            self.logger.info(f"Maya import started for asset {asset_id}")

            # Get asset name from metadata
            asset_metadata = self.asset_service.get_asset_metadata(asset_id)
            asset_name = asset_metadata.get("name", asset_id) if asset_metadata else asset_id
            crash_logger.log("PREVIEW-2: Asset metadata retrieved")

            # Check if Maya import is available
            capabilities = self.asset_service.get_import_capabilities()
            maya_available = capabilities.get("maya_available", False)
            crash_logger.log("PREVIEW-3: Maya capabilities checked")

            if not maya_available:
                crash_logger.log("PREVIEW-4: Maya not available, showing warning")
                QMessageBox.warning(
                    self,
                    "Maya Import Not Available",
                    "Maya import service is not available.\n\nPlease ensure you're running TunnelUI from within Maya.",
                )
                return

            # Create and show progress dialog
            crash_logger.log("PREVIEW-5: Creating progress dialog")
            from ui.widgets.import_progress_dialog import ImportProgressDialog

            progress_dialog = ImportProgressDialog(
                parent=self,
                asset_service=self.asset_service,
                asset_id=asset_id,
                asset_name=asset_name,
            )
            crash_logger.log("PREVIEW-6: Progress dialog created")

            # Start the import
            crash_logger.log("PREVIEW-7: Starting import")
            progress_dialog.start_import()
            crash_logger.log("PREVIEW-8: Import started, about to show dialog")

            # Show the dialog (this will block until import completes)
            crash_logger.log("PREVIEW-9: Calling progress_dialog.exec()")
            result = progress_dialog.exec()
            crash_logger.log(f"PREVIEW-10: Progress dialog returned result: {result}")

            crash_logger.log("PREVIEW-11: Checking dialog result")
            # Use integer comparison instead of QDialog.Accepted constant to avoid attribute issues
            if result == 1:  # QDialog.Accepted = 1
                crash_logger.log("PREVIEW-12: Dialog accepted, getting import result")
                import_result = progress_dialog.get_import_result()
                crash_logger.log("PREVIEW-13: Import result retrieved")

                if import_result and import_result.success:
                    crash_logger.log("PREVIEW-14: Import successful, about to close preview")
                    self.logger.info(f"Maya import completed successfully for {asset_id}")

                    crash_logger.log("PREVIEW-15: About to call self.accept()")
                    # Close the preview dialog after successful import
                    # Use QTimer to delay the close to avoid double-close issues
                    QTimer.singleShot(100, self.accept)
                    crash_logger.log("PREVIEW-16: self.accept() scheduled")

                else:
                    crash_logger.log("PREVIEW-14: Import failed")
                    self.logger.error(f"Maya import failed for {asset_id}")
            else:
                crash_logger.log("PREVIEW-12: Import cancelled or failed")
                self.logger.info(f"Maya import cancelled for {asset_id}")

            crash_logger.log("PREVIEW-17: Maya import method finished")

        except Exception as e:
            crash_logger.log(f"PREVIEW-ERROR: Exception in Maya import: {e}")
            self.logger.error(f"Maya import error for {asset_id}: {e}")
            QMessageBox.critical(
                self,
                "Maya Import Error",
                f"Failed to import asset to Maya:\n\n{e}",
            )

    def _import_to_unreal(self, zip_path: Path, asset_id: str):
        """Import asset to Unreal (placeholder for future implementation)"""
        self.logger.info(f"Unreal import requested for asset {asset_id} from: {zip_path}")
        QMessageBox.information(
            self,
            "Unreal Import",
            f"Unreal import functionality coming soon!\n\nAsset: {asset_id}\nFile: {zip_path.name}\n\nFor now, the zip file will be opened instead.",
        )
        # Fallback to opening zip file
        self._open_zip_file(zip_path, asset_id)
