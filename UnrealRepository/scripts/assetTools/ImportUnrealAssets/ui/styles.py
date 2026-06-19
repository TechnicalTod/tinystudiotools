"""UI styles for the Import Unreal Assets tool."""

BROWSER_STYLE = """
QFrame#ImportBrowserPanel {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    background-color: #2a2a2a;
}
QLabel#BrowserSectionLabel {
    color: #aaaaaa;
    font-size: 11px;
    font-weight: bold;
    padding-top: 2px;
}
QListWidget#ImportAssetList {
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    background-color: #1e1e1e;
    padding: 2px;
}
QListWidget#ImportAssetList::item {
    padding: 4px 6px;
}
QTableWidget#ImportAssetTable {
    gridline-color: #333333;
}
"""

TABLE_COMBO_QSS = """
QComboBox {
    color: #d0d0d0;
    background-color: #4e4e4e;
    border: 1px solid #1e1e1e;
    border-radius: 3px;
    padding: 0px 20px 0px 6px;
    font-size: 11px;
}
QComboBox:hover,
QComboBox:focus,
QComboBox:on {
    color: #d0d0d0;
    background-color: #4e4e4e;
    border: 1px solid #1e1e1e;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid #3a3a3a;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
"""

TABLE_ROW_HEIGHT = 32
TOOL_DISPLAY_NAME = "Import Unreal Assets"
IMPORT_WINDOW_KEY = "import_unreal_assets"
BROWSER_TAB_MODES = ("setdec", "assets", "rigs")
