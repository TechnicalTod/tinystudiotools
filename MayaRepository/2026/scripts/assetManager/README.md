# Asset Manager (Maya)

Publishes Maya assets into the show drive under a fixed folder layout. Supported categories are **chr**, **prop**, **env**, and **veh**; supported publish types are **Model**, **Rig**, and **Layout** (configurable in the schema).

The tool is Maya-only. It lives entirely under `MayaRepository/2026/scripts/assetManager/`. All `maya.cmds` / `maya.mel` / `pymel` usage is isolated in `assetManager.host.MayaHost` so checks, exports, and core logic stay importable outside Maya where useful.

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
  "label": "Asset Manager",
  "module": "assetManager.ui.main_window",
  "function": "main",
  "icon": "assetManager_treasure.png"
}
```

`main()`:

1. Resolves `StudioContext` from env vars (`core.context.resolve_context`)
2. Loads `configs/asset_publish_schema.json`
3. Builds a `MayaHost`
4. Opens `AssetManagerWindow` parented to Maya's main window

Re-opening the shelf button creates a new window instance (previous reference is replaced).

---

## On-disk layout

Published assets follow this path:

```
S:/<show>/assets/<category>/<asset>/publish/<publish_type>/<asset>_<publish_type>_<variant>_v###/
```

Example version folder for `BigGuy` model `main` v001:

```
S:/MyShow/assets/chr/BigGuy/publish/model/BigGuy_model_main_v001/
  BigGuy_model_main_v001.ma          # maya_scene (default export)
  BigGuy_model_main_v001_preview.png # optional viewport capture at publish time
  manifest.json                      # metadata + artifact list
  tex/                               # copy_applied_textures
  …                                  # per-type exports (FBX, layout.json, etc.)
```

### Version folder naming

Pattern: `{asset}_{publish_type}_{variant}_v{padding}`

- **Asset** — PascalCase folder name (`BigGuy`, `Prop02`)
- **Publish type** — schema key (`model`, `rig`, `layout`)
- **Variant** — lowercase slug (`main`, `test`, `lod0`)
- **Version** — zero-padded integer (`v001`, `v002`, …)

### `manifest.json`

Written (or updated) on every publish:

```json
{
  "asset": "BigGuy",
  "category": "chr",
  "publish_type": "model",
  "variant": "main",
  "version": 1,
  "artifacts": [
    "BigGuy_model_main_v001.ma",
    "tex/",
    "BigGuy_model_main_v001.fbx",
    "BigGuy_model_main_v001_preview.png"
  ]
}
```

If export fails after the version folder was created, `PublishService` removes the empty or partial folder before re-raising.

---

## User interface

### Window layout

Three resizable columns (default window ~1650×930):

| Column | Default width | Contents |
| ------ | ------------- | -------- |
| **Left** | ~330px | Asset tree |
| **Center** | stretch | Published versions table + publish form |
| **Right** | ~420px | Screenshot (top, compact) and pre-checks (bottom, taller) |

The header bar shows **Show**, **Host**, **User**, and **Drive** from the resolved context.

### Left — asset tree

Hierarchy: **Category → Asset → Publish type**

| Node | When it appears | Selecting it |
| ---- | --------------- | ------------ |
| Category | Always (if folder exists on disk and is in schema whitelist) | Sets category in the form; table stays empty |
| Asset | Under each category | Sets category + asset name; table stays empty until a publish type is chosen |
| Publish type | Only when that type folder exists **and** contains at least one version directory | Sets category, asset, and type; drives the center table and syncs the form type dropdown |

Publish type labels use the schema display name (e.g. `Model`). A count badge appears when multiple versions exist: `Model  (3)`.

**Variants are never shown in the tree** — all variants for the selected type appear in the center table.

After **Refresh** or **Publish**, the tree rescans disk and restores the previous selection path when possible (`category/asset/publish_type`).

### Center — versions table

Columns: **Variant**, **Version**, **Summary**, **Modified**

- Populated only when a **publish type leaf** is selected in the tree
- Lists **all variants** for that asset + type (`include_all_variants=True`)
- **Summary** shows file/folder counts inside the version directory
- **Double-click** a row to **Open** that publish (same as the Open button)

### Center — publish form

| Field | Notes |
| ----- | ----- |
| **Asset name** | Editable combo populated from disk for the selected category; type a new name to create an asset on first publish |
| **Variant** | Default `main`; normalized to lowercase slug |
| **Asset type** | Model / Rig / Layout — used for first publish to a type not yet in the tree; synced when selecting a type leaf |

| Button | Action |
| ------ | ------ |
| **Refresh** | Rescans the show drive, refreshes tree asset list, keeps form values |
| **Load** | References the selected table row into the current scene (`MayaHost.reference_scene`, namespace = sanitized asset name) |
| **Open** | Opens the selected publish as the current Maya file; prompts if the scene has unsaved changes |
| **Publish** | Reserves next version, runs exports, writes manifest, refreshes UI |

Load/Open are disabled when the table is empty or no row is selected.

### Right — screenshot

- **Capture** — viewport playblast to a temp PNG attached to the next publish
- **Clear** — removes the attached capture (does not affect table preview from disk)

Selecting a table row shows that version's on-disk preview in the panel (read-only display; does not attach to publish).

There is no file-picker browse in v1 — only viewport capture.

### Right — pre-checks (advisory)

- **Run checks** — executes the check list for the current publish type against the open Maya scene
- Results are **advisory only** in v1: they never disable **Publish**
- Changing category, asset, variant, or type **clears** previous results (avoids stale output)
- Severity icons: pass (green), warning (yellow), error (red)

A future `enforce_checks_before_publish` schema flag may block publish on error-severity failures in production shows. `CheckRunner.has_blocking_errors()` already exists for that follow-up.

---

## Publish workflow

### Browse existing publishes

1. Select **category → asset → publish type** in the tree
2. Review all variants in the table
3. Select a row to preview its screenshot
4. **Load** or **Open** as needed

### Publish a new version (existing type in tree)

1. Select the publish type leaf in the tree
2. Set **Variant** (and change **Asset type** only if you intentionally target a different type)
3. Optionally **Capture** a screenshot
4. Optionally **Run checks**
5. Click **Publish**

### First publish for an asset or type

1. Select **category** or **asset** in the tree (no type leaf yet)
2. Set **Asset name**, **Variant**, and **Asset type** in the form
3. Optionally capture / run checks
4. Click **Publish**

Publishing creates missing folders on disk (`assets/<category>/<asset>/publish/<type>/…`). After success, the tree refreshes and the new publish type appears under the asset.

### Target resolution

The UI builds an `AssetPublishTarget` (category, asset, publish_type, variant, dcc):

| Use case | `publish_type` source |
| -------- | --------------------- |
| Browsing the table | Tree selection only (must select a type leaf) |
| Publish / Run checks | Tree `publish_type` if set, else form **Asset type** dropdown |
| Category | From tree selection synced into the form |
| Asset | Tree selection or form **Asset name** |
| Variant | Form **Variant** (defaults to schema `default_variant`) |

Asset and variant names are validated (`core.asset_name`, `core.variant`) before publish or check runs.

---

## Universal publish outputs

Every publish type runs `default_exports` first, then type-specific exports:

| Artifact | Export id | Description |
| -------- | --------- | ----------- |
| Maya scene | `maya_scene` | Saves current scene as `<asset>_<type>_<variant>_v###.ma` (or `.mb` via params) |
| Textures | `copy_applied_textures` | Copies textures from applied materials into `tex/` (including UDIM siblings on disk) |

