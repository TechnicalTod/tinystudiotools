"""Set Dec published asset browser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ...core.context import StudioContext
from ...core.versioning import PublishEntry
from ..qt import Qt, QtWidgets, Signal


@dataclass(frozen=True)
class SetDecTreeSelection:
    group: str
    asset: Optional[str] = None
    variant: Optional[str] = None


def _list_subdirs(folder: Path) -> list[str]:
    if not folder.exists():
        return []
    try:
        return sorted(
            (entry.name for entry in folder.iterdir() if entry.is_dir()),
            key=str.lower,
        )
    except PermissionError:
        return []


def _version_number(version_name: str) -> Optional[int]:
    match = re.match(r"^v(?P<version>\d+)$", version_name, re.IGNORECASE)
    if not match:
        return None
    return int(match.group("version"))


def list_setdec_versions(
    setdec_root: Path,
    group: str,
    asset: str,
    variant: str,
) -> list[PublishEntry]:
    variant_dir = setdec_root / group / asset / variant
    entries: list[PublishEntry] = []
    for version_name in _list_subdirs(variant_dir):
        version = _version_number(version_name)
        if version is None:
            continue
        entries.append(
            PublishEntry(
                path=variant_dir / version_name,
                asset=asset,
                publish_type="setdec",
                variant=variant,
                version=version,
            )
        )
    entries.sort(key=lambda entry: entry.version, reverse=True)
    return entries


class SetDecTreeBrowser(QtWidgets.QWidget):
    """Browse ``assets/setdec/<group>/<asset>/<variant>/``."""

    selection_changed = Signal()

    def __init__(
        self,
        context: StudioContext,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._setdec_root = context.assets_root / "setdec"
        self._selection: Optional[SetDecTreeSelection] = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QtWidgets.QLabel("Set Dec")
        label.setStyleSheet("font-weight: bold; color: #e8e8e8; background: transparent; border: none;")
        layout.addWidget(label)

        hint = QtWidgets.QLabel(
            "Select a variant to browse published Set Dec versions."
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

    @property
    def setdec_root(self) -> Path:
        return self._setdec_root

    def refresh(self) -> None:
        path = self._selection_path()
        self._populate()
        self._restore_path(path)

    def current_selection(self) -> Optional[SetDecTreeSelection]:
        return self._selection

    def _selection_path(self) -> Optional[str]:
        if self._selection is None:
            return None
        parts = [self._selection.group]
        if self._selection.asset:
            parts.append(self._selection.asset)
        if self._selection.variant:
            parts.append(self._selection.variant)
        return "/".join(parts)

    def _restore_path(self, path: Optional[str]) -> None:
        if not path:
            return
        parts = path.split("/")
        if not parts:
            return
        group_item = self._find_child(self._tree.invisibleRootItem(), parts[0], "group")
        if group_item is None:
            return
        if len(parts) == 1:
            self._tree.setCurrentItem(group_item)
            return
        asset_item = self._find_child(group_item, parts[1], "asset")
        if asset_item is None:
            return
        if len(parts) == 2:
            self._tree.setCurrentItem(asset_item)
            return
        variant_item = self._find_child(asset_item, parts[2], "variant")
        if variant_item is not None:
            self._tree.setCurrentItem(variant_item)

    @staticmethod
    def _find_child(
        parent: QtWidgets.QTreeWidgetItem,
        text: str,
        match_key: str,
    ) -> Optional[QtWidgets.QTreeWidgetItem]:
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole) or {}
            if data.get(match_key) == text:
                return child
        return None

    def _populate(self) -> None:
        self._tree.clear()
        self._selection = None

        for group in _list_subdirs(self._setdec_root):
            group_item = QtWidgets.QTreeWidgetItem([group])
            group_item.setData(0, Qt.UserRole, {"kind": "group", "group": group})
            group_item.setExpanded(True)

            for asset in _list_subdirs(self._setdec_root / group):
                asset_item = QtWidgets.QTreeWidgetItem([asset])
                asset_item.setData(
                    0,
                    Qt.UserRole,
                    {"kind": "asset", "group": group, "asset": asset},
                )

                for variant in _list_subdirs(self._setdec_root / group / asset):
                    entries = list_setdec_versions(
                        self._setdec_root,
                        group,
                        asset,
                        variant,
                    )
                    if not entries:
                        continue
                    label = variant
                    if len(entries) > 1:
                        label = f"{variant}  ({len(entries)})"
                    variant_item = QtWidgets.QTreeWidgetItem([label])
                    variant_item.setData(
                        0,
                        Qt.UserRole,
                        {
                            "kind": "variant",
                            "group": group,
                            "asset": asset,
                            "variant": variant,
                        },
                    )
                    asset_item.addChild(variant_item)

                group_item.addChild(asset_item)

            self._tree.addTopLevelItem(group_item)

    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            self._selection = None
            self.selection_changed.emit()
            return

        data = items[0].data(0, Qt.UserRole) or {}
        kind = data.get("kind")
        if kind == "group":
            self._selection = SetDecTreeSelection(group=data["group"])
        elif kind == "asset":
            self._selection = SetDecTreeSelection(
                group=data["group"],
                asset=data["asset"],
            )
        elif kind == "variant":
            self._selection = SetDecTreeSelection(
                group=data["group"],
                asset=data["asset"],
                variant=data["variant"],
            )
        else:
            self._selection = None
        self.selection_changed.emit()
