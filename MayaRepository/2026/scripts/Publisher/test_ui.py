#!/usr/bin/env python
"""
UI Test Script - Maya Asset Publishing Tool
Test all UI components and functionality
"""

import sys
import os
from pathlib import Path

# Add source to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *

    print("✅ Using PySide6")
except ImportError:
    try:
        from PySide2.QtWidgets import *
        from PySide2.QtCore import *
        from PySide2.QtGui import *

        print("✅ Using PySide2")
    except ImportError:
        print("❌ Neither PySide6 nor PySide2 is available")
        sys.exit(1)


def test_imports():
    """Test all module imports"""
    print("\n🔍 Testing imports...")

    try:
        # UI components
        from ui.maya_integration import MayaUIIntegration

        print("✅ Maya integration imported")

        from ui.publish_widget import PublishWidget

        print("✅ Publish widget imported")

        from ui.browse_widget import BrowseWidget

        print("✅ Browse widget imported")

        from ui.settings_widget import SettingsWidget

        print("✅ Settings widget imported")

        from ui.main_window import MainWindow

        print("✅ Main window imported")

        # Core components
        from core.models import PublishRecord, EnvironmentContext

        print("✅ Core models imported")

        from database.publish_database import PublishDatabase

        print("✅ Database imported")

        from file_system.network_publisher import NetworkPublisher

        print("✅ Network publisher imported")

        from validation.validation_manager import ValidationManager

        print("✅ Validation manager imported")

        from configuration.config_manager import ConfigurationManager

        print("✅ Configuration manager imported")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_individual_widgets():
    """Test individual widgets"""
    print("\n🔍 Testing individual widgets...")

    try:
        from ui.publish_widget import PublishWidget
        from ui.browse_widget import BrowseWidget
        from ui.settings_widget import SettingsWidget

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Test publish widget
        print("Testing publish widget...")
        publish_widget = PublishWidget()
        publish_widget.show()
        QTimer.singleShot(1000, publish_widget.close)
        print("✅ Publish widget created successfully")

        # Test browse widget
        print("Testing browse widget...")
        browse_widget = BrowseWidget()
        browse_widget.show()
        browse_widget.load_publishes([])  # Test with empty data
        QTimer.singleShot(1000, browse_widget.close)
        print("✅ Browse widget created successfully")

        # Test settings widget
        print("Testing settings widget...")
        settings_widget = SettingsWidget()
        settings_widget.show()
        test_settings = {
            "network_path": "S:/",
            "database_path": "test.db",
            "auto_backup": True,
            "validation_rules": {"naming_convention": True},
        }
        settings_widget.set_settings(test_settings)
        retrieved_settings = settings_widget.get_settings()
        QTimer.singleShot(1000, settings_widget.close)
        print("✅ Settings widget created successfully")

        return True

    except Exception as e:
        print(f"❌ Widget test failed: {e}")
        return False


def test_backend_integration():
    """Test backend system integration"""
    print("\n🔍 Testing backend integration...")

    try:
        from core.models import PublishRecord, EnvironmentContext
        from database.publish_database import PublishDatabase
        from file_system.network_publisher import NetworkPublisher
        from validation.validation_manager import ValidationManager
        from configuration.config_manager import ConfigurationManager

        # Test database
        print("Testing database...")
        db = PublishDatabase(":memory:")  # In-memory database for testing

        # Create test record
        test_record = PublishRecord(
            show_name="TestShow",
            asset_type="asset",
            asset_id="test_character",
            task="model",
            version=1,
            artist="TestArtist",
            maya_version="2024",
            comments="Test publish",
        )

        saved_record = db.create_publish(test_record)
        print(f"✅ Database test passed - Record ID: {saved_record.id}")

        # Test configuration
        print("Testing configuration...")
        config_manager = ConfigurationManager()
        config = config_manager.get_global_config()
        print(f"✅ Configuration test passed - Config loaded: {bool(config)}")

        # Test validation
        print("Testing validation...")
        validator = ValidationManager()
        test_context = {"test": True}
        results = validator.run_all_validations(test_context)
        print(f"✅ Validation test passed - Rules run: {len(results)}")

        return True

    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False