Type-specific artifacts come from `publish_types.<key>.exports` in the schema (see inventory below).

---

## Schema (`configs/asset_publish_schema.json`)

The schema is the **configuration surface** for categories, publish types, checks, and export pipelines. Python handlers must still be registered in the check/export registries.

```jsonc
{
  "schemaVersion": 2,
  "allowed_categories": ["chr", "prop", "env", "veh"],
  "default_variant": "main",
  "version_padding": 3,
  "dcc": "maya",

  "default_exports": [
    { "id": "maya_scene" },
    { "id": "copy_applied_textures" }
  ],

  "publish_types": {
    "model": {
      "label": "Model",
      "checks": [
        { "id": "asset_name_pascal_case", "severity": "warning" },
        { "id": "materials_m_prefix_pascal", "severity": "warning" }
      ],
      "exports": [
        { "id": "fbx_selection" }
      ]
    }
  }
}
```

### Check entries

Each check is either a string id or an object:

```json
{ "id": "root_joint_exists", "severity": "error", "params": { "root_joint": "root_joint" } }
```

- **`severity`** — `error` or `warning` (used when the check fails; passes always show as pass)
- **`params`** — passed to the plugin via `CheckContext.params`
- Legacy top-level keys (e.g. `"nodes": ["foo"]`) are folded into `params`

### Export entries

Each export is either a string id or `{ "id": "…", "params": { … } }`.

Export order: **`default_exports`** (global) then **`publish_types.<key>.exports`** (per type).

---

## Pre-publish checks

### Adding a check

1. Create `checks/plugins/<name>.py`:

   ```python
   from ..runner import CheckContext, CheckResult

   def run(ctx: CheckContext) -> CheckResult:
       ok = ...
       return CheckResult(ctx.spec.id, "message", "pass" if ok else ctx.spec.severity, ok)
   ```

2. Register the id in `checks/registry.py` → `DEFAULT_CHECKS`
3. Add an entry under the matching publish type in the schema

Plugins must use `ctx.host` (`MayaHost`) for scene queries — not `maya.cmds` directly.

### Checks wired in schema (v1)

