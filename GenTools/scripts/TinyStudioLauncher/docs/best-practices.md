# TinyStudioLauncher: Best Practices

## Environment Configuration Best Practices

### Maya Environment Variables

#### MAYA_APP_DIR

**Recommendation:** Use local directories for `MAYA_APP_DIR`

```json
{
  "env_vars": {
    "MAYA_APP_DIR": "C:\\Users\\{USERNAME}\\Documents\\maya\\{version}"
  }
}
```

**Rationale:**

- Maya writes frequently to this directory (preferences, shelves, etc.)
- Network locations cause performance issues due to frequent writes
- Multiple users can't safely write to the same network location
- Different Maya versions need separate preference directories

**Benefits:**

- Faster Maya startup and operation
- No permission issues with user preferences
- No conflicts between Maya versions
- Multiple instances can run simultaneously

#### Project Data

**Recommendation:** Use network locations for project data

```json
{
  "env_vars": {
    "MAYA_PROJECT": "{SAGA_BASE_SHOW_DIR}{SHOW_NAME}/maya/projects"
  }
}
```

**Rationale:**

- Project data needs to be accessible to all team members
- Assets and scenes are shared resources
- Change tracking and backup is centralized
- Collaboration requires shared storage

### Path Configuration

#### Windows Path Format

When configuring paths in JSON files, use double backslashes for Windows paths:

```json
"MAYA_APP_DIR": "C:\\Users\\{USERNAME}\\Documents\\maya\\{version}"
```

#### Variable Substitution

TinyStudioLauncher supports variable substitution in paths with the format `{VARIABLE_NAME}`:

| Variable      | Description              |
| ------------- | ------------------------ |
| `{USERNAME}`  | Current Windows username |
| `{version}`   | Application version      |
| `{SHOW_NAME}` | Selected show name       |

### Environment Isolation

#### Package Management

- Each application version gets its own Python environment
- Package requirements are stored in `requirements/app_version.txt`
- Use UV for fast package installation: `python -m src.environment_manager install maya-2023 "numpy==1.26.4"`

#### Launch Isolation

TinyStudioLauncher ensures full environment isolation by:

1. Clearing existing environment variables (PYTHONPATH, etc.)
2. Creating fresh path lists for each launch
3. Using dedicated Python environments per application
4. Testing write access to crucial directories before launch

## Known Issues and Workarounds

### Maya PYTHONPATH Handling

Maya adds its own paths to PYTHONPATH at startup. To ensure these don't conflict:

1. Clear PYTHONPATH before launch
2. Set minimal PYTHONPATH with only required paths
3. Let Maya append its own paths at runtime

### Environment Variable Conflicts

If multiple DCCs need to share environments, use specific prefixes:

```json
{
  "env_vars": {
    "MAYA_MODULE_PATH": "path/to/modules",
    "HOUDINI_PATH": "path/to/houdini/modules"
  }
}
```
