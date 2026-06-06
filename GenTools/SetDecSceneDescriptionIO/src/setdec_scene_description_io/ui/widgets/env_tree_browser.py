"""Environment / variant tree browser."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...core.discovery import EnvDiscovery
from ..qt import Qt, QtWidgets, Signal


@dataclass(frozen=True)
class EnvTreeSelection:
    """A selectable environment or variant leaf in the tree."""

    env: str
    variant: Optional[str] = None


class EnvTreeBrowser(QtWidgets.QWidget):
    """Browse ``assets/env/<env>/publish/unreal/sceneDescription/<variant>/``."""

    selection_changed = Signal()

    def __init__(
        self,
        discovery: EnvDiscovery,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._discovery = discovery
        self._selection: Optional[EnvTreeSelection] = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QtWidgets.QLabel("Environments")
        label.setStyleSheet(
            "font-weight: bold; color: #e8e8e8; background: transparent; border: none;"
        )
        layout.addWidget(label)

        hint = QtWidgets.QLabel(
            "Select a variant to browse versions, or pick an environment to export a new variant."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "color: #a8a8a8; background: transparent; border: none; font-size: 11px;"
        )
        layout.addWidget(hint)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(240)
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._tree, 1)

        self._populate()

    def refresh(self, *, restore_path: Optional[str] = None) -> None:
        path = restore_path if restore_path is not None else self._selection_path()
        self._discovery.invalidate()
        self._populate()
        self._restore_path(path)

    def current_selection(self) -> Optional[EnvTreeSelection]:
        return self._selection

    def _selection_path(self) -> Optional[str]:
        if not self._selection:
            return None
        if self._selection.variant:
            return f"{self._selection.env}/{self._selection.variant}"
        return self._selection.env

    def _restore_path(self, path: Optional[str]) -> None:
        if not path:
            return
        parts = path.split("/")
        env_item = self._find_child(self._tree.invisibleRootItem(), parts[0], "env")
        if env_item is None:
            return
        if len(parts) == 1:
            self._tree.setCurrentItem(env_item)
            return
        variant_item = self._find_child(env_item, parts[1], "variant")
        if variant_item is not None:
            self._tree.setCurrentItem(variant_item)

    @staticmethod
    def _find_child(
        parent: QtWidgets.QTreeWidgetItem,
        text: str,
        kind: str,
    ) -> Optional[QtWidgets.QTreeWidgetItem]:
        for index in range(parent.childCount()):
            child = parent.child(index)
            data = child.data(0, Qt.UserRole) or {}
            if kind == "env" and data.get("env") == text and data.get("kind") == "env":
                return child
            if kind == "variant" and data.get("variant") == text:
                return child
        return None

    def _populate(self) -> None:
        self._tree.clear()
        self._selection = None

        for env in self._discovery.environments():
            env_item = QtWidgets.QTreeWidgetItem([env])
            env_item.setData(0, Qt.UserRole, {"kind": "env", "env": env})
            env_item.setExpanded(True)

            for variant in self._discovery.variants(env):
                variant_item = QtWidgets.QTreeWidgetItem([variant])
                variant_item.setData(
                    0,
                    Qt.UserRole,
                    {"kind": "variant", "env": env, "variant": variant},
                )
                env_item.addChild(variant_item)

            self._tree.addTopLevelItem(env_item)

    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            self._selection = None
            self.selection_changed.emit()
            return

        data = items[0].data(0, Qt.UserRole) or {}
        if data.get("kind") == "variant":
            self._selection = EnvTreeSelection(
                env=data["env"],
                variant=data.get("variant"),
            )
        elif data.get("kind") == "env":
            self._selection = EnvTreeSelection(env=data["env"])
        else:
            self._selection = None
        self.selection_changed.emit()
