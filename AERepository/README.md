# AERepository

TinyStudio **After Effects** tooling: a small **ScriptUI** shell plus **ExtendScript** (`.jsx`) tools, wired to the rest of the studio via **TinyStudioLauncher** and environment variables.

## What you get

- **Window → TinyStudioTools.jsx** — palette that reads a JSON manifest and runs registered tools.
- **Per-tool scripts** under `tools/` — each tool is its own `.jsx` file.
- **Windows installer** — links or copies the panel into Adobe’s ScriptUI Panels folder (AE does not load panels from arbitrary repo paths).

## Requirements

- **After Effects** (paths in the installer assume a normal Windows `%AppData%` layout).
- Launch AE from **TinyStudioLauncher** (recommended) so **`AE_REPO`** points at this repository, or set `AE_REPO` yourself to the folder that contains `config/`, `scripts/`, and `tools/`.
- For tools that read/write files or use the network: **Edit → Preferences → Scripting & Expressions → Allow Scripts to Write Files and Access Network**.

## Repository layout

| Path | Purpose |
|------|---------|
| `config/tinystudio_ae_tools.json` | Tool registry (labels, script paths, enabled flags). |
| `scripts/ScriptUI Panels/TinyStudioTools.jsx` | Panel UI: loads manifest, dropdown + Run, `$.evalFile` per tool. |
| `tools/*.jsx` | Individual tools (see contract below). |
| `install/install_tinystudio_ae_panel.ps1` | Installs the panel into Adobe's ScriptUI Panels folder. |

Optional override: set **`AE_MANIFEST`** to a full path if the manifest should not live at `{AE_REPO}/config/tinystudio_ae_tools.json` (TinyStudioLauncher’s `ae_*.json` can set this).

## Installing the panel (Windows)

After Effects only discovers ScriptUI panels under Adobe’s **Scripts** tree, not under `L:\…\AERepository` directly.

**Option A — TinyStudioLauncher (easiest)**  
Menu **Install → After Effects scripts panel…**, pick the AE version year, then **Install After Effects scripts panel**.

**Option B — PowerShell**

```powershell
cd L:\TinyStudioTools\AERepository\install
.\install_tinystudio_ae_panel.ps1
# Match your installed AE year if needed:
.\install_tinystudio_ae_panel.ps1 -AeYear 2025
```

Symlinks need **Developer Mode** or an elevated shell; otherwise the script **copies** the file (re-run after big panel updates if you use copy mode).

Restart After Effects, then open **Window → TinyStudioTools.jsx**.

## Workfile Publisher

The **Workfile Publisher** tool (`tools/WorkfilePublisher.jsx`) matches the Maya workfile publisher UX:

- Reads **show context** from launcher env vars (`SHOW_NAME`, `TINYSTUDIO_BASE_SHOW_DIR`, `USERNAME`) — no in-tool show picker.
- **Left tree**: shot → task (with workfile counts), plus a workfile table and variant field on the right.
- **Publish** saves the active project to `…/work/ae/<task>/<shot>_<task>_<variant>_v###.aep`.
- **Open Selected** / double-click opens an existing workfile from the table.

Launch AE from **TinyStudioLauncher**, open the panel, choose **Workfile Publisher**, and click **Run**. Enable **Allow Scripts to Write Files and Access Network** in AE preferences.

## Adding a tool

1. **Create** `tools/MyTool.jsx` with a global entry point:

   ```javascript
   function tinystudioRun() {
     // your logic
   }
   ```

2. **Register** it in `config/tinystudio_ae_tools.json`:

   ```json
   {
     "id": "my_tool",
     "label": "My Tool",
     "description": "Short description for humans.",
     "script": "tools/MyTool.jsx",
     "enabled": true
   }
   ```

3. Reload the panel (close and reopen from the **Window** menu) so the manifest is read again.

Keep manifest JSON **UTF-8 without BOM** if you edit outside the repo defaults; the panel strips BOM and has a parse fallback, but plain ASCII in strings is the least fragile.

## Launcher integration

TinyStudioLauncher config lives next to the launcher, e.g. `GenTools/TinyStudioLauncher/configs/ae_2024.json`. It sets:

- **`AE_REPO`** — this repo’s root path.
- **`AE_MANIFEST`** — optional explicit path to `tinystudio_ae_tools.json`.
- Other paths such as **`AE_SCRIPTS_DIR`** / show dirs as needed for your pipeline.

See `GenTools/TinyStudioLauncher/docs/adding-applications.md` for the full After Effects section.

## Troubleshooting

| Symptom | Check |
|--------|--------|
| “AE_REPO is not set” | Launch from TinyStudioLauncher or set `AE_REPO` in the system/user environment before starting AE. |
| “Invalid manifest JSON” | Valid JSON, `tools` array present; avoid BOM; restart AE after editing the panel script. |
| Panel missing from **Window** | Re-run the install step; confirm `%AppData%\Adobe\After Effects\<x.x>\Scripts\ScriptUI Panels\TinyStudioTools.jsx` exists. |
| “Tool did not define tinystudioRun()” | Ensure the tool `.jsx` defines `function tinystudioRun() { … }` at top level after `$.evalFile`. |

## Scope

This repo is **ExtendScript / ScriptUI** only. CEP/HTML panels and separate **Python** batch tooling are out of scope here; the launcher may still put repo paths on `PYTHONPATH` for future use.
