# Adding New Applications to TinyStudioLauncher

## Overview

Adding a new application involves three simple steps:

1. Create a configuration file
2. Create a requirements file
3. Set up the environment

## Step-by-Step Guide

### 1. Create Configuration File

Create a new JSON file in `configs/` directory. For example, `houdini.json`:

```json
{
  "name": "Houdini 20",
  "repository": "HoudiniRepository",
  "python_version": "3.10",
  "executable_path": "C:/Program Files/Side Effects Software/Houdini {version}/bin/houdinifx.exe",
  "icon": "houdini.png",
  "additional_paths": ["{HOUDINI_REPO}/scripts/python", "{HOUDINI_REPO}/otls"],
  "env_vars": {
    "HOUDINI_PATH": "{HOUDINI_REPO};{TINYSTUDIO_BASE_SHOW_DIR}{SHOW_NAME}/houdini;&",
    "HOUDINI_OTLSCAN_PATH": "{HOUDINI_REPO}/otls;@/otls",
    "HOUDINI_SCRIPT_PATH": "{PYTHONPATH}",
    "HOUDINI_PYTHON_VERSION": "3.10"
  },
  "script_paths": ["scripts", "shared", "tools"],
  "supported_shows": "all"
}
```

### 2. Create Requirements File

Create a requirements file in `requirements/` directory. For example, `requirements/houdini.txt`:

```txt
# Houdini Python Requirements
# Python 3.10 compatible packages

# Add any Python packages your Houdini tools need
numpy==1.26.4
```

### 3. Update Setup Script

Edit `setup_environments.py` to include your new application:

```python
environments = [
    ("maya-2023", "3.9", "Maya 2023"),
    ("maya-2026", "3.10", "Maya 2026"),
    ("unreal", "3.10", "Unreal Engine"),
    ("houdini", "3.10", "Houdini 20"),  # Add this line
]
```

### 4. Create the Environment

Run the setup for just the new application:

```bash
python -c "from src.environment_manager import EnvironmentManager; em = EnvironmentManager('.'); em.create_environment('houdini', '3.10'); em.sync_environment('houdini')"
```

Or re-run the full setup:

```bash
python setup_environments.py
```

## Configuration File Reference

### Required Fields

- `name`: Display name for the application
- `repository`: Folder name under the studio repo root (e.g., "MayaRepository"), relative to `SCRIPT_DIR`
- `python_version`: Python version to use (e.g., "3.9", "3.10")
- `icon`: Icon filename in resources/icons/

### Executable Configuration

For standard applications:

```json
"executable_path": "C:/Program Files/AppName/app.exe"
```

For project-based applications (like Unreal):

```json
"executable_type": "project",
"project_pattern": "{TINYSTUDIO_BASE_SHOW_DIR}{SHOW_NAME}/path/to/project.ext"
```

### Environment Variables

Use template variables that will be replaced at launch:

- `{SHOW_NAME}` - Selected show name
- `{CURRENT_SHOW}` - Same as SHOW_NAME
- `{TINYSTUDIO_BASE_SHOW_DIR}` - S:/
- `{TINYSTUDIO_LIB_DIR}` - L:/
- `{SCRIPT_DIR}` - L:/TinyStudioTools/
- `{PYTHONPATH}` - Constructed Python path
- `{version}` - Application version
- Any custom variables defined in env_vars

### Path Management

- `additional_paths`: Extra paths to add to PYTHONPATH
- `script_paths`: Subdirectories in the repository to include

## Examples

### Nuke Configuration

```json
{
  "name": "Nuke 14",
  "repository": "NukeRepository",
  "python_version": "3.10",
  "executable_path": "C:/Program Files/Nuke14.0v1/Nuke14.0.exe",
  "icon": "nuke.png",
  "additional_paths": ["{NUKE_REPO}/gizmos", "{NUKE_REPO}/python"],
  "env_vars": {
    "NUKE_PATH": "{NUKE_REPO};{TINYSTUDIO_BASE_SHOW_DIR}{SHOW_NAME}/nuke",
    "PYTHONPATH": "{PYTHONPATH}",
    "NUKE_INTERACTIVE": "1"
  },
  "script_paths": ["scripts", "shared", "tools"],
  "startup_script": "init.py",
  "supported_shows": "all"
}
```

