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
        import importUnrealAsset
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
        import ImportShotFromMaya
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
        import ImportExportUSDUI_V2
        reload (ImportExportUSDUI_V2)
        ImportExportUSDUI_V2.openWindow()
ImportExportUSDUIMenuButton = ImportExportUSDUIClass()
 
ImportExportUSDUIMenuButton.init_entry(
    owner_name=previs_menu.menu_name,
    menu=previs_menu.menu_name,
    name="Import / Export USD From File",
    label="Import / Export USD From File",
    section="import",
    tool_tip="Import and Export USD layouts from user file"
)
ImportExportUSDUIMenuButton.register_menu_entry()

#Import sub levels button
@unreal.uclass()
class ImportLevelAndSubLevelsClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import ImportLevelAndSubLevels
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

#Import sub levels button
@unreal.uclass()
class ENVBuilderClass(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        import UE_envBuilder
        reload (UE_envBuilder)
        UE_envBuilder.openWindow()
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

menus.refresh_all_widgets()