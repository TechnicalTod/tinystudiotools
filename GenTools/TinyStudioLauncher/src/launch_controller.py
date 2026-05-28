"""
Launch Controller for TinyStudioLauncher

Handles application launching with proper environment isolation.
"""

import json
import logging
import os
import subprocess
import sys
import getpass
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

import psutil

from .log_setup import get_module_logger
from .show_config import (
    DEFAULT_BASE_SHOW_DIR,
    ShowVersionMismatchError,
    load_show_config,
)

logger = get_module_logger(__name__)


@dataclass
class LaunchConfig:
    """Configuration for launching an application"""

    app_name: str
    version: str
    show: str
    executable_path: str
    environment_path: str
    env_vars: Dict[str, str]
    python_paths: List[str]
    script_paths: List[str]


class LaunchController:
    """Controls the launching of applications with proper environment setup"""

    def __init__(self, config_dir: Path, env_manager):
        """
        Initialize the launch controller.

        Args:
            config_dir: Directory containing application configs
            env_manager: EnvironmentManager instance
        """
        self.config_dir = Path(config_dir)
        self.env_manager = env_manager
        self.active_processes = {}
        self.base_show_dir = DEFAULT_BASE_SHOW_DIR

        logger.info(f"LaunchController initialized with configs from {self.config_dir}")

    def get_show_config(self, show: str):
        """Load per-show config from {base_show_dir}{show}/config/show_config.json."""
        return load_show_config(show, self.base_show_dir)

    def validate_show_version(self, app_name: str, version: str, show: str) -> None:
        """
        Ensure the requested version matches the show's pinned version, if any.

        Raises:
            ShowVersionMismatchError: when the show config pins a different version.
        """
        show_config = self.get_show_config(show)
        if show_config is not None:
            show_config.validate_version(app_name, version, show)

    def load_config(self, app_name: str, version: str = "") -> Dict:
        """
        Load configuration for an application/version.

        Args:
            app_name: Application name (e.g., "maya", "unreal")
            version: Version string (e.g., "2026", "5.6")

        Returns:
            Configuration dictionary
        """
        # Build config filename
        if version:
            config_file = self.config_dir / f"{app_name}_{version}.json"
        else:
            config_file = self.config_dir / f"{app_name}.json"

        if not config_file.exists():
            # Try to find any matching config
            pattern = f"{app_name}*.json"
            configs = list(self.config_dir.glob(pattern))
            if configs:
                config_file = configs[0]
                logger.warning(f"Using {config_file.name} for {app_name}")
            else:
                raise FileNotFoundError(f"Configuration not found for {app_name}")

        with open(config_file, "r") as f:
            config = json.load(f)

        logger.debug(f"Loaded config from {config_file}")
        return config

    def prepare_launch_config(self, app_name: str, version: str, show: str) -> LaunchConfig:
        """
        Prepare launch configuration with all necessary paths and variables.

        Args:
            app_name: Application name
            version: Version string
            show: Show name

        Returns:
            LaunchConfig object ready for launching
        """
        self.validate_show_version(app_name, version, show)

        # Load application config
        config = self.load_config(app_name, version)

        # Build environment name
        if version:
            env_name = f"{app_name}-{version}"
        else:
            env_name = app_name

        # Get environment info
        env_info = self.env_manager.get_environment_info(env_name)

        if not env_info["exists"]:
            python_version = config.get("python_version")
            if not python_version:
                raise RuntimeError(f"Environment not found for {env_name}")

            logger.warning(
                f"Environment not found for {env_name}. Creating with Python {python_version}..."
            )
            created = self.env_manager.create_environment(env_name, python_version)
            if not created:
                raise RuntimeError(f"Environment not found for {env_name}")

            # Best-effort dependency sync; launcher can still run if requirements are empty.
            self.env_manager.sync_environment(env_name)

            env_info = self.env_manager.get_environment_info(env_name)
            if not env_info["exists"]:
                raise RuntimeError(f"Environment not found for {env_name}")

        # Build base environment variables
        env_vars = os.environ.copy()

        # Clear any existing Python paths
        env_vars.pop("PYTHONPATH", None)
        env_vars.pop("MAYA_SCRIPT_PATH", None)

        # Set base paths
        base_paths = {
            "TINYSTUDIO_BASE_SHOW_DIR": self.base_show_dir,
            "TINYSTUDIO_LIB_DIR": "L:/",
            "SCRIPT_DIR": "L:/TinyStudioTools/",
            "SHOW_NAME": show,
            "CURRENT_SHOW": show,
            "version": version,
            "USERNAME": getpass.getuser(),  # Add current username
        }
        env_vars.update(base_paths)

        # Debug log for base paths
        logger.debug(f"Base paths set:")
        for key, value in base_paths.items():
            logger.debug(f"  {key}: {value}")

        # Build repository paths
        repo_name = config["repository"]
        if version and app_name == "maya":
            # Maya uses version in repository path
            repo_base = Path(base_paths["SCRIPT_DIR"]) / repo_name / version
        else:
            repo_base = Path(base_paths["SCRIPT_DIR"]) / repo_name

        # Add repository base to env vars
        env_vars[f"{app_name.upper()}_REPO"] = str(repo_base)

        # Collect Python paths
        python_paths = []

        # For Maya, add Maya's built-in Python paths first
        if app_name.lower() == "maya":
            maya_location = f"C:/Program Files/Autodesk/Maya{version}"
            if os.path.exists(maya_location):
                # Add Maya's Python paths
                maya_python_paths = [
                    f"{maya_location}/Python/Lib/site-packages",
                    f"{maya_location}/Python/Lib",
                    f"{maya_location}/Python",
                    f"{maya_location}/devkit/other/pymel/extras/completion/py",
                ]

                for path in maya_python_paths:
                    if os.path.exists(path):
                        python_paths.append(path)
                        logger.debug(f"Added Maya Python path: {path}")

        # Add base script paths from repository
        for script_path in config.get("script_paths", []):
            full_path = repo_base / script_path
            if full_path.exists():
                python_paths.append(str(full_path))

        # Add show-specific paths if they exist
        show_scripts = Path(base_paths["TINYSTUDIO_BASE_SHOW_DIR"]) / show / "scripts" / app_name
        if show_scripts.exists():
            python_paths.insert(0, str(show_scripts))

        # Add additional paths from config
        for path_template in config.get("additional_paths", []):
            # Replace variables in path template
            path = path_template
            for key, value in env_vars.items():
                path = path.replace(f"{{{key}}}", str(value))
            python_paths.append(path)

        # Add environment site-packages to PYTHONPATH
        # This is critical for accessing installed packages like numpy
        site_packages_path = Path(env_info["path"]) / "Lib" / "site-packages"
        if site_packages_path.exists():
            python_paths.append(str(site_packages_path))
            logger.debug(f"Added site-packages to PYTHONPATH: {site_packages_path}")

        # Set Python path
        env_vars["PYTHONPATH"] = os.pathsep.join(python_paths)

        if app_name.lower() == "ae":
            launcher_base = Path(self.env_manager.base_path)
            launcher_dir = str(launcher_base).replace("\\", "/")
            if not launcher_dir.endswith("/"):
                launcher_dir += "/"
            env_vars["TINYSTUDIO_LAUNCHER_DIR"] = launcher_dir
            ae_python = Path(env_info["path"]) / "Scripts" / "pythonw.exe"
            env_vars["TINYSTUDIO_AE_PYTHON"] = str(ae_python).replace("\\", "/")

        # Add custom environment variables from config
        for key, value_template in config.get("env_vars", {}).items():
            # Replace variables in template
            value = value_template

            # Debug log for MAYA_APP_DIR before replacement
            if key == "MAYA_APP_DIR":
                logger.debug(f"MAYA_APP_DIR template before replacement: {value_template}")

            for var_key, var_value in env_vars.items():
                value = value.replace(f"{{{var_key}}}", str(var_value))

                # Debug log for each replacement in MAYA_APP_DIR
                if key == "MAYA_APP_DIR" and f"{{{var_key}}}" in value_template:
                    logger.debug(f"  Replacing {{{var_key}}} with '{var_value}'")

            env_vars[key] = value

            # Debug log for MAYA_APP_DIR after replacement
            if key == "MAYA_APP_DIR":
                logger.debug(f"MAYA_APP_DIR after replacement: {value}")

        # For Maya, ensure MAYA_SCRIPT_PATH includes the PYTHONPATH
        # This is necessary for Maya to find the Python modules
        if app_name.lower() == "maya":
            if "MAYA_SCRIPT_PATH" not in env_vars:
                env_vars["MAYA_SCRIPT_PATH"] = env_vars["PYTHONPATH"]
            logger.debug(f"MAYA_SCRIPT_PATH: {env_vars['MAYA_SCRIPT_PATH']}")

        # Do not mkdir show or project paths — show layout is provisioned on the share.

        # Determine executable path
        if config.get("executable_type") == "project":
            # Project-based executable (like Unreal)
            executable_template = config.get("project_pattern", "")
            executable_path = executable_template
            for key, value in env_vars.items():
                executable_path = executable_path.replace(f"{{{key}}}", str(value))
        else:
            # Standard executable
            executable_template = config.get("executable_path", "")
            executable_path = executable_template
            for key, value in env_vars.items():
                executable_path = executable_path.replace(f"{{{key}}}", str(value))

        # Create launch config
        launch_config = LaunchConfig(
            app_name=app_name,
            version=version,
            show=show,
            executable_path=executable_path,
            environment_path=env_info["path"],
            env_vars=env_vars,
            python_paths=python_paths,
            script_paths=config.get("script_paths", []),
        )

        return launch_config

    def launch_application(self, launch_config: LaunchConfig) -> subprocess.Popen:
        """
        Launch an application with the prepared configuration.

        Args:
            launch_config: Prepared launch configuration

        Returns:
            Popen process object
        """
        # Verify executable exists
        if not Path(launch_config.executable_path).exists():
            raise FileNotFoundError(f"Executable not found: {launch_config.executable_path}")

        # Activate virtual environment by prepending to PATH
        env_scripts = Path(launch_config.environment_path) / "Scripts"
        launch_config.env_vars["PATH"] = f"{env_scripts};{launch_config.env_vars['PATH']}"
        launch_config.env_vars["VIRTUAL_ENV"] = launch_config.environment_path

        # Log launch information
        logger.info(
            f"Launching {launch_config.app_name} {launch_config.version} for {launch_config.show}"
        )
        logger.debug(f"Executable: {launch_config.executable_path}")
        logger.debug(f"PYTHONPATH: {launch_config.env_vars.get('PYTHONPATH', 'Not set')}")
        logger.debug(f"MAYA_APP_DIR: {launch_config.env_vars.get('MAYA_APP_DIR', 'Not set')}")

        # Launch the application with non-blocking I/O
        # Use DEVNULL instead of PIPE to prevent blocking on stdout/stderr
        process = subprocess.Popen(
            [launch_config.executable_path],
            env=launch_config.env_vars,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )

        # Track the process
        process_key = (
            f"{launch_config.app_name}_{launch_config.version}_{launch_config.show}_{process.pid}"
        )
        self.active_processes[process_key] = {
            "process": process,
            "config": launch_config,
            "pid": process.pid,
        }

        try:
            logger.info(f"✓ Application launched (PID: {process.pid})")
        except UnicodeEncodeError:
            # Fallback to ASCII if UTF-8 encoding fails
            logger.info(f"Successfully launched application (PID: {process.pid})")

        return process

    def get_active_processes(self) -> Dict[str, Dict]:
        """
        Get dictionary of active processes, cleaning up terminated ones.

        Returns:
            Dictionary of active process information
        """
        # Clean up terminated processes
        terminated = []
        for key, info in self.active_processes.items():
            if info["process"].poll() is not None:
                terminated.append(key)
                logger.debug(f"Process {key} has terminated")

        for key in terminated:
            del self.active_processes[key]

        return self.active_processes.copy()

    def terminate_process(self, process_key: str) -> bool:
        """
        Terminate a specific process.

        Args:
            process_key: Key identifying the process

        Returns:
            True if terminated successfully
        """
        if process_key not in self.active_processes:
            logger.warning(f"Process {process_key} not found")
            return False

        try:
            process = self.active_processes[process_key]["process"]
            process.terminate()
            process.wait(timeout=5)
            del self.active_processes[process_key]
            logger.info(f"Terminated process {process_key}")
            return True
        except subprocess.TimeoutExpired:
            # Force kill if terminate doesn't work
            process.kill()
            del self.active_processes[process_key]
            logger.warning(f"Force killed process {process_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to terminate process: {e}")
            return False

    def get_process_info(self, process_key: str) -> Optional[Dict]:
        """
        Get detailed information about a process.

        Args:
            process_key: Key identifying the process

        Returns:
            Process information dictionary or None
        """
        if process_key not in self.active_processes:
            return None

        info = self.active_processes[process_key]
        pid = info["pid"]

        try:
            # Get additional info using psutil
            proc = psutil.Process(pid)
            return {
                "key": process_key,
                "pid": pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "app_name": info["config"].app_name,
                "version": info["config"].version,
                "show": info["config"].show,
            }
        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            logger.warning(f"Could not get process info: {e}")
            return {
                "key": process_key,
                "pid": pid,
                "app_name": info["config"].app_name,
                "version": info["config"].version,
                "show": info["config"].show,
            }


if __name__ == "__main__":
    # Test the launch controller
    import sys

    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from src.environment_manager import EnvironmentManager

    # Initialize components
    base_path = Path(__file__).parent.parent
    env_manager = EnvironmentManager(base_path)
    controller = LaunchController(base_path / "configs", env_manager)

    # Test loading configs
    print("Available configs:")
    for config_file in controller.config_dir.glob("*.json"):
        print(f"  - {config_file.stem}")

    # Test preparing launch config
    try:
        launch_config = controller.prepare_launch_config("maya", "2026", "TEST_SHOW")
        print(f"\nPrepared launch config for Maya 2026:")
        print(f"  Executable: {launch_config.executable_path}")
        print(f"  Environment: {launch_config.environment_path}")
        print(f"  Python paths: {len(launch_config.python_paths)} paths")
    except Exception as e:
        print(f"\nError preparing launch config: {e}")
