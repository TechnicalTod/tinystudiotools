# Workfile Publisher

Cross-DCC workfile publisher for TinyStudio. Maya uses the shared Python/PySide publisher; After Effects uses a native ExtendScript workfile tool in `AERepository/tools/WorkfilePublisher.jsx`.

The active show, show drive, and artist username all come from `TinyStudioLauncher` via environment variables. The publisher never asks "which show?" - if the launcher didn't set one, the tool refuses to start.

---

## Run modes

| Mode | Entry point | When |
|------|-------------|------|
| Maya | `Workfiles` shelf button (calls `workfile_publisher.ui.main_window.show_in_maya`) | Inside Maya 2026 launched by TinyStudioLauncher. |
| After Effects | `Window -> TinyStudio Tools.jsx -> Workfile Publisher -> Run` | Native ScriptUI tool inside After Effects. |
| Standalone | `python launcher.py --host standalone --show ...` | UI iteration without a DCC. |

### Maya

The Maya shelf already has a `Workfiles` button (see `MayaRepository/2026/config/tinystudio_tools.json`). It loads `workfiles.main_window.main`, which is a thin shim in `MayaRepository/2026/scripts/workfiles/main_window.py` that imports from `workfile_publisher` here. The launcher adds this repo's `src/` to PYTHONPATH via `configs/maya_2026.json`.

### After Effects

The AE publisher does **not** use Python. It plugs into the existing TinyStudio panel and saves with `app.project.save(...)`:

1. The launcher sets `SHOW_NAME`, `TINYSTUDIO_LIB_DIR`, `AE_REPO`, etc on AE's environment.
2. In AE, open `Window -> TinyStudio Tools.jsx` (install it once with `AERepository/install/install_tinystudio_ae_panel.ps1` if it's not in the menu).
3. Pick `Workfile Publisher` from the dropdown and click `Run`.
4. `WorkfilePublisher.jsx` opens a palette aligned with the Maya publisher: show header, left workfile tree (shot → task), workfile table, variant + Publish / Open / Refresh.
5. The tool scans the target work folder for existing versions, reserves the next `v###` for the chosen variant, and saves with `app.project.save(...)`.

After Effects scripting preferences must allow file/network access: `Edit -> Preferences -> Scripting & Expressions -> Allow Scripts to Write Files and Access Network`.

### Standalone

Useful for UI iteration:

```powershell
$env:SHOW_NAME = "1000_TinyStudioTestShow"
$env:TINYSTUDIO_BASE_SHOW_DIR = "S:/"
$env:TINYSTUDIO_LIB_DIR = "L:/"
python launcher.py --host standalone
```

You can also pass `--show ...` and `--base-show-dir ...` instead of setting env vars.

---

## Path schema

The publisher writes into the pre-created `work/` folder under each asset or shot. Configured in `configs/path_schema.json`:

### Asset workfiles

```
S:/<show>/assets/<category>/<asset>/work/<dcc>/<task>/<asset>_<task>_<variant>_v###.<ext>
```

Example: `S:/1000_TinyStudioTestShow/assets/chr/character01/work/maya/model/character01_model_main_v001.ma`

### Shot workfiles

```
S:/<show>/episodes/<episode>/<sequence>/<shot>/work/<dcc>/<task>/<shot>_<task>_<variant>_v###.<ext>
```

Example: `S:/1000_TinyStudioTestShow/episodes/101/101_650/101_650_000/work/ae/comp/101_650_000_comp_main_v001.aep`

### Defaults

- `<variant>` defaults to `main`. Artists can override per-publish; each variant has its own version stream so `character01_model_main_v001.ma` and `character01_model_jenny_v001.ma` coexist.
- Variant names are normalised (lowercased, spaces -> underscores) and validated to `[a-z0-9][a-z0-9_-]*`.
- Versions are zero-padded to 3 digits and reserved atomically (`open(..., "xb")`), so two artists publishing the same variant at the same time won't collide on `v###`.

### Default task lists

| DCC | Context | Tasks |
|-----|---------|-------|
| Maya | Asset | `model, rig, shading` |
| Maya | Shot | `layout, anim, light, techviz` |
| AE | Asset | (not supported in v1) |
| AE | Shot | `layout, anim, light, techviz` |

---

## Adding or changing tasks / DCCs

Edit `configs/path_schema.json` and reopen the publisher:

```json
{
  "dcc": {
    "houdini": {
      "label": "Houdini",
      "extension": "hip",
      "supports_asset": true,
      "supports_shot": true,
      "asset_tasks": ["fx", "lookdev"],
      "shot_tasks": ["fx", "lighting"]
    }
  }
}
```

Then implement a new adapter in `src/workfile_publisher/adapters/` and register it in `adapters/__init__.py::build_adapter`.

The category list (`chr, env, prop, setdec, veh`) and episode/sequence/shot names are auto-discovered from the show drive; nothing to configure.

---

## Layout

```
GenTools/workfilePublisher/
  launcher.py                          -- standalone/dev entry point
  requirements.txt                     -- PySide6 (Maya bundles its own)
  configs/path_schema.json             -- DCCs, tasks, name template
  src/workfile_publisher/
    core/
      host.py                          -- detect_host()
      context.py                       -- env-driven StudioContext
      path_schema.py                   -- pure path builders
      versioning.py                    -- regex scan + atomic reserve
      discovery.py                     -- show-drive scanner with cache
      publish_service.py               -- publish() / open_workfile()
    adapters/
      base.py                          -- HostAdapter ABC
      maya_adapter.py                  -- cmds.file rename + save
      standalone_adapter.py            -- dev no-op
    ui/
      qt.py                            -- PySide6 / PySide2 shim
      main_window.py                   -- WorkfilePublisherWindow
      widgets/                         -- context, table, form
```

Integrations live outside this repo:

- `GenTools/TinyStudioLauncher/configs/maya_2026.json`           -- adds this repo to Maya PYTHONPATH.
- `MayaRepository/2026/scripts/workfiles/main_window.py`         -- shelf shim.
- `AERepository/config/tinystudio_ae_tools.json`                 -- AE tool registry entry.
- `AERepository/tools/WorkfilePublisher.jsx`                     -- native AE ScriptUI publisher.

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `SHOW_NAME is not set` dialog | Relaunch the DCC via TinyStudioLauncher; bare AE / Maya don't get the env vars. |
| `Show folder does not exist` | `S:/<SHOW_NAME>/` must exist on disk. |
| AE: nothing happens after `Run` | `Edit -> Preferences -> Scripting & Expressions -> Allow Scripts to Write Files and Access Network`, and reopen the TinyStudio panel after manifest edits. |
| AE: publish fails | Confirm the target `S:/<show>/episodes/.../work/ae/<task>` path is writable. |
| Maya: shelf button errors `No module named workfile_publisher` | Confirm the launcher added `{TINYSTUDIO_LIB_DIR}TinyStudioTools/GenTools/workfilePublisher/src` to PYTHONPATH (check `configs/maya_2026.json`). |
