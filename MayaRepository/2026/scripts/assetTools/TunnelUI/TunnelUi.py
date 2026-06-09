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
    from application import TunnelUIApplication, openWindow, show

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

    def show():
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

    openWindow = show

    if __name__ == "__main__":
        print("Cannot run standalone - import failed")
        openWindow()