### After Effects Configuration

Launcher config lives in `configs/ae_<version>.json` (for example [`ae_2024.json`](../configs/ae_2024.json)). After Effects does **not** load ExtendScript from `PYTHONPATH`; `additional_paths` only affects Python if you add Python-side tooling later. The **TinyStudio** UI is a **ScriptUI Panel** plus a JSON manifest under **AERepository**.

**One-time install (Windows):** from `AERepository/install/`, run:

```powershell
.\install_tinystudio_ae_panel.ps1
# or for another installed year:
.\install_tinystudio_ae_panel.ps1 -AeYear 2025
```

That symlinks (or copies) `scripts/ScriptUI Panels/TinyStudioTools.jsx` into `%AppData%\Adobe\After Effects\<24.0 etc>\Scripts\ScriptUI Panels\`. Restart After Effects, then use **Window → TinyStudioTools.jsx**. For tools that touch disk or the network, enable **Edit → Preferences → Scripting & Expressions → Allow Scripts to Write Files and Access Network**.

On **Windows**, use the launcher menu **Install → After Effects scripts panel…**, then click **Install After Effects scripts panel** in the dialog (pick the AE version year if you have several configs). You can still run `install_tinystudio_ae_panel.ps1` manually from `AERepository/install/` if you prefer.

**Runtime:** launch AE from TinyStudioLauncher so **`AE_REPO`** points at `AERepository`. The panel reads **`AE_MANIFEST`** if set (default in config: `{AE_REPO}/config/tinystudio_ae_tools.json`), loads the tool list, and runs each tool file via **`$.evalFile`** (tools define **`tinystudioRun()`**).

Example shape (match your real `configs/ae_2024.json`):

```json
{
  "name": "After Effects 2024",
  "repository": "AERepository",
  "python_version": "3.10",
  "executable_path": "C:/Program Files/Adobe/Adobe After Effects {version}/Support Files/AfterFX.exe",
  "icon": "aeIcon.png",
  "additional_paths": ["{AE_REPO}/scripts", "{AE_REPO}/tools"],
  "env_vars": {
    "AE_PROJECT_DIR": "{TINYSTUDIO_BASE_SHOW_DIR}{SHOW_NAME}/ae/projects",
    "AE_SCRIPTS_DIR": "{AE_REPO}/scripts",
    "AE_MANIFEST": "{AE_REPO}/config/tinystudio_ae_tools.json"
  },
  "script_paths": ["scripts", "tools"],
  "supported_shows": "all"
}
```

## Testing Your New Application

After adding the application:

1. **Check environment health**:

   ```python
   python -c "from src.environment_manager import EnvironmentManager; em = EnvironmentManager('.'); healthy, msg = em.check_environment_health('houdini'); print(msg)"
   ```

2. **List installed packages**:

   ```bash
   uv pip list --python environments/houdini/Scripts/python.exe
   ```

3. **Install additional packages**:
   ```bash
   uv pip install --python environments/houdini/Scripts/python.exe package-name
   ```

## Tips

1. **Python Version**: Check what Python version your application uses internally
2. **Icon Files**: Copy icon files to `resources/icons/` (PNG format, ~128x128px)
3. **Repository Structure**: Follow the same structure as Maya/Unreal repositories
4. **Testing**: Test the configuration before adding to the UI
5. **Show-Specific**: Use `"supported_shows": ["show1", "show2"]` to limit availability

## Troubleshooting

### Environment Creation Fails

- Check Python version is available
- Verify UV is installed: `uv --version`
- Check disk space

### Package Installation Issues

- Check network connectivity
- Verify package compatibility with Python version
- Use `--index-url` for custom package indexes

### Application Won't Launch

- Verify executable path is correct
- Check all required environment variables
- Test launching manually with the environment activated
