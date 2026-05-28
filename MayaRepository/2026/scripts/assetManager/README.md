# Asset Manager (Maya)

Publishes Maya assets (chr / prop / env / veh) into the show drive's `publish/` tree.

```
S:/<show>/assets/<category>/<asset>/publish/<publish_type>/<asset>_<publish_type>_<variant>_v###/
```

The active show, drive root, and username all come from `TinyStudioLauncher` via environment variables. The tool refuses to start if `SHOW_NAME` is unset.

Maya is the only supported host: the package lives entirely under `MayaRepository/2026/scripts/assetManager/`, and `assetManager.host.MayaHost` is the single place that imports `maya.cmds` / `pymel`.

---

## Entry point

The shelf JSON registers a button that calls `assetManager.ui.main_window.main`:

```json
{
  "type": "button",
  "label": "Asset Manager",
  "module": "assetManager.ui.main_window",
  "function": "main"
}
```

`main()` reads context from env vars, loads `configs/asset_publish_schema.json`, builds a `MayaHost`, and opens an `AssetManagerWindow` parented to Maya's main window.

---

## Publish flow

1. Select a **category** (or existing asset) in the left-hand tree (`chr`, `prop`, …).
2. Set **Asset name** — pick from the combo or type a new name (e.g. `Prop02`). Publishing creates the asset folder on disk if needed.
3. Set **Variant** (default `main`) and **Asset type** (Model / Rig / Layout).
4. Optionally capture or browse a screenshot for the version's preview thumbnail.
5. Click **Run checks** to populate the advisory pre-check panel — this is **never** a hard gate in v1.
6. Click **Publish**. The service reserves the next `v###` folder, runs the universal default exports, then the per-type exports, and writes a `manifest.json` listing every artifact.
7. Select a published version in the table, then **Load** (reference into the current scene) or **Open** (replace the current Maya scene with the publish).

Every publish, regardless of type, includes:

- `<asset>_<publish_type>_<variant>_v###.ma` — saved via the `maya_scene` step (universal default).
- `tex/<file>` — copies of textures referenced by applied materials, via `copy_applied_textures` (universal default).

The remaining artifacts are driven by `publish_types.<key>.exports` in the schema.

---

## Schema (`configs/asset_publish_schema.json`)

The schema is the **only** place to wire new product types, checks, or export steps once the Python handlers are registered.

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

Both `checks` and `exports` accept either a plain string (just the id) or an object with `id`, optional `severity` (checks only), and an optional `params` dict. Anything other than `id` / `severity` / `params` on a check entry is folded into `params` so legacy `nodes: [...]` keeps working.

---

## Adding a pre-publish check

1. Create `checks/plugins/<name>.py` exposing one function:
   ```python
   from ..runner import CheckContext, CheckResult

   def run(ctx: CheckContext) -> CheckResult:
       ok = ...
       return CheckResult(ctx.spec.id, "msg", "pass" if ok else ctx.spec.severity, ok)
   ```
2. Register the id in `checks/registry.py::DEFAULT_CHECKS`.
3. Add an entry under the matching publish type in the schema:
   ```json
   { "id": "<name>", "severity": "warning", "params": { ... } }
   ```

Plugins talk to the scene only through `ctx.host` (a `MayaHost`). To probe something `MayaHost` doesn't yet expose, add a method on it and call from the plugin — that keeps `maya.cmds` calls in one place.

### V1 check inventory

| Publish type | Check id | Rule |
|--------------|----------|------|
| model | `asset_name_pascal_case` | Asset folder name segments are PascalCase. |
| model | `materials_m_prefix_pascal` | Every assigned material is `M_<PascalCase>`. |
| rig | `root_joint_exists` | Configurable root joint (default `root_joint`) is in the scene. |
| rig | `root_joint_puppet_attrs` | All puppet metadata string attrs from `addCustomPuppetAttrs.py` are present. |
| layout | `content_under_env_group` | All mesh shapes are descendants of a top-level `ENV` group. |

Checks are advisory: results show in the **Pre-checks (advisory)** panel but never disable the Publish button. A future `enforce_checks_before_publish` flag will reintroduce blocking for production shows.

---

## Adding an export step

1. Create `exporters/plugins/<name>.py`:
   ```python
   from ..base import ExportContext, ExportResult

   def run(ctx: ExportContext) -> ExportResult:
       out = ctx.version_dir / f"{ctx.target.asset}.bin"
       ...
       return ExportResult(artifacts=[out.name])
   ```
2. Register the id in `exporters/registry.py::DEFAULT_EXPORTS`.
3. Reference it under either `default_exports` (runs for every publish) or `publish_types.<key>.exports` in the schema.

### V1 export inventory

| Step id | Where it runs | Notes |
|---------|---------------|-------|
| `maya_scene` | `default_exports` | Save the scene as `<asset>_<type>_<variant>_v###.ma`. |
| `copy_applied_textures` | `default_exports` | Copy textures from applied materials into `tex/`. |
| `fbx_selection` | `model.exports` | Export current selection as FBX. |
| `fbx_rig` | `rig.exports` | Export `root_joint` + `visGeo` as an Unreal-ready FBX bundle. |
| `layout_placeholder` | `layout.exports` | Writes `layout.json` describing the publish intent. Full layout export is a follow-up. |

---

## Layout

```
MayaRepository/2026/scripts/assetManager/
  __init__.py
  host.py                                  -- MayaHost: cmds / mel / pymel surface
  configs/asset_publish_schema.json        -- categories, types, checks, exports
  core/
    context.py                             -- env-driven StudioContext
    discovery.py                           -- assets-tree scanner
    paths.py                               -- publish-path builders
    publish_service.py                     -- reserve + write manifest
    schema.py                              -- schema dataclasses + loader
    target.py                              -- AssetPublishTarget
    versioning.py                          -- atomic version reserve
    variant.py                             -- variant normalisation
  checks/
    runner.py                              -- CheckRunner + CheckContext
    registry.py                            -- id -> plugin map
    plugins/                               -- one file per check
  exporters/
    base.py                                -- ExportContext + run_exports
    registry.py                            -- id -> plugin map
    plugins/                               -- one file per export step
  ui/
    qt.py                                  -- PySide6 shim
    main_window.py                         -- AssetManagerWindow + main()
    widgets/                               -- asset tree, table, form, panels
```

The launcher (`GenTools/TinyStudioLauncher/configs/maya_2026.json`) adds `MayaRepository/2026/scripts` to `PYTHONPATH`, which is all that's required for `import assetManager` to resolve inside Maya.
