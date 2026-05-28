"""
Import Progress Dialog

A dialog for displaying real-time progress during Maya asset imports,
with progress bar, current step display, and detailed logs.
"""

import logging
import asyncio
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QTextEdit,
    QPushButton,
    QGroupBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QFont

# Add crash logger import
import sys
from pathlib import Path

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


class ImportWorker(QObject):
    """Worker object for running async import in separate thread"""

    progress_updated = Signal(str, float)  # step, percentage
    import_completed = Signal(object)  # import_result
    import_failed = Signal(str)  # error_message

    def __init__(self, asset_service, asset_id: str):
        super().__init__()
        self.asset_service = asset_service
        self.asset_id = asset_id
        self.is_cancelled = False

    def run_import(self):
        """Run the Maya import operation"""
        try:

            def progress_callback(step: str, percentage: float):
                if not self.is_cancelled:
                    self.progress_updated.emit(step, percentage)

            # Run the async import
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.asset_service.import_asset_to_maya(
                    asset_id=self.asset_id, progress_callback=progress_callback
                )
            )

            loop.close()

            if not self.is_cancelled:
                self.import_completed.emit(result)

        except Exception as e:
            if not self.is_cancelled:
                self.import_failed.emit(str(e))

    def cancel(self):
        """Cancel the import operation"""
        self.is_cancelled = True


