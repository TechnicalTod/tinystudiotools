"""Register the TinyStudio Previs menu in the Unreal editor."""

from genTools.studio_python_path import ensure_gen_tools_shared

ensure_gen_tools_shared()

from importlib import reload

import unreal

_REGISTERED = False
_TICK_HANDLE = None
_FRAMES = 0
_WARMUP_FRAMES = 30

_SECTION_IMPORT = "Import"
_SECTION_LEVEL = "Level"
_SECTION_EXPORT = "Export"
_SECTION_SHOT = "ShotTools"
_SECTION_ASSET = "AssetTools"


def _reload_and_show(module_name: str, entry: str = "show") -> None:
    """Reload shared UI helpers and a tool module, then open its window."""
    import importlib

    import studioUiUtils
    import genTools.uiUtils as uiUtils

    reload(studioUiUtils)
    reload(uiUtils)
    module = importlib.import_module(module_name)
    reload(module)
    getattr(module, entry)()


def _add_previs_sections(menu: unreal.ToolMenu) -> None:
    menu.set_editor_property("separate_sections", True)
    menu.add_section(_SECTION_IMPORT, "Import")
    menu.add_section(_SECTION_LEVEL, "Level")
    menu.add_section(_SECTION_EXPORT, "Export")
    menu.add_section(_SECTION_SHOT, "Shot Tools")
    menu.add_section(_SECTION_ASSET, "Asset Tools")


def register_previs_menu() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    _REGISTERED = True

    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    previs_menu = main_menu.add_sub_menu(
        main_menu.menu_name, "Previs Menu", " ", "CFX PREVIS TOOLS", "CFX Previs Toolset"
    )
    _add_previs_sections(previs_menu)

    # -------------------------------------------------------------------------
    # Import
    # -------------------------------------------------------------------------

    @unreal.uclass()
    class importUnrealAssetClass(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("assetTools.importUnrealAsset")

    importUnrealAssetMenuButton = importUnrealAssetClass()
    importUnrealAssetMenuButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Import SetDec Assets",
        label="Import SetDec Assets",
        section=_SECTION_IMPORT,
        tool_tip="Import Unreal assets from published location",
    )
    importUnrealAssetMenuButton.register_menu_entry()

    @unreal.uclass()
    class ImportShotFromMayaClass(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("shotTools.ImportShotFromMaya")

    ImportShotFromMayaMenuButton = ImportShotFromMayaClass()
    ImportShotFromMayaMenuButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Import Published Shot",
        label="Import Published Shot",
        section=_SECTION_IMPORT,
        tool_tip="Build published shot from Maya",
    )
    ImportShotFromMayaMenuButton.register_menu_entry()

    @unreal.uclass()
    class ImportExportUSDUIClass(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("levelTools.SetDecSceneDescriptionUIUnreal")

    ImportExportUSDUIMenuButton = ImportExportUSDUIClass()
    ImportExportUSDUIMenuButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Import / Export Published Layout",
        label="Import / Export Published Layout",
        section=_SECTION_IMPORT,
        tool_tip="Import and Export USD layouts from user file",
    )
    ImportExportUSDUIMenuButton.register_menu_entry()

    @unreal.uclass()
    class ImportLevelAndSubLevelsClass(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("levelTools.ImportLevelAndSubLevels")

    ImportLevelAndSubLevelsMenuButton = ImportLevelAndSubLevelsClass()
    ImportLevelAndSubLevelsMenuButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Import sub levels",
        label="Import sub levels",
        section=_SECTION_IMPORT,
        tool_tip="Import PL and SL into current level",
    )
    ImportLevelAndSubLevelsMenuButton.register_menu_entry()

    # -------------------------------------------------------------------------
    # Level
    # -------------------------------------------------------------------------

    @unreal.uclass()
    class ENVBuilderClass(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("levelTools.EnvBuilder")

    ENVBuilderButton = ENVBuilderClass()
    ENVBuilderButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="ENV Builder",
        label="ENV Builder",
        section=_SECTION_LEVEL,
        tool_tip="Automatically Build ENV Dirs",
    )
    ENVBuilderButton.register_menu_entry()

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    @unreal.uclass()
    class USD_Asset_Exporter_Class(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("assetTools.USDAssetExporter")

    USDExporterMenuButton = USD_Asset_Exporter_Class()
    USDExporterMenuButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Bulk Asset Exporter",
        label="Bulk Asset Exporter",
        section=_SECTION_EXPORT,
        tool_tip="Bulk Export Assets to USD for Set Dec Processing",
    )
    USDExporterMenuButton.register_menu_entry()

    # -------------------------------------------------------------------------
    # Shot Tools
    # -------------------------------------------------------------------------

    @unreal.uclass()
    class USD_ShotVersioner_Class(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            import shotTools.shotVersioner as shotVersioner

            reload(shotVersioner)
            shotVersioner.schedule_version_and_fix_redirectors()

    ShotVersionerButton = USD_ShotVersioner_Class()
    ShotVersionerButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Shot Versioner",
        label="Shot Versioner",
        section=_SECTION_SHOT,
        tool_tip="Version Up Shot",
    )
    ShotVersionerButton.register_menu_entry()

    # -------------------------------------------------------------------------
    # Asset Tools
    # -------------------------------------------------------------------------

    @unreal.uclass()
    class remapShadersClass(unreal.ToolMenuEntryScript):
        @unreal.ufunction(override=True)
        def execute(self, context):
            _reload_and_show("assetTools.remapShaders")

    remapShadersButton = remapShadersClass()
    remapShadersButton.init_entry(
        owner_name=previs_menu.menu_name,
        menu=previs_menu.menu_name,
        name="Remap multiple shaders UI",
        label="Remap multiple shaders UI",
        section=_SECTION_ASSET,
        tool_tip="Tool to remap multiple shaders",
    )
    remapShadersButton.register_menu_entry()

    menus.refresh_all_widgets()
    unreal.log("TinyStudio Previs menu registered")


def _post_tick(delta_time: float) -> None:
    global _FRAMES, _TICK_HANDLE

    _FRAMES += 1
    if _FRAMES < _WARMUP_FRAMES:
        return

    try:
        register_previs_menu()
    except Exception as exc:
        unreal.log_error(f"TinyStudio Previs menu failed: {exc}")
    finally:
        if _TICK_HANDLE is not None:
            unreal.unregister_slate_post_tick_callback(_TICK_HANDLE)
            _TICK_HANDLE = None


def schedule_register_previs_menu() -> None:
    global _TICK_HANDLE
    unreal.log("TinyStudio: scheduling Previs menu registration")
    _TICK_HANDLE = unreal.register_slate_post_tick_callback(_post_tick)


if __name__ == "__main__":
    schedule_register_previs_menu()
