# Workfile Manager (Maya)

Versioned Maya workfiles under the show drive. Supports **asset** workfiles (`work/maya/<task>/`) and **shot** workfiles under the episodes tree. Tasks and path layout are configured in `configs/path_schema.json`.

The tool is Maya-only. It lives entirely under `MayaRepository/2026/scripts/workfileManager/`. All `maya.cmds` / `maya.mel` usage is isolated in `workfileManager.host.MayaHost` so core and UI logic stay importable outside Maya where useful.

**After Effects** uses a separate native tool: `AERepository/tools/WorkfilePublisher.jsx`. It does not import this package or read `path_schema.json`.

---

## Requirements

Launch Maya through **TinyStudioLauncher**. The launcher sets environment variables and adds `MayaRepository/2026/scripts` to `PYTHONPATH` (see `GenTools/TinyStudioLauncher/configs/maya_2026.json`).

| Variable | Required | Purpose |
| -------- | -------- | ------- |
| `SHOW_NAME` | Yes | Active show folder name (e.g. `1000_TinyStudioTestShow`) |
| `TINYSTUDIO_BASE_SHOW_DIR` | Yes | Drive root containing show folders (e.g. `S:/`) |
| `TINYSTUDIO_LIB_DIR` | No | Studio library root (defaults to `L:/`) |
| `USERNAME` | No | Display name in the header (falls back to OS user) |

If `SHOW_NAME` or `TINYSTUDIO_BASE_SHOW_DIR` is missing, or the resolved show folder does not exist on disk, the tool raises `ContextError` and refuses to start.

---

## Entry point

The shelf is defined in `MayaRepository/2026/config/tinystudio_tools.json`:

```json
{
  "type": "button",
  "label": "Workfile Manager",
  "module": "workfileManager.ui.main_window",
  "function": "main",
  "icon": "workfileManager_manager.png"
}
```

`main()`:

1. Resolves `StudioContext` from env vars (`core.context.resolve_context`)
2. Loads `configs/path_schema.json`
3. Builds a `MayaHost`
4. Opens `WorkfileManagerWindow` parented to Maya's main window

Re-opening the shelf button creates a new window instance (previous reference is replaced).

---

## On-disk layout

### Asset workfiles

```
S:/<show>/assets/<category>/<asset>/work/maya/<task>/<asset>_<task>_<variant>_v###.ma
```

Example:

```
S:/MyShow/assets/prop/Hero_Chair/work/maya/model/Hero_Chair_model_main_v001.ma
```

### Shot workfiles

```
S:/<show>/episodes/<episode>/<sequence>/<shot>/work/maya/<task>/<shot>_<task>_<variant>_v###.ma
```

### Versioning

Each variant (`main`, `test`, etc.) has its own version stream. The manager atomically reserves the next `v###` slot by creating an empty placeholder file, then Maya overwrites it on save.

Default asset tasks: **model**, **rig**, **shading**, **layout**, **techviz**  
Default shot tasks: **layout**, **lighting**, **previz**, **techviz**

Edit `configs/path_schema.json` to change tasks or file extension.

---

## Package layout

```
workfileManager/
  host.py                 # MayaHost — maya.cmds save/open/setProject
  configs/
    path_schema.json
  core/
    context.py            # StudioContext from launcher env vars
    discovery.py          # Show-drive asset/episode scanner
    path_schema.py        # Path builders + schema loader
    publish_service.py    # Save/open orchestration
    versioning.py         # v### scan + atomic reserve
  ui/
    main_window.py        # Shelf entry point
    qt.py
    widgets/
      publish_form.py
      workfile_table.py
      workfile_tree_browser.py
```

---

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `ContextError: SHOW_NAME is not set` | Launch Maya through TinyStudioLauncher with a show selected |
| `Show folder does not exist` | Check `SHOW_NAME` matches a folder on the show drive |
| `SchemaError: Path schema not found` | Confirm `workfileManager/configs/path_schema.json` exists in the repo |
| `MayaHost requires running inside Autodesk Maya` | Open from the Maya shelf, not a standalone Python shell |
| Stylesheet missing | Confirm `genTools.uiUtils.load_qss` is on the Maya script path |

---

## Related tools

| Tool | Path | Purpose |
| ---- | ---- | ------- |
| Asset Manager | `assetManager/` | Publish assets to `publish/` (not workfiles) |
| AE Workfile Publisher | `AERepository/tools/WorkfilePublisher.jsx` | Separate ExtendScript implementation |

See also: [Docs/workfile-publisher-move.md](../../../../Docs/workfile-publisher-move.md) for the relocation history.