class ImportProgressDialog(QDialog):
    """Dialog for displaying Maya import progress"""

    def __init__(self, parent=None, asset_service=None, asset_id: str = "", asset_name: str = ""):
        super().__init__(parent)
        self.asset_service = asset_service
        self.asset_id = asset_id
        self.asset_name = asset_name
        self.logger = logging.getLogger(__name__)

        # Worker thread for import
        self.worker_thread = None
        self.worker = None
        self.import_result = None

        self.setWindowTitle(f"Importing {asset_name}")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Asset info section
        info_group = QGroupBox("Asset Information")
        info_layout = QVBoxLayout(info_group)

        self.asset_label = QLabel(f"<b>Asset:</b> {self.asset_name}")
        self.asset_id_label = QLabel(f"<b>ID:</b> {self.asset_id}")

        info_layout.addWidget(self.asset_label)
        info_layout.addWidget(self.asset_id_label)
        layout.addWidget(info_group)

        # Progress section
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Current step label
        self.step_label = QLabel("Preparing import...")
        self.step_label.setWordWrap(True)
        font = QFont()
        font.setBold(True)
        self.step_label.setFont(font)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # Progress percentage label
        self.percentage_label = QLabel("0%")
        self.percentage_label.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(self.step_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.percentage_label)
        layout.addWidget(progress_group)

        # Detailed log section
        log_group = QGroupBox("Import Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
        """
        )

        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.close_button = QPushButton("Close")
        self.close_button.setEnabled(False)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect signals and slots"""
        self.cancel_button.clicked.connect(self._cancel_import)
        self.close_button.clicked.connect(self.accept)

    def start_import(self):
        """Start the Maya import process"""
        if not self.asset_service:
            self._add_log("ERROR: Asset service not available", "error")
            self._import_failed("Asset service not available")
            return

        # Check if Maya import is available
        capabilities = self.asset_service.get_import_capabilities()
        if not capabilities.get("maya_available", False):
            self._add_log("ERROR: Maya import service not available", "error")
            self._import_failed("Maya import service not available")
            return

        self._add_log(f"Starting import of {self.asset_name} ({self.asset_id})", "info")

        # Create worker and thread
        self.worker = ImportWorker(self.asset_service, self.asset_id)
        self.worker_thread = QThread()

        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.import_completed.connect(self._import_completed)
        self.worker.import_failed.connect(self._import_failed)
        self.worker_thread.started.connect(self.worker.run_import)

        # Start the thread
        self.worker_thread.start()

    def _update_progress(self, step: str, percentage: float):
        """Update progress display"""
        self.step_label.setText(step)
        self.progress_bar.setValue(int(percentage))
        self.percentage_label.setText(f"{percentage:.1f}%")

        self._add_log(f"[{percentage:.1f}%] {step}", "progress")

    def _import_completed(self, import_result):
        """Handle successful import completion"""
        crash_logger.log("UI-1: Import completion handler started")

        self.import_result = import_result
        crash_logger.log("UI-2: Import result stored")

        if import_result.success:
            crash_logger.log("UI-3: Processing successful import result")

            self._add_log("✅ Import completed successfully!", "success")
            self._add_log(f"Duration: {import_result.import_duration:.2f} seconds", "info")
            self._add_log(f"Imported objects: {len(import_result.imported_objects)}", "info")
            self._add_log(f"Created materials: {len(import_result.created_materials)}", "info")

            if import_result.cache_entry:
                self._add_log("Cache entry created for future imports", "info")

            crash_logger.log("UI-4: Setting UI completion status")
            self.step_label.setText("✅ Import completed successfully!")
            self.progress_bar.setValue(100)
            self.percentage_label.setText("100%")
            crash_logger.log("UI-5: UI status updated successfully")

            # Auto-close dialog on successful import
            crash_logger.log("UI-5.5: About to auto-accept dialog for successful import")
            self.accept()  # This will close the dialog and return QDialog.Accepted
            crash_logger.log("UI-5.6: Auto-accept completed")

        else:
            crash_logger.log("UI-3: Processing failed import result")
            self._add_log(f"❌ Import failed: {import_result.error_message}", "error")
            self.step_label.setText(f"❌ Import failed: {import_result.error_message}")

            # For failed imports, just update buttons but don't auto-close
            crash_logger.log("UI-6: About to cleanup worker")
            self._cleanup_worker()
            crash_logger.log("UI-7: Worker cleanup completed")

            crash_logger.log("UI-8: Updating button states")
            self.cancel_button.setEnabled(False)
            self.close_button.setEnabled(True)
            crash_logger.log("UI-9: Import completion handler finished")

    def _import_failed(self, error_message: str):
        """Handle import failure"""
        crash_logger.log("UI-FAIL-1: Import failure handler started")

        self._add_log(f"❌ Import failed: {error_message}", "error")
        self.step_label.setText(f"❌ Import failed: {error_message}")

        crash_logger.log("UI-FAIL-2: About to cleanup worker")
        self._cleanup_worker()
        crash_logger.log("UI-FAIL-3: Worker cleanup completed")

        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        crash_logger.log("UI-FAIL-4: Import failure handler finished")

    def _cancel_import(self):
        """Cancel the import operation"""
        crash_logger.log("UI-CANCEL-1: Import cancel handler started")

        if self.worker:
            self.worker.cancel()

        self._add_log("Import cancelled by user", "warning")
        self.step_label.setText("Import cancelled")

        crash_logger.log("UI-CANCEL-2: About to cleanup worker")
        self._cleanup_worker()
        crash_logger.log("UI-CANCEL-3: Worker cleanup completed")

        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        crash_logger.log("UI-CANCEL-4: Import cancel handler finished")

    def _cleanup_worker(self):
        """Clean up worker thread"""
        crash_logger.log("UI-CLEANUP-1: Worker cleanup started")

        if self.worker_thread and self.worker_thread.isRunning():
            crash_logger.log("UI-CLEANUP-2: Thread is running, quitting...")
            self.worker_thread.quit()
            crash_logger.log("UI-CLEANUP-3: Thread quit called, waiting...")
            self.worker_thread.wait(3000)  # Wait up to 3 seconds
            crash_logger.log("UI-CLEANUP-4: Thread wait completed")
        else:
            crash_logger.log("UI-CLEANUP-2: No running thread to cleanup")

        crash_logger.log("UI-CLEANUP-5: Worker cleanup finished")

    def _add_log(self, message: str, level: str = "info"):
        """Add a message to the log"""
        timestamp = QTimer()

        # Color coding for different log levels
        colors = {
            "info": "#ffffff",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "progress": "#2196F3",
        }

        color = colors.get(level, "#ffffff")
        formatted_message = f'<span style="color: {color};">{message}</span>'

        self.log_text.append(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Handle dialog close event"""
        crash_logger.log("DIALOG-CLOSE-1: closeEvent started")

        if self.worker_thread and self.worker_thread.isRunning():
            crash_logger.log("DIALOG-CLOSE-2: Worker still running, cancelling...")
            self._cancel_import()
            crash_logger.log("DIALOG-CLOSE-3: Cancel import completed")
        else:
            crash_logger.log("DIALOG-CLOSE-2: No running worker to cancel")

        crash_logger.log("DIALOG-CLOSE-4: About to accept close event")
        event.accept()
        crash_logger.log("DIALOG-CLOSE-5: Close event accepted")

    def accept(self):
        """Override accept to add crash logging"""
        crash_logger.log("DIALOG-ACCEPT-1: Dialog accept started")

        # Check if we should auto-close based on completion
        if hasattr(self, "import_result") and self.import_result and self.import_result.success:
            crash_logger.log("DIALOG-ACCEPT-2: Import successful, proceeding with accept")
        else:
            crash_logger.log("DIALOG-ACCEPT-2: Accept called without successful import")

        crash_logger.log("DIALOG-ACCEPT-3: About to call super().accept()")
        super().accept()
        crash_logger.log("DIALOG-ACCEPT-4: super().accept() completed")

    def reject(self):
        """Override reject to add crash logging"""
        crash_logger.log("DIALOG-REJECT-1: Dialog reject started")

        crash_logger.log("DIALOG-REJECT-2: About to call super().reject()")
        super().reject()
        crash_logger.log("DIALOG-REJECT-3: super().reject() completed")

    def get_import_result(self):
        """Get the import result after completion"""
        crash_logger.log("GET-RESULT-1: Getting import result")
        result = self.import_result
        crash_logger.log("GET-RESULT-2: Import result retrieved")
        return result
