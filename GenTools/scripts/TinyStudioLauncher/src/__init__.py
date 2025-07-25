"""
TinyStudioLauncher - Modern application launcher with environment isolation
"""

__version__ = "0.1.0"
__author__ = "Saga Studio Pipeline Team"

from .environment_manager import EnvironmentManager
from .launch_controller import LaunchController, LaunchConfig

__all__ = ["EnvironmentManager", "LaunchController", "LaunchConfig"]
