"""
TunnelUI Asset Browser - Refactored Version

This is the main entry point for the refactored TunnelUI Asset Browser.
It maintains backward compatibility while using the new modular architecture.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

try:
    # Import from refactored architecture (no 'src.' prefix since src is in path)
    from application import TunnelUIApplication

    def openWindow():
        """
        Main entry point for Maya shelf integration.

        This function maintains the exact same signature as the original
        while using the new refactored architecture underneath.
        """
        try:
            print("🚀 Initializing TunnelUI Application...")
            app = TunnelUIApplication()
            print("✅ Application initialized successfully")

            # Run in appropriate mode based on environment
            if app.environment.is_maya:
                print("🎯 Running in Maya mode")
                return app.run_maya_mode()
            else:
                print("🎯 Running in standalone mode")
                return app.run_standalone()

        except ImportError as ie:
            error_msg = f"Import error during initialization: {ie}"
            print(f"❌ {error_msg}")
            try:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.critical(
                    None,
                    "TunnelUI Import Error",
                    f"Missing dependency:\n{ie}\n\nPlease ensure PySide6 is available in Maya.",
                )
            except Exception:
                print(f"CRITICAL: {error_msg}")
            return None

        except Exception as e:
            error_msg = f"Failed to initialize TunnelUI: {e}"
            print(f"❌ {error_msg}")
            import traceback

            traceback.print_exc()

            try:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.critical(
                    None,
                    "TunnelUI Error",
                    f"Initialization failed:\n{e}\n\nCheck the Script Editor for details.",
                )
            except Exception:
                print(f"CRITICAL ERROR: {error_msg}")
            return None

    # For standalone testing and development
    if __name__ == "__main__":
        print("Starting TunnelUI Asset Browser (Refactored)")
        try:
            app = TunnelUIApplication()
            exit_code = app.run_standalone()
            sys.exit(exit_code if exit_code is not None else 0)
        except Exception as e:
            print(f"Failed to start TunnelUI: {e}")
            sys.exit(1)

except ImportError as e:
    print(f"Refactored version failed to import ({e}), falling back to original implementation")

    def openWindow():
        """
        Fallback entry point when refactored version fails to import.
        """
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication

            if not QApplication.instance():
                QApplication(sys.argv)

            QMessageBox.critical(
                None,
                "TunnelUI Configuration Error",
                "The refactored TunnelUI could not be loaded.\n\n"
                "Please check that all dependencies are available and\n"
                "the asset library is properly configured.",
            )
        except Exception:
            print("CRITICAL: TunnelUI could not be loaded and fallback also failed")
        return None

    if __name__ == "__main__":
        print("Cannot run standalone - import failed")
        openWindow()