| Publish type | Check id | Severity | Rule |
| ------------ | -------- | -------- | ---- |
| model | `asset_name_pascal_case` | warning | Asset folder name segments are PascalCase |
| model | `materials_m_prefix_pascal` | warning | Assigned materials match `M_<PascalCase>` |
| rig | `root_joint_exists` | error | Configurable root joint exists (default `root_joint`) |
| rig | `root_joint_puppet_attrs` | warning | Puppet metadata string attrs present on root joint |
| layout | `content_under_env_group` | warning | Mesh shapes are under top-level `ENV` group |

### Registered but optional (not in schema by default)

These handlers exist in `checks/registry.py` and can be enabled by adding them to the schema:

| Check id | Purpose |
| -------- | ------- |
| `selection_not_empty` | Current selection is non-empty |
| `no_history_on_selection` | Selected mesh shapes have no construction history |
| `nodes_exist` | Configured node list exists (`params.nodes`) |

---

## Export steps

### Adding an export

1. Create `exporters/plugins/<name>.py`:

   ```python
   from ..base import ExportContext, ExportResult

   def run(ctx: ExportContext) -> ExportResult:
       out = ctx.version_dir / "artifact.ext"
       ...
       return ExportResult(artifacts=[out.name])
   ```

2. Register the id in `exporters/registry.py` → `DEFAULT_EXPORTS`
3. Reference under `default_exports` or `publish_types.<key>.exports`

### Export inventory (v1)

| Step id | Where | Output |
| ------- | ----- | ------ |
| `maya_scene` | `default_exports` | `<asset>_<type>_<variant>_v###.ma` |
| `copy_applied_textures` | `default_exports` | `tex/` with applied material textures |
| `fbx_selection` | `model.exports` | FBX of current selection |
| `fbx_rig` | `rig.exports` | `UnrealExport/<asset>_ExportedRigForUnreal_<version>.fbx` from `root_joint` + `visGeo` |
| `layout_placeholder` | `layout.exports` | `layout.json` stub describing publish intent |

---

## Versioning

- **Next version** — highest existing `v###` for the same asset + type + variant, plus one
- **Reservation** — `reserve_version_dir` creates the folder atomically (`mkdir`); on collision it tries the next number (up to 64 attempts)
- **Listing** — `list_publish_versions` scans publish type folders with a regex matching the naming convention; sorts by variant then version (newest first)

---

## Package layout

```
MayaRepository/2026/scripts/assetManager/
  __init__.py
  host.py                                  # MayaHost — sole Maya API surface
  configs/asset_publish_schema.json        # categories, types, checks, exports
  core/
    asset_name.py                          # asset folder name validation
    context.py                             # env-driven StudioContext
    discovery.py                           # category/asset scanner (whitelist)
    paths.py                               # publish path + filename helpers
    publish_service.py                     # publish orchestration + manifest
    schema.py                              # schema dataclasses + loader
    target.py                              # AssetPublishTarget
    versioning.py                          # scan, reserve, PublishEntry
    variant.py                             # variant normalisation
  checks/
    runner.py                              # CheckRunner, CheckContext, CheckResult
    registry.py                            # id → plugin
    plugins/                               # one module per check
  exporters/
    base.py                                # ExportContext, run_exports
    registry.py                            # id → plugin
    plugins/                               # one module per export step
  ui/
    qt.py                                  # PySide6 / shiboken shim
    main_window.py                         # AssetManagerWindow + main()
    widgets/
      asset_tree_browser.py                # left tree
      publish_table.py                     # center table
      publish_form.py                      # center form
      screenshot_panel.py                  # right top
      precheck_panel.py                    # right bottom
```

---

## Troubleshooting

| Symptom | Likely cause |
| ------- | ------------- |
| Tool won't open | Maya not launched via TinyStudioLauncher, or show folder missing |
| Empty category list | No `assets/<category>/` folders on disk for schema categories |
| Type missing under asset | No publishes yet for that type — use the form **Asset type** and **Publish** |
| Table empty with asset selected | Select a **publish type** leaf; asset-only selection is for new publishes |
| Publish fails on export | Check Maya script editor; partial version folder is rolled back |
| FBX / rig export fails | Missing selection (`fbx_selection`) or missing `root_joint` / `visGeo` (`fbx_rig`) |
| Load references wrong namespace | Namespace is derived from asset name (`MayaHost.sanitize_namespace`) |
| Capture fails | Viewport playblast error — publish still works without a preview image |

---

## Design notes

- **Advisory checks in v1** — artists can publish with warnings or even rig `error`-severity check failures; strict gating is deferred.
- **Schema-driven pipeline** — new studio rules are usually a JSON edit plus a small plugin, not a UI change.
- **Maya isolation** — extend scene access by adding methods to `MayaHost`, then calling them from plugins.
- **Discovery cache** — `AssetDiscovery.invalidate()` runs on tree refresh; categories are filtered to `allowed_categories` even if extra folders exist on disk.
