# TinyStudioLauncher

A modern application launcher for Saga Studio that provides isolated environments for DCC applications.

## Features

- Clean, modern UI for launching DCC applications
- Isolated Python environments using UV for dependency management
- Per-application and per-version configuration
- Show-specific script paths and environment variables
- Process monitoring and management
- Non-blocking application launching

## Requirements

- Python 3.9+
- UV package manager
- Windows 10 or newer

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the launcher: `python launcher.py`

## Usage

### UI Mode

Run the launcher without any arguments to open the UI:

```
python launcher.py
```

### Command Line Mode

Launch applications directly from the command line:

```
python launcher.py --app maya --version 2026 --show 001_SHOWTEST
```

Options:

- `--app`: Application name (e.g., maya, unreal)
- `--version`: Application version (e.g., 2023, 2026, 5.6)
- `--show`: Show name
- `--fast`: Enable fast startup mode (reduces startup time)

## Configuration

Application configurations are stored in JSON files in the `configs` directory.

Example configuration:

```json
{
  "name": "Maya 2026",
  "repository": "MayaRepository",
  "python_version": "3.10",
  "executable_path": "C:/Program Files/Autodesk/Maya{version}/bin/maya.exe",
  "icon": "maya.png",
  "additional_paths": ["{MAYA_REPO}/scripts/melScripts"],
  "env_vars": {
    "MAYA_APP_DIR": "C:\\Users\\{USERNAME}\\Documents\\maya",
    "MAYA_PROJECT": "{SAGA_BASE_SHOW_DIR}{SHOW_NAME}/maya/projects",
    "MAYA_MODULE_PATH": "{MAYA_REPO}/modules"
  },
  "script_paths": ["scripts", "shared", "tools"],
  "startup_script": "userSetup.py",
  "supported_shows": "all"
}
```

### Maya Configuration Notes

For Maya, the `MAYA_APP_DIR` should point to the top-level directory (without the version number). Maya will automatically create version-specific subdirectories like `2023` or `2026` within this directory.

Example:

```
MAYA_APP_DIR = "C:\Users\username\Documents\maya"
```

Maya will then create:

```
C:\Users\username\Documents\maya\2023\
C:\Users\username\Documents\maya\2026\
```

## Directory Structure

- `configs/`: Application configuration files
- `environments/`: UV-managed Python environments
- `resources/`: Icons and other resources
- `src/`: Core application code
  - `environment_manager.py`: Manages Python environments
  - `launch_controller.py`: Handles application launching
  - `ui/`: User interface components

## Implementation Details

The launcher uses a clean approach to application launching:

1. Reads configuration from JSON files
2. Sets up environment variables as defined in the config
3. Creates directories for path-based environment variables if they don't exist
4. Launches applications with non-blocking I/O to prevent UI hanging

## Future Improvements

1. Add support for more DCC applications
2. Implement package management UI
3. Add process tracking
4. Create PyInstaller spec for distribution
