import unreal
from importlib import reload

menus = unreal.ToolMenus.get()
#Get main menu
main_menu = menus.find_menu("LevelEditor.MainMenu")
#Add CFX menu
previs_menu = main_menu.add_sub_menu(main_menu.menu_name, "Previs Menu", " ", "CFX PREVIS TOOLS", "CFX Previs Toolset")

#Import SetDec Assets Button
@unreal.uclass()
class importUnrealAssetClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import assetTools.importUnrealAsset as importUnrealAsset
        reload (importUnrealAsset)
        importUnrealAsset.openWindow()
importUnrealAssetMenuButton = importUnrealAssetClass()

importUnrealAssetMenuButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Import SetDec Assets",
    label="Import SetDec Assets",
    section="import",
    tool_tip="Import Unreal assets from published location"
)
importUnrealAssetMenuButton.register_menu_entry()

#Import Published Shot Button
@unreal.uclass()
class ImportShotFromMayaClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import shotTools.ImportShotFromMaya as ImportShotFromMaya
        reload (ImportShotFromMaya)
        ImportShotFromMaya.openWindow()
ImportShotFromMayaMenuButton = ImportShotFromMayaClass()

ImportShotFromMayaMenuButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Import Published Shot",
    label="Import Published Shot",
    section="import",
    tool_tip="Build published shot from Maya"
)
ImportShotFromMayaMenuButton.register_menu_entry()

#Import / Export USD From File Button
@unreal.uclass()
class ImportExportUSDUIClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import levelTools.USDSceneImportExportUIUnreal as USDSceneImportExportUIUnreal
        reload (USDSceneImportExportUIUnreal)
        USDSceneImportExportUIUnreal.openWindow()
ImportExportUSDUIMenuButton = ImportExportUSDUIClass()
 
ImportExportUSDUIMenuButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Import / Export Published Layout",
    label="Import / Export Published Layout",
    section="import",
    tool_tip="Import and Export USD layouts from user file"
)
ImportExportUSDUIMenuButton.register_menu_entry()

#Import sub levels button
@unreal.uclass()
class ImportLevelAndSubLevelsClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import levelTools.ImportLevelAndSubLevels as ImportLevelAndSubLevels
        reload (ImportLevelAndSubLevels)
        ImportLevelAndSubLevels.openWindow()
ImportLevelAndSubLevelsMenuButton = ImportLevelAndSubLevelsClass()
 
ImportLevelAndSubLevelsMenuButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Import sub levels",
    label="Import sub levels",
    section="import",
    tool_tip="Import PL and SL into current level"
)
ImportLevelAndSubLevelsMenuButton.register_menu_entry()

#ENV Builder Button
@unreal.uclass()
class ENVBuilderClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import levelTools.EnvBuilder as EnvBuilder
        reload (EnvBuilder)
        EnvBuilder.openWindow()
ENVBuilderButton = ENVBuilderClass()
 
ENVBuilderButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="ENV Builder",
    label="ENV Builder",
    section="import",
    tool_tip="Automatically Build ENV Dirs"
)
ENVBuilderButton.register_menu_entry()

#Export Bulk Assets
@unreal.uclass()
class USD_Asset_Exporter_Class(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import assetTools.USDAssetExporter as USDAssetExporter
        reload (USDAssetExporter)
        USDAssetExporter.openWindow()
USDExporterMenuButton = USD_Asset_Exporter_Class()
 
USDExporterMenuButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Bulk Asset Exporter",
    label="Bulk Asset Exporter",
    section="import",
    tool_tip="Bulk Export Assets to USD for Set Dec Processing"
)
USDExporterMenuButton.register_menu_entry()

#Export Bulk Assets
@unreal.uclass()
class USD_ShotVersioner_Class(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import shotTools.shotVersioner as shotVersioner
        reload (shotVersioner)
        shotVersioner.version_and_fix_redirectors()
ShotVersionerButton = USD_ShotVersioner_Class()
 
ShotVersionerButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Shot Versioner",
    label="Shot Versioner",
    section="Shot Tools",
    tool_tip="Version Up Shot"
)
ShotVersionerButton.register_menu_entry()

#Remap shaders UI
@unreal.uclass()
class remapShadersClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import assetTools.remapShaders as remapShaders
        reload (remapShaders)
        remapShaders.openWindow()
remapShadersButton = remapShadersClass()
 
remapShadersButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Remap multiple shaders UI",
    label="Remap multiple shaders UI",
    section="import",
    tool_tip="Tool to remap multiple shaders"
)
remapShadersButton.register_menu_entry()

menus.refresh_all_widgets()