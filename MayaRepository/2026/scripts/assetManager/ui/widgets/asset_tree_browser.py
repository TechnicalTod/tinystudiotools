"""Assets tree browser (category / asset)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...core.discovery import AssetDiscovery
from ..qt import Qt, QtWidgets, Signal


@dataclass(frozen=True)
class AssetTreeSelection:
    category: str
    asset: Optional[str] = None


class AssetTreeBrowser(QtWidgets.QWidget):
    """Browse ``assets/<category>/`` and existing asset folders."""

    selection_changed = Signal()

    def __init__(
        self,
        discovery: AssetDiscovery,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._discovery = discovery
        self._selection: Optional[AssetTreeSelection] = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QtWidgets.QLabel("Assets")
        label.setStyleSheet("font-weight: bold; color: #e8e8e8; background: transparent; border: none;")
        layout.addWidget(label)

        hint = QtWidgets.QLabel("Select a category or existing asset.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a8a8a8; background: transparent; border: none; font-size: 11px;")
        layout.addWidget(hint)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(200)
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._tree, 1)

        self._populate()

    def refresh(self) -> None:
        path = self._selection_path()
        self._discovery.invalidate()
        self._populate()
        self._restore_path(path)

    def current_selection(self) -> Optional[AssetTreeSelection]:
        return self._selection

    def current_category(self) -> Optional[str]:
        return self._selection.category if self._selection else None

    def _selection_path(self) -> Optional[str]:
        if not self._selection:
            return None
        if self._selection.asset:
            return f"{self._selection.category}/{self._selection.asset}"
        return self._selection.category

    def _restore_path(self, path: Optional[str]) -> None:
        if not path:
            return
        parts = path.split("/")
        if not parts:
            return
        category = parts[0]
        cat_item = self._find_child(self._tree.invisibleRootItem(), category)
        if cat_item is None:
            return
        if len(parts) == 1:
            self._tree.setCurrentItem(cat_item)
            return
        asset_item = self._find_child(cat_item, parts[1])
        if asset_item is not None:
            self._tree.setCurrentItem(asset_item)

    @staticmethod
    def _find_child(parent: QtWidgets.QTreeWidgetItem, text: str) -> Optional[QtWidgets.QTreeWidgetItem]:
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == text:
                return child
        return None

    def _populate(self) -> None:
        self._tree.clear()
        self._selection = None

        for category in self._discovery.categories():
            cat_item = QtWidgets.QTreeWidgetItem([category])
            cat_item.setData(0, Qt.UserRole, {"kind": "category", "category": category})
            cat_item.setExpanded(True)

            for asset in self._discovery.assets(category):
                asset_item = QtWidgets.QTreeWidgetItem([asset])
                asset_item.setData(
                    0,
                    Qt.UserRole,
                    {"kind": "asset", "category": category, "asset": asset},
                )
                cat_item.addChild(asset_item)

            self._tree.addTopLevelItem(cat_item)

    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            self._selection = None
            self.selection_changed.emit()
            return

        data = items[0].data(0, Qt.UserRole) or {}
        kind = data.get("kind")
        if kind == "category":
            self._selection = AssetTreeSelection(category=data["category"])
        elif kind == "asset":
            self._selection = AssetTreeSelection(
                category=data["category"],
                asset=data["asset"],
            )
        else:
            self._selection = None
        self.selection_changed.emit()
