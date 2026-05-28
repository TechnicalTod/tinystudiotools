# TinyStudioLauncher

A small desktop launcher for TinyStudio: pick a DCC, version, and show, then start Maya or Unreal with isolated Python environments managed by [uv](https://docs.astral.sh/uv/).

---

## Prerequisites

Before you start, install or verify the following on **Windows 10 or newer**:

| Requirement                | Notes                                                                                          |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| **Python 3.10+**           | Same major.minor as the per-app UV envs (see `setup_environments.py`). 3.10 is a safe default. |
| **Internet**               | For `pip` and the first `uv` sync of each environment.                                         |
| **Autodesk Maya / Unreal** | Install the versions you reference in `configs/*.json` if you intend to launch them.           |

You will use **two** Python contexts:

1. **Host Python** — the interpreter where you run `launcher.py`, `setup_environments.py`, and PyInstaller. Install `requirements.txt` here.
2. **Per-DCC UV environments** — created under `environments/` by `setup_environments.py` (for example `maya-2026`, `unreal-5.6`).

---

## Part A — Step-by-step setup (from source)

Do these steps **in order** from the `TinyStudioLauncher` folder (the directory that contains `launcher.py`).

### Step 1 — Open a terminal in the project folder

```powershell
cd L:\TinyStudioTools\GenTools\TinyStudioLauncher
```

Use your real path if it differs.

### Step 2 — (Optional) Create a dedicated host virtual environment

Recommended so the launcher’s dependencies do not mix with your system site-packages.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install host dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs the UI stack (PySide6), tooling (`uv`, `psutil`, `watchdog`, …), and optional dev packages. Confirm `uv` is on your PATH:

```powershell
uv --version
```

### Step 4 — Create and sync the DCC UV environments

```powershell
python setup_environments.py
```

This script:

- Creates folders under `environments/` (for example `environments\maya-2026`).
- Runs `uv venv` with the Python versions defined in the script.
- Runs `uv pip sync` against `requirements\maya-2026.txt`, `requirements\unreal-5.6.txt`, etc.

If an environment already exists, the script asks whether to recreate it. Answer `y` only if you want a clean reinstall.

**Requirement:** the `uv` CLI must be available (provided by Step 3). If `uv` is missing, install it from the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) and retry.

### Step 5 — Point the launcher at your studio layout

1. **JSON configs** — Edit files in `configs\` (for example `maya_2026.json`, `unreal_5.6.json`): `executable_path`, `repository`, `env_vars`, and paths should match your machines. See `configs\template.json.example` if you add a new app.
2. **Base TinyStudio paths** — In `src\launch_controller.py`, the dictionary `base_paths` (around `TINYSTUDIO_BASE_SHOW_DIR`, `TINYSTUDIO_LIB_DIR`, `SCRIPT_DIR`) defaults to studio-specific roots. Change these to match your drives and repo layout before relying on launches.

### Step 6 — Run the launcher from source

```powershell
python launcher.py
```

With no arguments, the UI opens. Logs are also written to `%USERPROFILE%\TinyStudioLauncher.log`.

**Command-line launch** (no UI):

```powershell
python launcher.py --app maya --version 2026 --show 1000_TinyStudioTestShow
python launcher.py --app unreal --version 5.6 --show 1000_TinyStudioTestShow
```

Use `--fast` for Maya fast-start tweaks (see `launcher.py`).

---

## Part B — Build or rebuild the PyInstaller executable

The repo includes `TinyStudioLauncher.spec` (PySide2/shiboken2 excluded, `hiddenimports` for `src.log_setup`). That matches the **one-folder** layout under `dist\TinyStudioLauncher\`. Use the **same host Python** (and venv, if you use one) as in Part A whenever you build or rebuild.

**Before rebuilding:** quit `TinyStudioLauncher.exe` and close any Explorer window opened inside `dist\TinyStudioLauncher` so PyInstaller can delete the old output (otherwise you may see `PermissionError` / `Access is denied`).

### Rebuilding the exe (quick reference)

Run this whenever you change **launcher code**, anything under `src\`, or bundled `configs` / `resources`. PyInstaller **copies** those at build time; the exe does not pick up edits to the source tree afterward.

1. Activate the same environment you used for development (for example `.\.venv\Scripts\Activate.ps1`).
2. `cd` to the `TinyStudioLauncher` folder (where `launcher.py` and the `.spec` live).
3. Run the build command in Step 2. `--clean` clears PyInstaller’s cache so the next build is not polluted by stale hooks.
4. If you ship `environments\` with the app, copy that folder into `dist\TinyStudioLauncher\` again after a rebuild (Step 3), unless nothing changed there.
5. Smoke-test from `dist\TinyStudioLauncher\` (Step 4).

### Step 1 — Install PyInstaller in the same host environment as Part A

One-time (or after recreating the venv):

```powershell
pip install pyinstaller
```

### Step 2 — Build or rebuild from the `TinyStudioLauncher` directory

**Preferred — use the spec** (includes `hiddenimports`, excludes conflicting Qt bindings):

```powershell
python -m PyInstaller --noconfirm --clean TinyStudioLauncher.spec
```

**Alternative — one-shot CLI** (if you are not using the spec):

```powershell
python -m PyInstaller --noconfirm --clean --name TinyStudioLauncher --windowed --onedir `
  --icon "resources\icons\TinyStudioLauncher.ico" `
  --add-data "configs;configs" `
  --add-data "resources;resources" `
  --hidden-import src.log_setup `
  --exclude-module PySide2 `
  --exclude-module shiboken2 `
  launcher.py
```

