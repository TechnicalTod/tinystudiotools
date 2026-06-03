"""Assets tree browser (category / asset / publish type)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...core.discovery import AssetDiscovery
from ...core.schema import AssetPublishSchema
from ...core.versioning import list_publish_versions
from ..qt import Qt, QtWidgets, Signal


@dataclass(frozen=True)
class AssetTreeSelection:
    category: str
    asset: Optional[str] = None
    publish_type: Optional[str] = None


class AssetTreeBrowser(QtWidgets.QWidget):
    """Browse ``assets/<category>/<asset>/publish/<type>/``."""

    selection_changed = Signal()

    def __init__(
        self,
        discovery: AssetDiscovery,
        schema: AssetPublishSchema,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._discovery = discovery
        self._schema = schema
        self._selection: Optional[AssetTreeSelection] = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QtWidgets.QLabel("Assets")
        label.setStyleSheet("font-weight: bold; color: #e8e8e8; background: transparent; border: none;")
        layout.addWidget(label)

        hint = QtWidgets.QLabel(
            "Select a publish type to browse versions, or pick an asset to publish a new type."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a8a8a8; background: transparent; border: none; font-size: 11px;")
        layout.addWidget(hint)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(300)
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
        parts = [self._selection.category]
        if self._selection.asset:
            parts.append(self._selection.asset)
        if self._selection.publish_type:
            parts.append(self._selection.publish_type)
        return "/".join(parts)

    def _restore_path(self, path: Optional[str]) -> None:
        if not path:
            return
        parts = path.split("/")
        if not parts:
            return
        category = parts[0]
        cat_item = self._find_child(self._tree.invisibleRootItem(), category, match_key="category")
        if cat_item is None:
            return
        if len(parts) == 1:
            self._tree.setCurrentItem(cat_item)
            return
        asset_item = self._find_child(cat_item, parts[1], match_key="asset")
        if asset_item is None:
            return
        if len(parts) == 2:
            self._tree.setCurrentItem(asset_item)
            return
        publish_type = parts[2]
        for i in range(asset_item.childCount()):
            child = asset_item.child(i)
            data = child.data(0, Qt.UserRole) or {}
            if data.get("publish_type") == publish_type:
                self._tree.setCurrentItem(child)
                return

    @staticmethod
    def _find_child(
        parent: QtWidgets.QTreeWidgetItem,
        text: str,
        *,
        match_key: str,
    ) -> Optional[QtWidgets.QTreeWidgetItem]:
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole) or {}
            if match_key == "category" and data.get("category") == text:
                return child
            if match_key == "asset" and data.get("asset") == text:
                return child
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

                publish_dir = (
                    self._discovery.context.assets_root / category / asset / "publish"
                )
                for key in self._schema.publish_type_keys():
                    type_path = publish_dir / key
                    if not type_path.is_dir():
                        continue
                    entries = list_publish_versions(
                        type_path,
                        asset,
                        key,
                        padding=self._schema.version_padding,
                    )
                    if not entries:
                        continue

                    spec = self._schema.get_publish_type(key)
                    label = spec.label
                    count = len(entries)
                    if count > 1:
                        label = f"{spec.label}  ({count})"

                    type_item = QtWidgets.QTreeWidgetItem([label])
                    type_item.setData(
                        0,
                        Qt.UserRole,
                        {
                            "kind": "publish_type",
                            "category": category,
                            "asset": asset,
                            "publish_type": key,
                        },
                    )
                    asset_item.addChild(type_item)

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
        elif kind == "publish_type":
            self._selection = AssetTreeSelection(
                category=data["category"],
                asset=data["asset"],
                publish_type=data["publish_type"],
            )
        else:
            self._selection = None
        self.selection_changed.emit()
