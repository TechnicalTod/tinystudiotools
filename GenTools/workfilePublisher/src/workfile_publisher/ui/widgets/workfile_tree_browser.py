"""Workfile tree browser (assets or episodes → … → task), matching pipeline layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ...core import path_schema as ps
from ...core.discovery import ShowDiscovery
from ..qt import Qt, QtWidgets, Signal


@dataclass(frozen=True)
class WorkfileTreeSelection:
    """A selectable asset, shot, or task leaf in the workfile tree."""

    kind: str  # "asset" | "shot"
    task: Optional[str] = None
    category: Optional[str] = None
    asset: Optional[str] = None
    episode: Optional[str] = None
    sequence: Optional[str] = None
    shot: Optional[str] = None


class WorkfileTreeBrowser(QtWidgets.QWidget):
    """Tabbed asset and episode trees down to disk-backed task leaves."""

    selection_changed = Signal()

    def __init__(
        self,
        discovery: ShowDiscovery,
        schema: ps.PathSchema,
        dcc: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._discovery = discovery
        self._schema = schema
        self._dcc = dcc
        self._dcc_spec = schema.get_dcc(dcc)
        self._selection: Optional[WorkfileTreeSelection] = None

        self._asset_tree: Optional[QtWidgets.QTreeWidget] = None
        self._shot_tree: Optional[QtWidgets.QTreeWidget] = None
        self._tabs: Optional[QtWidgets.QTabWidget] = None
        self._use_tabs = (
            self._dcc_spec.supports_asset and self._dcc_spec.supports_shot
        )
        self._active_kind: Optional[str] = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        if self._use_tabs:
            self._tabs = QtWidgets.QTabWidget()
            if self._dcc_spec.supports_asset:
                self._asset_tree = self._create_tree()
                self._tabs.addTab(self._asset_tree, "Assets")
            if self._dcc_spec.supports_shot:
                self._shot_tree = self._create_tree()
                self._tabs.addTab(self._shot_tree, "Episodes")
            self._tabs.currentChanged.connect(self._on_tab_changed)
            layout.addWidget(self._tabs, 1)
            self._active_kind = "asset" if self._asset_tree else "shot"
        else:
            if self._dcc_spec.supports_asset:
                self._asset_tree = self._create_tree()
                layout.addWidget(self._asset_tree, 1)
                self._active_kind = "asset"
            elif self._dcc_spec.supports_shot:
                self._shot_tree = self._create_tree()
                layout.addWidget(self._shot_tree, 1)
                self._active_kind = "shot"

        self._populate()

    def _create_tree(self) -> QtWidgets.QTreeWidget:
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setMinimumWidth(200)
        tree.setAlternatingRowColors(True)
        tree.setUniformRowHeights(True)
        tree.itemSelectionChanged.connect(
            lambda t=tree: self._on_tree_selection_changed(t)
        )
        return tree

    def refresh(self, *, restore_path: Optional[str] = None) -> None:
        path = restore_path if restore_path is not None else self._selection_path()
        self._discovery.invalidate()
        self._populate()
        self._restore_path(path)

    def current_selection(self) -> Optional[WorkfileTreeSelection]:
        return self._selection

    def _tree_for_kind(self, kind: str) -> Optional[QtWidgets.QTreeWidget]:
        if kind == "asset":
            return self._asset_tree
        if kind == "shot":
            return self._shot_tree
        return None

    def _active_tree(self) -> Optional[QtWidgets.QTreeWidget]:
        if self._active_kind is None:
            return None
        return self._tree_for_kind(self._active_kind)

    def _switch_to_kind(self, kind: str) -> None:
        if self._tabs is None:
            return
        if kind == "asset" and self._asset_tree is not None:
            index = self._tabs.indexOf(self._asset_tree)
            if index >= 0:
                self._tabs.setCurrentIndex(index)
        elif kind == "shot" and self._shot_tree is not None:
            index = self._tabs.indexOf(self._shot_tree)
            if index >= 0:
                self._tabs.setCurrentIndex(index)

    def _selection_path(self) -> Optional[str]:
        if not self._selection:
            return None
        sel = self._selection
        if sel.kind == "asset":
            if sel.task:
                return f"asset/{sel.category}/{sel.asset}/{sel.task}"
            return f"asset/{sel.category}/{sel.asset}"
        if sel.task:
            return f"shot/{sel.episode}/{sel.sequence}/{sel.shot}/{sel.task}"
        return f"shot/{sel.episode}/{sel.sequence}/{sel.shot}"

    def _restore_path(self, path: Optional[str]) -> None:
        if not path:
            return
        parts = path.split("/")
        if len(parts) < 3:
            return
        kind = parts[0]
        tree = self._tree_for_kind(kind)
        if tree is None:
            return

        self._switch_to_kind(kind)
        self._active_kind = kind

        if kind == "asset" and len(parts) == 3:
            _kind, category, asset = parts
            category_item = self._find_child_by_text(tree.invisibleRootItem(), category)
            if category_item is None:
                return
            asset_item = self._find_child_by_text(category_item, asset)
            if asset_item is None:
                return
            tree.setCurrentItem(asset_item)
            return
        if kind == "asset" and len(parts) == 4:
            _kind, category, asset, task = parts
            category_item = self._find_child_by_text(tree.invisibleRootItem(), category)
            if category_item is None:
                return
            asset_item = self._find_child_by_text(category_item, asset)
            if asset_item is None:
                return
            self._select_task_child(tree, asset_item, task)
            return
        if kind == "shot" and len(parts) == 4:
            _kind, episode, sequence, shot = parts
            shot_item = self._find_shot_by_path(tree, episode, sequence, shot)
            if shot_item is None:
                return
            tree.setCurrentItem(shot_item)
            return
        if kind == "shot" and len(parts) == 5:
            _kind, episode, sequence, shot, task = parts
            shot_item = self._find_shot_by_path(tree, episode, sequence, shot)
            if shot_item is None:
                return
            self._select_task_child(tree, shot_item, task)

    def _find_shot_by_path(
        self,
        tree: QtWidgets.QTreeWidget,
        episode: str,
        sequence: str,
        shot: str,
    ) -> Optional[QtWidgets.QTreeWidgetItem]:
        episode_item = self._find_child_by_text(tree.invisibleRootItem(), episode)
        if episode_item is None:
            return None
        sequence_item = self._find_child_by_text(episode_item, sequence)
        if sequence_item is None:
            return None
        return self._find_shot_item(sequence_item, shot)

    @staticmethod
    def _find_child_by_text(
        parent: QtWidgets.QTreeWidgetItem, text: str
    ) -> Optional[QtWidgets.QTreeWidgetItem]:
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == text:
                return child
        return None

    @staticmethod
    def _find_shot_item(
        parent: QtWidgets.QTreeWidgetItem, shot: str
    ) -> Optional[QtWidgets.QTreeWidgetItem]:
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole) or {}
            if data.get("kind") == "shot" and data.get("shot") == shot:
                return child
        return None

    @staticmethod
    def _select_task_child(
        tree: QtWidgets.QTreeWidget,
        parent: QtWidgets.QTreeWidgetItem,
        task: str,
    ) -> None:
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole) or {}
            if data.get("kind") == "task" and data.get("task") == task:
                tree.setCurrentItem(child)
                return

    def _folder_item(self, label: str, kind: str) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, {"kind": kind})
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        return item

    def _count_workfiles(self, folder: Path) -> int:
        ext = f".{self._dcc_spec.extension}"
        if not folder.is_dir():
            return 0
        try:
            return sum(
                1
                for entry in folder.iterdir()
                if entry.is_file() and entry.suffix.lower() == ext
            )
        except OSError:
            return 0

    def _task_label(self, task: str, count: int) -> str:
        return f"{task}  ({count})" if count > 1 else task

    def _populate(self) -> None:
        if self._asset_tree is not None:
            self._asset_tree.clear()
        if self._shot_tree is not None:
            self._shot_tree.clear()
        self._selection = None

        if self._asset_tree is not None:
            self._populate_assets(self._asset_tree)
        if self._shot_tree is not None:
            self._populate_shots(self._shot_tree)

    def _populate_assets(self, tree: QtWidgets.QTreeWidget) -> None:
        for category in self._discovery.asset_categories():
            category_item = self._folder_item(category, "category")
            category_item.setData(
                0,
                Qt.UserRole,
                {"kind": "category", "category": category},
            )

            for asset in self._discovery.assets(category):
                asset_item = QtWidgets.QTreeWidgetItem([asset])
                asset_item.setData(
                    0,
                    Qt.UserRole,
                    {
                        "kind": "asset",
                        "category": category,
                        "asset": asset,
                    },
                )

                for task in self._dcc_spec.asset_tasks:
                    work_dir = (
                        self._discovery.context.assets_root
                        / category
                        / asset
                        / "work"
                        / self._dcc
                        / task
                    )
                    count = self._count_workfiles(work_dir)
                    if count == 0:
                        continue
                    task_item = QtWidgets.QTreeWidgetItem(
                        [self._task_label(task, count)]
                    )
                    task_item.setData(
                        0,
                        Qt.UserRole,
                        {
                            "kind": "task",
                            "context": "asset",
                            "category": category,
                            "asset": asset,
                            "task": task,
                        },
                    )
                    asset_item.addChild(task_item)

                category_item.addChild(asset_item)

            if category_item.childCount():
                tree.addTopLevelItem(category_item)

    def _populate_shots(self, tree: QtWidgets.QTreeWidget) -> None:
        for episode in self._discovery.episodes():
            episode_item = self._folder_item(episode, "episode")
            episode_item.setData(
                0,
                Qt.UserRole,
                {"kind": "episode", "episode": episode},
            )

            for sequence in self._discovery.sequences(episode):
                sequence_item = self._folder_item(sequence, "sequence")
                sequence_item.setData(
                    0,
                    Qt.UserRole,
                    {
                        "kind": "sequence",
                        "episode": episode,
                        "sequence": sequence,
                    },
                )

                for shot in self._discovery.shots(episode, sequence):
                    shot_item = QtWidgets.QTreeWidgetItem([shot])
                    shot_item.setData(
                        0,
                        Qt.UserRole,
                        {
                            "kind": "shot",
                            "episode": episode,
                            "sequence": sequence,
                            "shot": shot,
                        },
                    )

                    for task in self._dcc_spec.shot_tasks:
                        work_dir = (
                            self._discovery.context.episodes_root
                            / episode
                            / sequence
                            / shot
                            / "work"
                            / self._dcc
                            / task
                        )
                        count = self._count_workfiles(work_dir)
                        if count == 0:
                            continue
                        task_item = QtWidgets.QTreeWidgetItem(
                            [self._task_label(task, count)]
                        )
                        task_item.setData(
                            0,
                            Qt.UserRole,
                            {
                                "kind": "task",
                                "context": "shot",
                                "episode": episode,
                                "sequence": sequence,
                                "shot": shot,
                                "task": task,
                            },
                        )
                        shot_item.addChild(task_item)

                    sequence_item.addChild(shot_item)

                if sequence_item.childCount():
                    episode_item.addChild(sequence_item)

            if episode_item.childCount():
                tree.addTopLevelItem(episode_item)

    def _on_tab_changed(self, index: int) -> None:
        if self._tabs is None:
            return
        widget = self._tabs.widget(index)
        if widget is self._asset_tree:
            self._active_kind = "asset"
            if self._shot_tree is not None:
                self._shot_tree.clearSelection()
        elif widget is self._shot_tree:
            self._active_kind = "shot"
            if self._asset_tree is not None:
                self._asset_tree.clearSelection()
        self._read_selection_from_active_tree()

    def _on_tree_selection_changed(self, tree: QtWidgets.QTreeWidget) -> None:
        if tree is not self._active_tree():
            return
        self._read_selection_from_active_tree()

    def _read_selection_from_active_tree(self) -> None:
        tree = self._active_tree()
        if tree is None:
            self._selection = None
            self.selection_changed.emit()
            return

        items = tree.selectedItems()
        if not items:
            self._selection = None
            self.selection_changed.emit()
            return

        data = items[0].data(0, Qt.UserRole) or {}
        kind = data.get("kind")

        if kind == "task":
            if data.get("context") == "asset":
                self._selection = WorkfileTreeSelection(
                    kind="asset",
                    task=data["task"],
                    category=data["category"],
                    asset=data["asset"],
                )
            else:
                self._selection = WorkfileTreeSelection(
                    kind="shot",
                    task=data["task"],
                    episode=data["episode"],
                    sequence=data["sequence"],
                    shot=data["shot"],
                )
        elif kind == "asset":
            self._selection = WorkfileTreeSelection(
                kind="asset",
                category=data["category"],
                asset=data["asset"],
            )
        elif kind == "shot":
            self._selection = WorkfileTreeSelection(
                kind="shot",
                episode=data["episode"],
                sequence=data["sequence"],
                shot=data["shot"],
            )
        else:
            self._selection = None

        self.selection_changed.emit()
