#!/usr/bin/env python
"""
TinyStudioLauncher - Main Entry Point

This script starts the TinyStudioLauncher UI application.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging with UTF-8 encoding
# Create handlers with explicit UTF-8 encoding for console output
stream_handler = logging.StreamHandler(sys.stdout)
if hasattr(stream_handler.stream, "reconfigure"):
    stream_handler.stream.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "encoding"):
    sys.stdout.encoding = "utf-8"

# Configure the formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)

# File handler always uses UTF-8
file_handler = logging.FileHandler(Path.home() / "TinyStudioLauncher.log", encoding="utf-8")
file_handler.setFormatter(formatter)

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stream_handler)
root_logger.addHandler(file_handler)

logger = logging.getLogger("TinyLauncher")

# Add project directory to path if needed
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))


def launch_ui():
    """Launch the TinyStudioLauncher UI"""
    try:
        # Try both PySide6 (preferred) and PySide2 (Maya compatibility)
        try:
            from PySide6.QtWidgets import QApplication

            # Check if we're using PySide6 to determine which exec method to use
            USING_PYSIDE6 = True
        except ImportError:
            logger.info("PySide6 not found, falling back to PySide2")
            from PySide2.QtWidgets import QApplication

            USING_PYSIDE6 = False

        # Import the UI
        from src.ui import TinyLauncherWindow

        # Start the application
        app = QApplication(sys.argv)
        app.setApplicationName("TinyStudioLauncher")
        app.setApplicationVersion("1.0.0")

        # Create and show the main window
        window = TinyLauncherWindow()
        window.show()

        logger.info("TinyStudioLauncher UI started")

        # Execute the application
        if USING_PYSIDE6:
            sys.exit(app.exec())  # PySide6 uses exec()
        else:
            sys.exit(app.exec_())  # PySide2 uses exec_()

    except Exception as e:
        logger.error(f"Error starting TinyStudioLauncher: {str(e)}")
        import traceback

        traceback.print_exc()

        # Keep the console open if there was an error
        if not sys.stdout.isatty():
            input("\nPress Enter to exit...")


def launch_direct(app_name, version, show, fast_mode=False):
    """
    Launch an application directly without UI

    Args:
        app_name: Application name (e.g., "maya", "unreal")
        version: Version string (e.g., "2023", "5.6")
        show: Show name
        fast_mode: Whether to use fast startup optimizations
    """
    # Import necessary modules
    from src.environment_manager import EnvironmentManager
    from src.launch_controller import LaunchController

    # Initialize components
    env_manager = EnvironmentManager(project_dir)
    controller = LaunchController(project_dir / "configs", env_manager)

    try:
        # Prepare launch config
        config = controller.prepare_launch_config(app_name, version, show)
        logger.info(f"Launching {app_name} {version} for show {show}")

        # Apply fast mode optimizations if requested
        if fast_mode and app_name.lower() == "maya":
            config.env_vars["MAYA_NO_PLUGIN_LOAD"] = "1"
            config.env_vars["MAYA_DISABLE_CIP"] = "1"
            config.env_vars["MAYA_DISABLE_CER"] = "1"
            logger.info("Fast mode enabled: Disabled plugins and telemetry")

        # Launch the application with non-blocking process
        process = controller.launch_application(config)
        logger.info(f"{app_name} {version} launched successfully (PID: {process.pid})")

        return process

    except Exception as e:
        logger.error(f"Error launching {app_name}: {str(e)}")
        return None


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="TinyStudioLauncher")
    parser.add_argument("--app", help="Application to launch directly (e.g., maya, unreal)")
    parser.add_argument("--version", default="", help="Application version")
    parser.add_argument("--show", default="001_SHOWTEST", help="Show name")
    parser.add_argument("--fast", action="store_true", help="Enable fast startup mode")

    args = parser.parse_args()

    if args.app:
        # Direct launch mode
        launch_direct(args.app, args.version, args.show, args.fast)
    else:
        # UI mode
        launch_ui()
