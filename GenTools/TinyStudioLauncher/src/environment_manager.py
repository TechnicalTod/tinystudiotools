"""
Environment Manager for TinyStudioLauncher

Manages UV virtual environments for different applications and versions.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .log_setup import get_module_logger

logger = get_module_logger(__name__)


class EnvironmentManager:
    """Manages UV virtual environments for different applications"""

    def __init__(self, base_path: Path):
        """
        Initialize the environment manager.

        Args:
            base_path: Base directory for TinyStudioLauncher
        """
        self.base_path = Path(base_path)
        self.environments_dir = self.base_path / "environments"
        self.requirements_dir = self.base_path / "requirements"

        # Ensure directories exist
        self.environments_dir.mkdir(exist_ok=True, parents=True)
        self.requirements_dir.mkdir(exist_ok=True, parents=True)

        logger.info(f"EnvironmentManager initialized at {self.base_path}")

    def create_environment(self, app_name: str, python_version: str) -> bool:
        """
        Create a new UV environment for an application.

        Args:
            app_name: Name of the application (e.g., "maya-2026")
            python_version: Python version to use (e.g., "3.9")

        Returns:
            True if successful, False otherwise
        """
        env_path = self.environments_dir / app_name

        try:
            logger.info(f"Creating environment for {app_name} with Python {python_version}")

            # Use uv to create virtual environment with specific Python version
            cmd = ["uv", "venv", str(env_path), "--python", python_version]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to create environment: {result.stderr}")
                return False

            try:
                logger.info(f"✓ Created environment for {app_name}")
            except UnicodeEncodeError:
                logger.info(f"Successfully created environment for {app_name}")

            # Create a marker file with environment info
            info = {
                "app_name": app_name,
                "python_version": python_version,
                "created_at": subprocess.check_output(["date", "/t"], shell=True).decode().strip(),
            }

            info_file = env_path / "env_info.json"
            with open(info_file, "w") as f:
                json.dump(info, f, indent=2)

            return True

        except FileNotFoundError:
            logger.error("UV not found. Please install it with: pip install uv")
            return False
        except Exception as e:
            logger.error(f"Error creating environment: {e}")
            return False

    def sync_environment(self, app_name: str) -> bool:
        """
        Sync packages from requirements file using UV.

        Args:
            app_name: Name of the application

        Returns:
            True if successful, False otherwise
        """
        env_path = self.environments_dir / app_name
        req_file = self.requirements_dir / f"{app_name}.txt"

        if not env_path.exists():
            logger.error(f"Environment {app_name} does not exist")
            return False

        if not req_file.exists():
            logger.warning(f"No requirements file found for {app_name}")
            # Create empty requirements file
            req_file.touch()
            return True

        try:
            logger.info(f"Syncing packages for {app_name}")

            # Use uv pip sync to install requirements
            python_exe = self._get_python_executable(app_name)

            cmd = ["uv", "pip", "sync", "--python", str(python_exe), str(req_file)]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to sync packages: {result.stderr}")
                return False

            try:
                logger.info(f"✓ Synced packages for {app_name}")
            except UnicodeEncodeError:
                logger.info(f"Successfully synced packages for {app_name}")
            return True

        except Exception as e:
            logger.error(f"Error syncing packages: {e}")
            return False

    def install_package(self, app_name: str, package: str) -> bool:
        """
        Install a single package into an environment.

        Args:
            app_name: Name of the application
            package: Package specification (e.g., "numpy==1.26.4")

        Returns:
            True if successful, False otherwise
        """
        env_path = self.environments_dir / app_name

        if not env_path.exists():
            logger.error(f"Environment {app_name} does not exist")
            return False

        try:
            logger.info(f"Installing {package} in {app_name}")

            python_exe = self._get_python_executable(app_name)

            cmd = ["uv", "pip", "install", "--python", str(python_exe), package]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to install package: {result.stderr}")
                return False

            try:
                logger.info(f"✓ Installed {package} in {app_name}")
            except UnicodeEncodeError:
                logger.info(f"Successfully installed {package} in {app_name}")

            # Update requirements file
            self._update_requirements(app_name)

            return True

        except Exception as e:
            logger.error(f"Error installing package: {e}")
            return False

    def get_environment_info(self, app_name: str) -> Dict:
        """
        Get information about an environment.

        Args:
            app_name: Name of the application

        Returns:
            Dictionary with environment information
        """
        env_path = self.environments_dir / app_name

        if not env_path.exists():
            return {"exists": False}

        info = {
            "exists": True,
            "path": str(env_path),
            "python_executable": str(self._get_python_executable(app_name)),
            "packages": [],
        }

        # Load environment info if available
        info_file = env_path / "env_info.json"
        if info_file.exists():
            with open(info_file, "r") as f:
                env_info = json.load(f)
                info.update(env_info)

        # Get installed packages using UV
        try:
            python_exe = self._get_python_executable(app_name)
            cmd = ["uv", "pip", "list", "--python", str(python_exe), "--format=json"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                info["packages"] = json.loads(result.stdout)
        except Exception as e:
            logger.warning(f"Could not get package list: {e}")

        return info

    def check_environment_health(self, app_name: str) -> Tuple[bool, str]:
        """
        Check if an environment is healthy and ready to use.

        Args:
            app_name: Name of the application

        Returns:
            Tuple of (is_healthy, message)
        """
        env_path = self.environments_dir / app_name

        if not env_path.exists():
            return False, f"Environment {app_name} does not exist"

        python_exe = self._get_python_executable(app_name)

        if not python_exe.exists():
            return False, f"Python executable not found in {app_name}"

        # Test Python execution
        try:
            result = subprocess.run(
                [str(python_exe), "-c", "import sys; print(sys.version)"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return False, f"Python execution failed: {result.stderr}"

            return True, f"Environment {app_name} is healthy"

        except subprocess.TimeoutExpired:
            return False, f"Python execution timed out"
        except Exception as e:
            return False, f"Error checking environment: {e}"

    def list_environments(self) -> List[Dict]:
        """
        List all available environments.

        Returns:
            List of environment information dictionaries
        """
        environments = []

        if not self.environments_dir.exists():
            return environments

        for env_dir in self.environments_dir.iterdir():
            if env_dir.is_dir():
                info = self.get_environment_info(env_dir.name)
                if info["exists"]:
                    environments.append({"name": env_dir.name, **info})

        return environments

    def remove_environment(self, app_name: str) -> bool:
        """
        Remove an environment.

        Args:
            app_name: Name of the application

        Returns:
            True if successful, False otherwise
        """
        env_path = self.environments_dir / app_name

        if not env_path.exists():
            logger.warning(f"Environment {app_name} does not exist")
            return True

        try:
            import shutil

            shutil.rmtree(env_path)
            try:
                logger.info(f"✓ Removed environment {app_name}")
            except UnicodeEncodeError:
                logger.info(f"Successfully removed environment {app_name}")
            return True
        except Exception as e:
            logger.error(f"Error removing environment: {e}")
            return False

    def _get_python_executable(self, app_name: str) -> Path:
        """Get the Python executable path for an environment."""
        env_path = self.environments_dir / app_name

        if os.name == "nt":  # Windows
            return env_path / "Scripts" / "python.exe"
        else:  # Unix-like
            return env_path / "bin" / "python"

    def _update_requirements(self, app_name: str):
        """Update the requirements file for an environment."""
        try:
            python_exe = self._get_python_executable(app_name)
            req_file = self.requirements_dir / f"{app_name}.txt"

            # Use uv pip freeze to get current packages
            cmd = ["uv", "pip", "freeze", "--python", str(python_exe)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                with open(req_file, "w") as f:
                    f.write(result.stdout)
                logger.debug(f"Updated requirements for {app_name}")
        except Exception as e:
            logger.warning(f"Could not update requirements: {e}")


if __name__ == "__main__":
    # Test the environment manager
    import sys

    manager = EnvironmentManager(Path(__file__).parent.parent)

    # Create test environment
    if manager.create_environment("test-env", "3.10"):
        try:
            print("✓ Created test environment")
        except UnicodeEncodeError:
            print("Successfully created test environment")

        # Check health
        healthy, msg = manager.check_environment_health("test-env")
        print(f"Health check: {msg}")

        # List environments
        envs = manager.list_environments()
        print(f"\nFound {len(envs)} environments:")
        for env in envs:
            print(f"  - {env['name']} (Python {env.get('python_version', 'unknown')})")
