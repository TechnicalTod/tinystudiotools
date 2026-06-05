# UnrealRepository

Python tools, startup scripts, and shared assets for TinyStudio Unreal projects. Launch Unreal through **TinyStudioLauncher** so environment variables, `PYTHONPATH`, and the per-engine UV environment are set correctly.

---

## Studio layout

| Path | Role |
| ---- | ---- |
| **L:/TinyStudioTools** | This repository (`UnrealRepository/` lives here) |
| **S:/** | Show drive — published assets, editorial, config (`S:/<show_id>/…`) |
| **L:/Artist/{USERNAME}** | Per-artist settings (including Unreal project mappings) |

See the [root README](../README.md) for full studio prerequisites and Python library notes.

---

## Launch Unreal

Always start the editor from **TinyStudioLauncher** (`GenTools/TinyStudioLauncher/`).

1. Select the show and Unreal version in the launcher UI.
2. On first launch for a show, browse to your local `.uproject` when prompted. The path is saved to `L:\Artist\{USERNAME}\TinyStudioSettings\unreal_projects.json`.
3. To change the project later, right-click the Unreal tile → **Set Unreal project…**

**CLI example:**

```powershell
python launcher.py --app unreal --version 5.6 --show 1000_TinyStudioTestShow
```

The launcher sets `UNREAL_REPO`, `UE_PROJECT_DIR`, `UE_PYTHONPATH`, `TINYSTUDIO_BASE_SHOW_DIR`, and `SHOW_NAME`, then runs `customMenus.py` via `-ExecCmds` (no project `DefaultEngine.ini` changes required). Per-DCC packages live under `GenTools/TinyStudioLauncher/environments/unreal-5.6/`.

---

## Environment variables (launcher)

| Variable | Purpose |
| -------- | ------- |
| `SHOW_NAME` | Active show folder (e.g. `1000_TinyStudioTestShow`) |
| `TINYSTUDIO_BASE_SHOW_DIR` | Show drive root (e.g. `S:/`) |
| `TINYSTUDIO_LIB_DIR` | Studio library root (e.g. `L:/`) |
| `UNREAL_REPO` | Path to this folder (`L:/TinyStudioTools/UnrealRepository`) |
| `UE_PROJECT_DIR` | Local Unreal project directory (from mapping or show template) |
| `UE_PYTHONPATH` | Import paths for UE5’s isolated Python interpreter |
| `UE_ENGINE_DIR` | Installed engine root (from `unreal_*.json`) |

Tools resolve show and studio paths through `shared/unrealFilePaths.py`.

---

## Repository layout

```
UnrealRepository/
├── scripts/
│   ├── startupScripts/     # Previs menu registration
│   ├── assetTools/         # Import/export, USD, SetDec
│   ├── shotTools/          # Sequencer, shot import from Maya
│   ├── levelTools/         # USD scenes, env build, level import
│   ├── genTools/           # Shared utilities
│   └── _Deprecated/        # Retired render / Perforce automation code
└── shared/
    └── unrealFilePaths.py

Qt stylesheets live in `GenTools/pyQtStyleSheets/` (loaded via `genTools.uiUtils`).
```

---

## New show — Unreal project setup

### 1. Create the show skeleton

Run `GenTools/Scripts/ShowSetupScripts/createNewShow.py` to create the show folder tree and `config/show_config.json` on **S:/**.

### 2. Ingest the Unreal project

Add the project to Perforce and map it per artist. The launcher stores each artist’s local `.uproject` path per show.

### 3. Enable the Python Script Plugin

Enable **Edit → Plugins → Python Editor Script Plugin** and **USD Core** (and **USD Importer** if you use layout import/export). No changes to `DefaultEngine.ini` are needed when using TinyStudioLauncher.

If someone opens the `.uproject` directly, run **Tools → Execute Python Script** and pick `UnrealRepository/scripts/startupScripts/customMenus.py`, or add a startup entry to `DefaultEngine.ini`.

### 4. Shared Derived Data Cache (optional)

Point DDC paths to your studio shared cache (e.g. `X:/UnrealCache`).

### 5. Verify

1. Launch through TinyStudioLauncher — no “Executing Python Script…” hang.
2. Confirm the **Previs Menu** appears after the editor finishes loading.
3. Run a test SetDec import or shot import.

---

## Python packages (PySide6, NumPy, …)

UI tools import **PySide6** from the TinyStudioLauncher UV environment. The launcher adds that env’s `site-packages` to `UE_PYTHONPATH` at startup. **Unreal envs must use Python 3.11** to match UE 5.6+ embedded Python (3.10 wheels will fail to import).

After changing `GenTools/TinyStudioLauncher/requirements/unreal-*.txt`, re-sync the matching env:

```powershell
cd L:\TinyStudioTools\GenTools\TinyStudioLauncher
uv pip sync --native-tls --python .\environments\unreal-5.7\Scripts\python.exe .\requirements\unreal-5.7.txt
```

Replace `unreal-5.7` with your engine version. Requirements include `PySide6_Essentials` and `PySide6_Addons` (the `PySide6` meta package alone installs stubs only). If the env does not exist yet, run `python setup_environments.py` first (Unreal envs use **Python 3.11**).

---

## Related docs

- [TinyStudioLauncher](../GenTools/TinyStudioLauncher/README.md) — launcher setup, Unreal project mapping, CLI
- [Root README](../README.md) — studio drives, prerequisite apps, FAQ
- [Maya SetDec export](../MayaRepository/2026/scripts/unrealTools/exportSetDecAssets/README.md) — publishing assets from Maya for Unreal import