- Use `python -m PyInstaller` if the `pyinstaller` command is not on your PATH.
- **Application icon:** PyInstaller embeds a Windows `.ico` into the exe, not a PNG. The spec uses `resources\icons\TinyStudioLauncher.ico`, built from `TinyStudioIcon.png` (multi-resolution). After changing the mark, regenerate that `.ico` with any tool that exports multi-size ICO, or with Pillow by opening `TinyStudioIcon.png` and saving as ICO with sizes 16 through 256 px.
- Omit `--windowed` in the spec or switch the spec to `console=True` if you want a console for tracebacks.
- If the app fails at runtime with missing Qt plugins or DLLs, add `--collect-all PySide6` to the CLI variant (larger output).

**Output layout (PyInstaller 6+ onedir):** `TinyStudioLauncher.exe` sits in `dist\TinyStudioLauncher\`; `configs`, `resources`, and `src` are typically under `dist\TinyStudioLauncher\_internal\`. The launcher resolves that layout automatically.

### Step 3 — Add UV environments to the distributable

`PyInstaller` does **not** bundle `environments\` automatically. For a machine that only receives the `dist` folder:

- **Option A:** Copy the entire `environments` directory from your dev tree into `dist\TinyStudioLauncher\` beside the exe (after build), **or**
- **Option B:** On the target PC, install Python + `uv`, copy the project (or at least `setup_environments.py`, `src\`, `requirements\`), and run `python setup_environments.py` once so `environments\` is created next to the launcher.

Without a valid environment for the chosen app/version, launch will fail until one of these is done.

### Step 4 — Smoke-test the build

```powershell
cd dist\TinyStudioLauncher
.\TinyStudioLauncher.exe
```

---

## Adding new applications

The UI loads one entry per `configs\*.json` file. `launch_controller` resolves the **UV environment name** as `{app}-{version}` (lowercase app key, hyphen, version string). That same name must exist as `requirements\{app}-{version}.txt` and as a folder under `environments\` after setup.

### Naming checklist

| Piece                      | Rule                                                                                  | Example                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Config file                | Stem is `app_version` with **exactly one** underscore (split into app key + version). | `houdini_20.json` → app `houdini`, version `20`                          |
| UV env / requirements file | `app-version` (hyphen).                                                               | `houdini-20` → `requirements\houdini-20.txt`, `environments\houdini-20\` |
| `setup_environments.py`    | First column of each tuple must match that env name.                                  | `("houdini-20", "3.10", "Houdini 20")`                                   |

Steps:

1. **Add a config** — Copy `configs\template.json.example` to `configs\<app>_<version>.json` and edit `name`, `repository`, `python_version`, `executable_path`, `env_vars`, `script_paths`, `additional_paths`, and `icon` for your DCC.
2. **Add an icon** — Put a PNG in `resources\icons\`. The UI prefers `resources\icons\<app>Icon.png` (case-insensitive prefix + `Icon.png`); otherwise it uses `resources\icons\<app>.png`.
3. **Add a requirements file** — Create `requirements\<app>-<version>.txt` (same hyphenated name as the UV env). List packages your tools need; `uv pip sync` installs **exactly** what is listed (see below).
4. **Register the environment** — Append a row to the `environments` list in `setup_environments.py`: `(env_name, python_minor_string, display_name)`. Use the same Python minor series the DCC ships with when possible.
5. **Create / sync** — Run `python setup_environments.py` and allow create + sync for the new row. Alternatively, the launcher can **auto-create** a missing env on first launch if `uv` is available and `python_version` is set in the JSON, but running the setup script once keeps behavior predictable.

For more fields (`executable_type`, `project_pattern`, show filters, troubleshooting), see `docs\adding-applications.md`.

---

## Adding or changing Python requirements

Per-DCC packages live in `requirements\<env-name>.txt` (for example `requirements\maya-2026.txt`). The launcher uses **`uv pip sync`**, which makes the environment match that file: versions are pinned, and packages not listed are removed when you sync again.

### Update an existing environment after editing the `.txt`

From the `TinyStudioLauncher` folder, either:

- Run `python setup_environments.py` and recreate or let it sync the env, **or**
- Sync manually (Windows paths):

```powershell
uv pip sync --python .\environments\maya-2026\Scripts\python.exe .\requirements\maya-2026.txt
```

Replace `maya-2026` with the env name you use in `setup_environments.py` and in `launch_controller` (`{app}-{version}`).

### One-off installs (not persisted until you edit the file)

```powershell
uv pip install --python .\environments\maya-2026\Scripts\python.exe some-package
```

Add the same package (with a version pin) to the matching `requirements\*.txt` if you want the next `uv pip sync` or `setup_environments.py` run to keep it.

### New requirement file for a new app

Create `requirements\<app>-<version>.txt`, register the env in `setup_environments.py`, then run `python setup_environments.py` (or use `EnvironmentManager.create_environment` + `sync_environment` from Python as in `docs\adding-applications.md`).

---

## Reference

### Features

- Qt UI for choosing app, version, and show.
- Per-app UV virtualenvs and `uv pip sync` from `requirements\*.txt`.
- JSON-driven configs and non-blocking process launch.
- Optional CLI launch without opening the UI.

### Directory layout

| Path            | Role                                                           |
| --------------- | -------------------------------------------------------------- |
| `configs\`      | One JSON file per app/version (see `template.json.example`).   |
| `environments\` | UV-created venvs (gitignored by default).                      |
| `requirements\` | Per-env requirement lists consumed by `setup_environments.py`. |
| `resources\`    | Icons, `styles\dark.qss`, etc.                                 |
| `src\`          | `environment_manager`, `launch_controller`, `ui\`.             |

### Maya `MAYA_APP_DIR` note

In Maya configs, `MAYA_APP_DIR` should be the **parent** preferences folder (no version suffix). Maya creates `2026`, `2023`, etc. underneath automatically.

### More documentation

- `docs\adding-applications.md` — extending supported DCCs.
- `docs\best-practices.md` — pipeline notes.

---

## Implementation summary

1. Load JSON from `configs\`.
2. Merge environment variables from config and `launch_controller` base paths.
3. Ensure optional paths exist where the launcher creates them.
4. Start the DCC process without blocking the UI thread.
