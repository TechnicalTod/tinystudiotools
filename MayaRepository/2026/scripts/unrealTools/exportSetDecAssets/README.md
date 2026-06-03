# Publish Set Dec Assets

Maya tool for publishing set-dressing (Set Dec) geometry and materials to the show drive for Unreal and other downstream pipelines. It versions assets per **group**, **variant**, and **version**, and exports FBX, USD, Maya scene, and texture copies in a consistent folder layout.

## Requirements

- **Maya 2026** (PySide6) with **mayaUsdPlugin** loaded
- Session launched through **TinyStudioLauncher** so environment variables are set:
  - `SHOW_NAME` — active show folder name (e.g. `1000_TinyStudioTestShow`)
  - `TINYSTUDIO_BASE_SHOW_DIR` — show drive root (e.g. `S:/`)
- Mesh transforms with a **mesh shape** assigned
- **Legacy USD Preview Surface** material (see [Materials](#materials))

If `SHOW_NAME` is missing, the tool refuses to open.

## Opening the tool

**Shelf / menu:** Unreal → **Publish Setdec Assets**  
(config: `MayaRepository/2026/config/tinystudio_tools.json`)

**Script:**

```python
import unrealTools.exportSetDecAssets as setdec
setdec.openWindow()
```

The window title and header show the current **Show**, **User**, and **Drive** from the launcher (read-only).

## Show folder layout

Published assets are written under the same layout as other TinyStudio asset tools:

```text
{show_root}/assets/setdec/
└── {group}/                          # e.g. setdec01
    └── {asset_name}/                 # short DAG name, e.g. pCube1
        └── {variant}/                # e.g. base
            └── {version}/            # e.g. v001
                ├── fbx/
                ├── usd/
                ├── maya/
                └── tex/
```

- **`show_root`** = `TINYSTUDIO_BASE_SHOW_DIR` / `SHOW_NAME` (normalized like Asset Manager)
- **Set Dec Group** dropdown lists subfolders of `{show_root}/assets/setdec/`
- Create group folders on the show drive before publishing if the list is empty

Example:

```text
S:/1000_TinyStudioTestShow/assets/setdec/setdec01/pCube1/base/v001/
```

## Artist workflow

### 1. Prepare the mesh

- Model set-dressing geometry with UVs as required by your show.
- Name transforms clearly; the **short name** (no path) is used as the asset key on disk.
- Avoid duplicate short names in the publish list.

### 2. Assign materials

Use a **legacy `usdPreviewSurface`** shading network with `file` texture nodes wired to the standard USD Preview inputs (see [Materials](#materials)).

Helper in `shadingTools/genShaderUtils.py`:

```python
import shadingTools.genShaderUtils as gsu
gsu.createSetDecShaderPerShape()  # selected transforms
```

### 3. Publish

1. Open **Publish Set Dec Assets**.
2. Choose **Set Dec Group** (or type a new group name if the combo is editable).
3. Select mesh(es) in the viewport → **Add Set Dec**.
4. Set **Variant** and **New Version** per row (existing versions are listed under **Current Version**).
5. **Publish**.

On success:

- Files are written to the version folder (`fbx/`, `usd/`, `maya/`, `tex/`).
- The scene mesh is replaced by the published import (blue outliner, `published` attribute).
- Texture paths on the published network point at the copied `tex/` folder.

### 4. Unpublish (optional)

Select published row(s) → **Unpublish Selection** to restore shader assignment using stored `shaderName` / `publishedShaderList` when the original shaders still exist in the scene.

## UI overview

| Area | Purpose |
|------|--------|
| **Header** | Show, user, drive (from launcher) |
| **Set Dec Group** | Target folder under `assets/setdec/` |
| **Table** | Assets to publish: name, variant, current/new version |
| **Add / Remove / Clear / Refresh** | Manage the publish list |
| **Unpublish Selection** | Revert published state for selected rows |
| **Publish** | Run validation, copy textures, export |

**Table interactions**

- Click a **Set Dec name** cell to select that object in Maya.
- Right-click for variant rename on multiple rows.
- Duplicate names are highlighted **red**; already-published names **blue**.

## Materials

### Supported (publish path)

**`usdPreviewSurface`** shader assigned to the shape’s shading group, with textures connected to:

| Map | Maya attribute |
|-----|----------------|
| Diffuse | `diffuseColor` |
| Emissive | `emissiveColor` |
| AO | `occlusion` |
| Opacity | `opacity` |
| Metallic | `metallic` |
| Roughness | `roughness` |
| Normal | `normal` (via bump network) |
| Translucency | `clearcoat` |
| Displacement | `displacement` |

Texture filenames should follow the suffix convention in `constants.py` (e.g. `*_Diffuse`, `*_Normal`). UDIM paths using `.<UDIM>.png` are supported on publish.

### Not supported yet (Maya 2026 Lookdev)

HyperShade **USD Preview** in Maya 2026 often creates a **`MaterialXSurfaceShader`** + MaterialX stack, not a `usdPreviewSurface` node. That assignment **fails** this tool’s shader check and cannot be texture-walked until MaterialX support or convert-on-publish is implemented.

**Use legacy `usdPreviewSurface` for Set Dec publish** (e.g. `genShaderUtils.createSetDecShaderPerShape()` or your studio shelf).

## Publish outputs

For each asset version the tool creates:

| Output | Location |
|--------|----------|
| FBX | `{version}/fbx/{asset}_{version}.fbx` |
| USD | `{version}/usd/{asset}_{version}.usda` |
| Maya | `{version}/maya/{asset}_{version}.ma` |
| Textures | `{version}/tex/` (copied from shader `file` nodes) |

USD export uses `materialsScopeName=mtl` and a root scope named after the asset. Published transforms store metadata: `assetName`, `variantName`, `version`, `basePath`, `published`, `publishedShaderList`.

## Validation (preflight)

Publish is blocked if:

- Any listed object has no mesh shape
- Shader is not **legacy USD Preview** (`usdPreviewSurface`)
- **Duplicate** short names appear in the list
- Objects are already **published** (unpublish or remove first)
- Normal maps / shader types do not match USD Preview expectations

## Unreal / downstream

- Unreal import paths may reference `/Game/01_Assets/SETDEC` (see `unrealTools/conversionUtilites.py`).
- On-disk layout uses `assets/setdec` on the show drive; keep import rules aligned with your project.
- Confirm USD material binding in-engine after pipeline changes.

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Tool won’t open | Launch Maya via TinyStudioLauncher; verify `SHOW_NAME` |
| Empty Set Dec Group list | Create `{show}/assets/setdec/{group}/` on the show drive |
| “Must be USD Preview material” | Assign legacy `usdPreviewSurface`, not MaterialX-only USD Preview |
| Dropdown arrow missing on group combo | Reload tool after `dark.qss` / icon updates; ensure `MayaRepository/2026/icons/dropDownArrow.png` exists |
| Textures not in `tex/` | Wire `file` nodes to `usdPreviewSurface` attributes; check map naming |
| Wrong publish path | Paths come from `paths.py` → `{show_root}/assets/setdec/` (not `03_Production/Assets/SETDEC`) |

## Module layout (TD)

| File | Role |
|------|------|
| `__init__.py` | `openWindow()` entry point |
| `main_window.py` | Qt UI, table, publish/unpublish actions |
| `paths.py` | Show-root resolution, `assets/setdec` paths |
| `publish_ops.py` | Texture copy, FBX/USD/Maya export, publish metadata |
| `validation.py` | Preflight checks |
| `unpublish_ops.py` | Restore shaders / attrs |
| `constants.py` | Texture parameter map |
| `styling.py` | Loads shared `dark.qss` via `genTools.uiUtils` |

## Known limitations

- MaterialX-based USD Preview (Maya 2026 default UI) is not yet a first-class publish source.
- Publish **replaces** the live mesh with the imported published `.ma` file.
- `parentScope` USD export option may be deprecated in favour of `rootPrim` in a future update.
- Legacy publishes under `03_Production/Assets/SETDEC` are not migrated automatically.

## Related tools

- `shadingTools/genShaderUtils.py` — create legacy USD Preview per shape
- `unrealTools/convertMegascansAssets.py` — Megascans → USD Preview networks
- Workfile Publisher — same show env / `assets/` layout for other categories
