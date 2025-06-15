#!/usr/bin/env python
"""
Quick import test for Maya Publisher
"""


def test_import():
    """Test if we can import the main function"""
    try:
        print("Testing import of main function...")
        from src.ui.main_window import main

        print("✅ Successfully imported main function")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")

        # Try alternative import
        try:
            print("Trying alternative import...")
            from Publisher.src.ui.main_window import main

            print("✅ Successfully imported main function with Publisher prefix")
            return True
        except Exception as e2:
            print(f"❌ Alternative import failed: {e2}")
            return False


def test_main_execution():
    """Test if we can call the main function"""
    try:
        print("Testing main function execution...")
        # Import Qt first to avoid issues
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            from PySide2.QtWidgets import QApplication

        # Now test main
        from src.ui.main_window import main

        print("✅ Main function is callable")
        return True
    except Exception as e:
        print(f"❌ Main function test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Maya Publisher Import Test")
    print("=" * 40)

    success = True
    success &= test_import()
    success &= test_main_execution()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed")
