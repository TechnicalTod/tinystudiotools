"""
Main Window - Maya Asset Publishing Tool
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

import os
import sys
from pathlib import Path

# Add the source path to sys.path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent

# Ensure the Publisher src directory is in the path
publisher_src = str(src_dir)
if publisher_src not in sys.path:
    sys.path.insert(0, publisher_src)

# Also add the Publisher root directory for relative imports
publisher_root = src_dir.parent
if str(publisher_root) not in sys.path:
    sys.path.insert(0, str(publisher_root))

try:
    from ui.maya_integration import MayaUIIntegration
    from ui.publish_widget import PublishWidget
    from ui.browse_widget import BrowseWidget
    from ui.settings_widget import SettingsWidget
    from ui.validation_widget import ValidationWidget
    from core.models import PublishRecord, EnvironmentContext
    from database.publish_database import PublishDatabase
    from file_system.network_publisher import NetworkDrivePublisher
    from configuration.config_manager import ConfigurationManager
    from validation.validation_manager import ValidationManager
except ImportError as e:
    # Fallback: try with Publisher prefix
    try:
        from Publisher.src.ui.maya_integration import MayaUIIntegration
        from Publisher.src.ui.publish_widget import PublishWidget
        from Publisher.src.ui.browse_widget import BrowseWidget
        from Publisher.src.ui.settings_widget import SettingsWidget
        from Publisher.src.ui.validation_widget import ValidationWidget
        from Publisher.src.core.models import PublishRecord, EnvironmentContext
        from Publisher.src.database.publish_database import PublishDatabase
        from Publisher.src.file_system.network_publisher import NetworkDrivePublisher
        from Publisher.src.configuration.config_manager import ConfigurationManager
        from Publisher.src.validation.validation_manager import ValidationManager
    except ImportError as e2:
        print(f"Import error: {e}")
        print(f"Fallback import error: {e2}")
        print(f"Current path: {current_dir}")
        print(f"Src path: {src_dir}")
        print(f"Publisher root: {publisher_root}")
        print(f"sys.path: {sys.path}")
        raise ImportError(f"Could not import Publisher modules: {e}")


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize backend systems
        self.init_backend_systems()

        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.setup_maya_integration()

        # Load initial data
        self.load_initial_data()

    def init_backend_systems(self):
        """Initialize backend systems"""
        try:
            # Configuration manager
            self.config_manager = ConfigurationManager()

            # Database
            db_path = self.config_manager.get_global_config().get("database_path", "publisher.db")
            self.database = PublishDatabase(db_path)

            # Network publisher
            network_path = self.config_manager.get_global_config().get("network_path", "S:/")
            self.network_publisher = NetworkDrivePublisher(network_path)

            # Validation manager
            self.validation_manager = ValidationManager()

            print("✅ Backend systems initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize backend systems: {e}")
            QMessageBox.critical(
                self, "Initialization Error", f"Failed to initialize backend systems:\n{str(e)}"
            )

    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Maya Asset Publishing Tool")
        self.setMinimumSize(1000, 700)

        # Apply Maya styling if available
        MayaUIIntegration.load_maya_stylesheet(self)

        # Central widget with tab layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_main_tab()  # Browse + Publish side by side
        self.create_validation_tab()  # Validation on its own tab
        self.create_settings_tab()  # Settings on its own tab

        # Status bar
        self.create_status_bar()

        # Menu bar
        self.create_menu_bar()

    def create_main_tab(self):
        """Create the main tab with browse and publish side by side"""
        main_tab = QWidget()
        layout = QHBoxLayout(main_tab)
        layout.setSpacing(10)

        # Browse widget on the left
        self.browse_widget = BrowseWidget()
        browse_frame = QFrame()
        browse_frame.setFrameStyle(QFrame.StyledPanel)
        browse_layout = QVBoxLayout(browse_frame)
        browse_layout.addWidget(QLabel("📂 Browse Published Files"))
        browse_layout.addWidget(self.browse_widget)

        # Publish widget on the right
        self.publish_widget = PublishWidget()
        publish_frame = QFrame()
        publish_frame.setFrameStyle(QFrame.StyledPanel)
        publish_layout = QVBoxLayout(publish_frame)
        publish_layout.addWidget(QLabel("📤 Publish Assets"))
        publish_layout.addWidget(self.publish_widget)

        # Add to layout with equal sizing
        layout.addWidget(browse_frame, 1)
        layout.addWidget(publish_frame, 1)

        self.tab_widget.addTab(main_tab, "🏠 Main")

    def create_validation_tab(self):
        """Create the validation tab"""
        self.validation_widget = ValidationWidget()
        self.tab_widget.addTab(self.validation_widget, "✅ Validation")

    def create_settings_tab(self):
        """Create the settings tab"""
        self.settings_widget = SettingsWidget()
        self.tab_widget.addTab(self.settings_widget, "⚙️ Settings")

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status labels
        self.maya_status_label = QLabel("Maya: Unknown")
        self.db_status_label = QLabel("DB: Unknown")
        self.network_status_label = QLabel("Network: Unknown")

        # Add to status bar
        self.status_bar.addWidget(self.maya_status_label)
        self.status_bar.addPermanentWidget(self.db_status_label)
        self.status_bar.addPermanentWidget(self.network_status_label)

        # Update status
        self.update_status_bar()

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all_data)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        validate_scene_action = QAction("&Validate Scene", self)
        validate_scene_action.triggered.connect(self.validate_current_scene)
        tools_menu.addAction(validate_scene_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_connections(self):
        """Setup signal connections between widgets"""
        # Publish widget connections
        self.publish_widget.validation_requested.connect(self.run_validation)
        self.publish_widget.publish_requested.connect(self.handle_publish)
        self.publish_widget.version_update_requested.connect(self.update_version_info)

        # Browse widget connections
        self.browse_widget.refresh_requested.connect(self.refresh_browse_data)
        self.browse_widget.file_selected.connect(self.handle_file_selection)
        self.browse_widget.show_filter_changed.connect(self.handle_show_filter_change)

        # Settings widget connections
        self.settings_widget.settings_changed.connect(self.handle_settings_change)
        self.settings_widget.network_test_requested.connect(self.test_network_connection)

        # Validation widget connections
        self.validation_widget.validation_requested.connect(self.run_validation_from_tab)

    def setup_maya_integration(self):
        """Setup Maya-specific integration"""
        try:
            # Try to detect Maya
            import maya.cmds as cmds

            self.maya_available = True
            self.maya_status_label.setText("Maya: ✅ Connected")
            self.maya_status_label.setStyleSheet("QLabel { color: #4CAF50; }")

        except ImportError:
            self.maya_available = False
            self.maya_status_label.setText("Maya: ❌ Not Available")
            self.maya_status_label.setStyleSheet("QLabel { color: #f44336; }")

    def load_initial_data(self):
        """Load initial data into widgets"""
        # Load settings
        try:
            settings = self.config_manager.get_global_config()
            self.settings_widget.set_settings(settings)
        except Exception as e:
            print(f"Warning: Could not load settings: {e}")

        # Load browse data
        self.refresh_browse_data()

        # Update context in publish widget
        self.update_publish_context()

    def update_status_bar(self):
        """Update status bar information"""
        # Database status
        try:
            record_count = len(self.database.get_all_publishes())
            self.db_status_label.setText(f"DB: ✅ {record_count} records")
            self.db_status_label.setStyleSheet("QLabel { color: #4CAF50; }")
        except Exception:
            self.db_status_label.setText("DB: ❌ Error")
            self.db_status_label.setStyleSheet("QLabel { color: #f44336; }")

        # Network status
        try:
            network_path = self.config_manager.get_global_config().get("network_path", "S:/")
            if Path(network_path).exists():
                self.network_status_label.setText("Network: ✅ OK")
                self.network_status_label.setStyleSheet("QLabel { color: #4CAF50; }")
            else:
                self.network_status_label.setText("Network: ❌ Unavailable")
                self.network_status_label.setStyleSheet("QLabel { color: #f44336; }")
        except Exception:
            self.network_status_label.setText("Network: ❌ Error")
            self.network_status_label.setStyleSheet("QLabel { color: #f44336; }")

    def update_publish_context(self):
        """Update the publish widget context"""
        try:
            if self.maya_available:
                try:
                    from maya_integration.scene_handler import SceneHandler
                except ImportError:
                    from Publisher.src.maya_integration.scene_handler import SceneHandler

                scene_handler = SceneHandler()
                context = scene_handler.get_environment_context()
            else:
                # Create a default context for testing
                context = EnvironmentContext(
                    scene_name="test_scene",
                    scene_path="",
                    maya_version="2024",
                    scene_units="cm",
                    linear_units="cm",
                    angular_units="deg",
                    frame_rate="24 fps",
                    frame_range=(1, 100),
                    current_time=1,
                )

            self.publish_widget.update_context(context)

        except Exception as e:
            print(f"Warning: Could not update context: {e}")

    def run_validation(self, publish_data):
        """Run validation on the current scene/publish data"""
        try:
            # Create validation context
            validation_context = {
                "publish_data": publish_data,
                "maya_available": self.maya_available,
            }

            # Run validation
            results = self.validation_manager.run_all_validations(validation_context)

            # Update publish widget with results
            self.publish_widget.update_validation_results(results)

            return results

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Validation Error", error_msg)
            return []

    def run_validation_from_tab(self, validation_context):
        """Run validation from the validation tab"""
        try:
            # Add maya availability to context
            validation_context["maya_available"] = self.maya_available

            # Run validation
            results = self.validation_manager.run_all_validations(validation_context)

            # Update validation widget with results
            self.validation_widget.update_validation_results(results)

            return results

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Validation Error", error_msg)
            return []

    def handle_publish(self, publish_data):
        """Handle publish request"""
        try:
            # Run validation first
            validation_results = self.run_validation(publish_data)

            # Check if validation passed
            has_errors = any(not result.passed for result in validation_results)

            if has_errors:
                reply = QMessageBox.question(
                    self,
                    "Validation Warnings",
                    "Some validation checks failed. Continue with publish?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            # Create publish record
            publish_record = PublishRecord(**publish_data)

            # Publish to network
            network_path = self.network_publisher.publish_file(
                publish_record, publish_data.get("source_file", "")
            )

            # Update record with network path
            publish_record.file_path = network_path

            # Save to database
            self.database.create_publish(publish_record)

            # Show success message
            QMessageBox.information(
                self, "Publish Successful", f"Successfully published:\n{network_path}"
            )

            # Refresh data
            self.refresh_browse_data()
            self.update_status_bar()

        except Exception as e:
            error_msg = f"Publish failed: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Publish Error", error_msg)

    def update_version_info(self, asset_info):
        """Update version information"""
        try:
            # Query database for latest version
            latest_version = self.database.get_latest_version(
                asset_info["show_name"],
                asset_info["asset_type"],
                asset_info["asset_id"],
                asset_info["task"],
            )

            next_version = (latest_version or 0) + 1
            self.publish_widget.set_version(next_version)

        except Exception as e:
            print(f"Warning: Could not update version: {e}")

    def refresh_browse_data(self):
        """Refresh browse widget data"""
        try:
            publishes = self.database.get_all_publishes()
            publish_dicts = [record.to_dict() for record in publishes]
            self.browse_widget.load_publishes(publish_dicts)

        except Exception as e:
            print(f"Warning: Could not refresh browse data: {e}")

    def handle_file_selection(self, file_data):
        """Handle file selection in browse widget"""
        print(f"Selected file: {file_data.get('file_path', 'Unknown')}")

    def handle_show_filter_change(self, show_name):
        """Handle show filter change"""
        print(f"Show filter changed to: {show_name}")

    def handle_settings_change(self, settings):
        """Handle settings change"""
        try:
            # Update configuration
            self.config_manager.update_global_config(settings)

            # Update backend systems if needed
            if "network_path" in settings:
                self.network_publisher.base_path = Path(settings["network_path"])

            if "database_path" in settings and settings["database_path"]:
                # Potentially reconnect to new database
                pass

            # Update status bar
            self.update_status_bar()

        except Exception as e:
            print(f"Warning: Could not apply settings: {e}")

    def test_network_connection(self, network_path):
        """Test network connection"""
        try:
            path = Path(network_path)
            success = path.exists() and path.is_dir()

            if success:
                print(f"✅ Network path accessible: {network_path}")
            else:
                print(f"❌ Network path not accessible: {network_path}")

            return success

        except Exception as e:
            print(f"❌ Network test error: {e}")
            return False

    def refresh_all_data(self):
        """Refresh all data in the application"""
        self.load_initial_data()
        self.update_status_bar()

    def validate_current_scene(self):
        """Validate the current Maya scene"""
        if not self.maya_available:
            QMessageBox.warning(
                self, "Maya Not Available", "Maya is not available for scene validation."
            )
            return

        try:
            # Get current publish data from publish widget
            publish_data = self.publish_widget.get_publish_data()

            # Run validation
            self.run_validation(publish_data)

            # Switch to publish tab to show results
            self.tab_widget.setCurrentIndex(0)

        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate scene:\n{str(e)}")

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Maya Asset Publishing Tool</h2>
        <p>Version 1.0</p>
        <p>A professional asset publishing pipeline for Maya.</p>
        
        <h3>Features:</h3>
        <ul>
        <li>Asset publishing with validation</li>
        <li>Database tracking and versioning</li>
        <li>Network file management</li>
        <li>Maya integration</li>
        </ul>
        
        <p>Built with Python and PySide.</p>
        """

        QMessageBox.about(self, "About Maya Publisher", about_text)

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Save any pending settings
            settings = self.settings_widget.get_settings()
            self.config_manager.update_global_config(settings)

        except Exception as e:
            print(f"Warning: Could not save settings on exit: {e}")

        event.accept()


def main():
    """Main function to run the application"""
    print("🚀 Maya Publisher - main() function called")

    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("Maya Asset Publishing Tool")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("Studio Pipeline")

        # Check if running in Maya
        try:
            maya_main_window = MayaUIIntegration.get_maya_main_window()
            window = MainWindow(maya_main_window)
            MayaUIIntegration.center_window(window)
            print("✅ Maya Publisher created with Maya parent")
        except Exception as e:
            # Running standalone
            window = MainWindow()
            print(f"✅ Maya Publisher created standalone (Maya error: {e})")

        window.show()
        print("✅ Maya Publisher window shown")

        # Don't exec the app if we're in Maya
        try:
            import maya.cmds

            print("✅ Maya Publisher launched in Maya environment")
            return window
        except ImportError:
            print("✅ Maya Publisher launched standalone")
            return app.exec_()

    except Exception as e:
        print(f"❌ Error in main(): {e}")
        import traceback

        traceback.print_exc()
        raise


def debug_test():
    """Simple debug function to test imports"""
    print("✅ Maya Publisher debug_test() function called successfully!")
    return "Debug test passed"


if __name__ == "__main__":
    main()