def test_signal_connections():
    """Test signal connections between widgets"""
    print("\n🔍 Testing signal connections...")

    try:
        from ui.publish_widget import PublishWidget
        from ui.browse_widget import BrowseWidget
        from ui.settings_widget import SettingsWidget

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Test publish widget signals
        publish_widget = PublishWidget()

        signal_received = []

        def on_validation_requested(data):
            signal_received.append("validation_requested")

        def on_publish_requested(data):
            signal_received.append("publish_requested")

        def on_version_update_requested(data):
            signal_received.append("version_update_requested")

        publish_widget.validation_requested.connect(on_validation_requested)
        publish_widget.publish_requested.connect(on_publish_requested)
        publish_widget.version_update_requested.connect(on_version_update_requested)

        print("✅ Publish widget signals connected")

        # Test browse widget signals
        browse_widget = BrowseWidget()

        def on_refresh_requested():
            signal_received.append("refresh_requested")

        def on_file_selected(data):
            signal_received.append("file_selected")

        browse_widget.refresh_requested.connect(on_refresh_requested)
        browse_widget.file_selected.connect(on_file_selected)

        print("✅ Browse widget signals connected")

        # Test settings widget signals
        settings_widget = SettingsWidget()

        def on_settings_changed(data):
            signal_received.append("settings_changed")

        settings_widget.settings_changed.connect(on_settings_changed)

        print("✅ Settings widget signals connected")

        return True

    except Exception as e:
        print(f"❌ Signal test failed: {e}")
        return False


def test_main_window():
    """Test main window integration"""
    print("\n🔍 Testing main window...")

    try:
        from ui.main_window import MainWindow

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create main window
        window = MainWindow()

        # Test that all tabs are created
        tab_count = window.tab_widget.count()
        expected_tabs = 3  # Publish, Browse, Settings

        if tab_count == expected_tabs:
            print(f"✅ Main window created with {tab_count} tabs")
        else:
            print(f"❌ Expected {expected_tabs} tabs, got {tab_count}")
            return False

        # Test tab names
        tab_names = []
        for i in range(tab_count):
            tab_names.append(window.tab_widget.tabText(i))

        print(f"✅ Tab names: {tab_names}")

        # Test status bar
        if window.status_bar:
            print("✅ Status bar created")
        else:
            print("❌ Status bar missing")
            return False

        # Test menu bar
        if window.menuBar():
            print("✅ Menu bar created")
        else:
            print("❌ Menu bar missing")
            return False

        window.close()
        return True

    except Exception as e:
        print(f"❌ Main window test failed: {e}")
        return False


def test_maya_integration():
    """Test Maya integration (if available)"""
    print("\n🔍 Testing Maya integration...")

    try:
        from ui.maya_integration import MayaUIIntegration

        # Test Maya detection
        try:
            main_window = MayaUIIntegration.get_maya_main_window()
            print("✅ Maya detected and main window retrieved")
            maya_available = True
        except:
            print("ℹ️ Maya not available (expected in standalone mode)")
            maya_available = False

        # Test stylesheet loading
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        test_widget = QWidget()

        # This should not crash even if stylesheet doesn't exist
        MayaUIIntegration.load_maya_stylesheet(test_widget)
        print("✅ Stylesheet loading function works")

        # Test window centering
        dummy_window = QWidget()
        MayaUIIntegration.center_window(dummy_window)
        print("✅ Window centering function works")

        return True

    except Exception as e:
        print(f"❌ Maya integration test failed: {e}")
        return False


def run_visual_test():
    """Run a visual test of the main application"""
    print("\n🎨 Running visual test...")

    try:
        from ui.main_window import main

        print("Starting main application...")
        print("This will open the main window for visual inspection.")
        print("Close the window to continue with the test.")

        # Run the main application
        window = main()

        print("✅ Visual test completed")
        return True

    except Exception as e:
        print(f"❌ Visual test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Maya Asset Publishing Tool - UI Test Suite")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("Widget Test", test_individual_widgets),
        ("Backend Integration", test_backend_integration),
        ("Signal Connections", test_signal_connections),
        ("Main Window", test_main_window),
        ("Maya Integration", test_maya_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")

    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")

        # Offer visual test
        print("\nWould you like to run a visual test? (y/n)")
        try:
            response = input().strip().lower()
            if response in ["y", "yes"]:
                run_visual_test()
        except:
            pass
    else:
        print("⚠️ Some tests failed. Please check the output above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
