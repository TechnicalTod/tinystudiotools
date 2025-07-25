# Suggested Improvements for Current SagaAppLauncher

While we work on implementing TinyStudioLauncher, here are some improvements that could be made to the current launcher to mitigate issues:

## Quick Wins (< 1 day)

### 1. Process Isolation Without UV

Modify the Python launch code to use isolated subprocess environments:

```python
def openMaya(self):
    selectedItem = self.showComboBox.currentText()
    selectedMayaVersion = self.mayaVersionComboBox.currentText()

    if selectedItem and selectedMayaVersion:
        mayaYear = selectedMayaVersion.split()[-1]

        # Create isolated environment variables
        env = os.environ.copy()

        # Clear any existing Python paths
        env.pop('PYTHONPATH', None)
        env.pop('MAYA_SCRIPT_PATH', None)

        # Set fresh paths
        maya_repo = f"L:/SagaTools/MayaRepository/{mayaYear}"
        python_paths = [
            f"{maya_repo}/scripts",
            f"{maya_repo}/shared",
            f"{maya_repo}/tools",
        ]

        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        env['MAYA_SCRIPT_PATH'] = env['PYTHONPATH']
        env['SHOW_NAME'] = selectedItem

        # Launch with isolated environment
        maya_exe = f"C:/Program Files/Autodesk/Maya{mayaYear}/bin/maya.exe"
        subprocess.Popen([maya_exe], env=env)
```

### 2. Better Error Handling

Add try-catch blocks and user-friendly error messages:

```python
def openMaya(self):
    try:
        # ... launch code ...
    except FileNotFoundError:
        self.logToConsole(f"ERROR: Maya {mayaYear} not installed", "ERROR")
    except Exception as e:
        self.logToConsole(f"ERROR: Failed to launch Maya: {str(e)}", "ERROR")
```

### 3. Console Output Improvements

Add color coding to the console:

```python
def logToConsole(self, message, level="INFO"):
    """Add a message to the console output with timestamp and color"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Define colors for different levels
    colors = {
        "INFO": "#ffffff",
        "SUCCESS": "#4ec9b0",
        "WARNING": "#dcdcaa",
        "ERROR": "#f48771"
    }

    color = colors.get(level, "#ffffff")
    formatted_message = f'<span style="color: {color}">[{timestamp}] {message}</span>'

    self.consoleOutput.append(formatted_message)
    self.consoleOutput.verticalScrollBar().setValue(
        self.consoleOutput.verticalScrollBar().maximum()
    )
```

## Medium Improvements (1-3 days)

### 4. Replace Batch Files with Python

Convert batch files to Python for better control:

```python
class MayaLauncher:
    @staticmethod
    def launch(show_name: str, maya_version: str) -> subprocess.Popen:
        """Launch Maya with proper environment setup"""
        env = os.environ.copy()

        # Base paths
        env['SAGA_BASE_SHOW_DIR'] = "S:/"
        env['SAGA_LIB_DIR'] = "L:/"
        env['SCRIPT_DIR'] = "L:/SagaTools/"
        env['MAYA_REPO'] = f"{env['SCRIPT_DIR']}MayaRepository/{maya_version}/"
        env['SHOW_NAME'] = show_name

        # Build Python paths
        python_paths = [
            f"{env['MAYA_REPO']}scripts",
            f"{env['MAYA_REPO']}shared",
            f"{env['MAYA_REPO']}tools",
            f"{env['MAYA_REPO']}scripts/melScripts",
        ]

        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        env['MAYA_SCRIPT_PATH'] = env['PYTHONPATH']
        env['QT_PLUGIN_PATH'] = f"C:/Program Files/Autodesk/Maya{maya_version}/plugins/platforms"

        # Launch Maya
        maya_exe = f"C:/Program Files/Autodesk/Maya{maya_version}/bin/maya.exe"

        if not os.path.exists(maya_exe):
            raise FileNotFoundError(f"Maya executable not found: {maya_exe}")

        return subprocess.Popen([maya_exe], env=env)
```

### 5. Add Status Indicators

Show launch status on buttons:

```python
class SagaLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.active_processes = {}
        # ... existing init code ...

    def updateButtonStatus(self, app_name, status):
        """Update button appearance based on status"""
        button = getattr(self, f"{app_name}Button")

        if status == "launching":
            button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #dcdcaa;
                    background-color: #3d3d3d;
                }
            """)
        elif status == "running":
            button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #4ec9b0;
                    background-color: #2d2d2d;
                }
            """)
        elif status == "error":
            button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #f48771;
                    background-color: #2d2d2d;
                }
            """)
```

### 6. Configuration File Support

Add JSON config loading:

```python
import json

class ConfigManager:
    def __init__(self, config_dir="configs"):
        self.config_dir = config_dir
        self.configs = {}
        self.load_configs()

    def load_configs(self):
        """Load all JSON config files"""
        config_path = Path(self.config_dir)
        if config_path.exists():
            for config_file in config_path.glob("*.json"):
                with open(config_file, 'r') as f:
                    app_name = config_file.stem
                    self.configs[app_name] = json.load(f)

    def get_config(self, app_name, version=None):
        """Get configuration for an application"""
        key = f"{app_name}_{version}" if version else app_name
        return self.configs.get(key, {})
```

## Larger Improvements (3-5 days)

### 7. Basic Environment Isolation

Implement a simple virtual environment system without UV:

```python
class SimpleEnvironmentManager:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.venv_dir = self.base_path / "venvs"

    def create_venv(self, name, python_version):
        """Create a basic virtual environment"""
        venv_path = self.venv_dir / name

        # Find Python executable
        python_exe = self.find_python(python_version)

        # Create venv
        subprocess.run([
            python_exe, "-m", "venv", str(venv_path)
        ])

        return venv_path

    def activate_venv(self, name):
        """Get environment variables for venv activation"""
        venv_path = self.venv_dir / name
        scripts_path = venv_path / "Scripts"

        env = os.environ.copy()
        env["PATH"] = f"{scripts_path};{env['PATH']}"
        env["VIRTUAL_ENV"] = str(venv_path)

        return env
```

### 8. Process Manager

Track and manage launched processes:

```python
class ProcessManager:
    def __init__(self):
        self.processes = {}

    def launch(self, name, command, env=None):
        """Launch and track a process"""
        process = subprocess.Popen(command, env=env)

        key = f"{name}_{process.pid}"
        self.processes[key] = {
            "process": process,
            "name": name,
            "command": command,
            "start_time": datetime.now()
        }

        return key

    def get_running(self):
        """Get list of running processes"""
        running = {}

        for key, info in list(self.processes.items()):
            if info["process"].poll() is None:
                running[key] = info
            else:
                # Clean up terminated
                del self.processes[key]

        return running
```

## Implementation Priority

1. **Immediate** (Do now):

   - Process isolation (#1)
   - Better error handling (#2)
   - Console improvements (#3)

2. **Short term** (Next sprint):

   - Replace batch files (#4)
   - Status indicators (#5)
   - Config file support (#6)

3. **Medium term** (While building TinyStudioLauncher):
   - Basic environment isolation (#7)
   - Process manager (#8)

## Testing Checklist

Before deploying any changes:

- [ ] Test launching Maya 2023 and 2026 simultaneously
- [ ] Verify environment variables are isolated
- [ ] Check error messages are user-friendly
- [ ] Ensure no regression in launch speed
- [ ] Test with different show configurations
- [ ] Verify logging works correctly

## Notes

These improvements will help mitigate current issues while we develop TinyStudioLauncher. However, they are band-aids compared to the full solution. The priority should remain on completing the new launcher for a permanent fix to environment isolation issues.
