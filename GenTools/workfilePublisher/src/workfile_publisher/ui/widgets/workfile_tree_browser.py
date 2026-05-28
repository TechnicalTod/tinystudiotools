"""Workfile tree browser (show folders → … → task), matching pipeline layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ...core import path_schema as ps
from ...core.discovery import ShowDiscovery
from ...core.publish_service import WorkfileTarget
from ..qt import Qt, QtWidgets, Signal


@dataclass(frozen=True)
class WorkfileTreeSelection:
    """A selectable task leaf in the workfile tree."""

    kind: str  # "asset" | "shot"
    task: str
    category: Optional[str] = None
    asset: Optional[str] = None
    episode: Optional[str] = None
    sequence: Optional[str] = None
    shot: Optional[str] = None

    def to_target(self, dcc: str, default_variant: str) -> WorkfileTarget:
        return WorkfileTarget(
            kind=self.kind,
            dcc=dcc,
            task=self.task,
            variant=default_variant,
            category=self.category,
            asset=self.asset,
            episode=self.episode,
            sequence=self.sequence,
            shot=self.shot,
        )


class WorkfileTreeBrowser(QtWidgets.QWidget):
    """Tree rooted at show folders (``assets``, ``episodes``) down to task leaves."""

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

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QtWidgets.QLabel("Show")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

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

    def current_selection(self) -> Optional[WorkfileTreeSelection]:
        return self._selection

    def current_target(self) -> Optional[WorkfileTarget]:
        if self._selection is None:
            return None
        return self._selection.to_target(self._dcc, self._schema.default_variant)

    def _selection_path(self) -> Optional[str]:
        if not self._selection:
            return None
        sel = self._selection
        if sel.kind == "asset":
            return f"asset/{sel.category}/{sel.asset}/{sel.task}"
        return f"shot/{sel.episode}/{sel.sequence}/{sel.shot}/{sel.task}"

    def _restore_path(self, path: Optional[str]) -> None:
        if not path:
            return
        parts = path.split("/")
        if len(parts) < 4:
            return
        kind = parts[0]
        if kind == "asset" and len(parts) == 4:
            _kind, category, asset, task = parts
            assets_root = self._find_child_by_text(
                self._tree.invisibleRootItem(), "assets"
            )
            if assets_root is None:
                return
            category_item = self._find_child_by_text(assets_root, category)
            if category_item is None:
                return
            asset_item = self._find_child_by_text(category_item, asset)
            if asset_item is None:
                return
            self._select_task_child(asset_item, task)
            return
        if kind == "shot" and len(parts) == 5:
            _kind, episode, sequence, shot, task = parts
            episodes_root = self._find_child_by_text(
                self._tree.invisibleRootItem(), "episodes"
            )
            if episodes_root is None:
                return
            episode_item = self._find_child_by_text(episodes_root, episode)
            if episode_item is None:
                return
            sequence_item = self._find_child_by_text(episode_item, sequence)
            if sequence_item is None:
                return
            shot_item = self._find_shot_item(sequence_item, shot)
            if shot_item is None:
                return
            self._select_task_child(shot_item, task)

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

    def _select_task_child(self, parent: QtWidgets.QTreeWidgetItem, task: str) -> None:
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole) or {}
            if data.get("kind") == "task" and data.get("task") == task:
                self._tree.setCurrentItem(child)
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

    def _task_label(self, task: str, folder: Path) -> str:
        count = self._count_workfiles(folder)
        return f"{task}  ({count})" if count else task

    def _populate(self) -> None:
        self._tree.clear()
        self._selection = None

        if self._dcc_spec.supports_asset:
            self._populate_assets()

        if self._dcc_spec.supports_shot:
            self._populate_shots()

    def _populate_assets(self) -> None:
        assets_root = self._folder_item("assets", "assets_root")

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
                asset_item.setFlags(asset_item.flags() & ~Qt.ItemIsSelectable)

                for task in self._dcc_spec.asset_tasks:
                    work_dir = (
                        self._discovery.context.assets_root
                        / category
                        / asset
                        / "work"
                        / self._dcc
                        / task
                    )
                    task_item = QtWidgets.QTreeWidgetItem(
                        [self._task_label(task, work_dir)]
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

                if asset_item.childCount():
                    category_item.addChild(asset_item)

            if category_item.childCount():
                assets_root.addChild(category_item)

        if assets_root.childCount():
            self._tree.addTopLevelItem(assets_root)
            assets_root.setExpanded(True)

    def _populate_shots(self) -> None:
        episodes_root = self._folder_item("episodes", "episodes_root")

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
                    shot_item.setFlags(shot_item.flags() & ~Qt.ItemIsSelectable)

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
                        task_item = QtWidgets.QTreeWidgetItem(
                            [self._task_label(task, work_dir)]
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

                    if shot_item.childCount():
                        sequence_item.addChild(shot_item)

                if sequence_item.childCount():
                    episode_item.addChild(sequence_item)

            if episode_item.childCount():
                episodes_root.addChild(episode_item)

        if episodes_root.childCount():
            self._tree.addTopLevelItem(episodes_root)
            episodes_root.setExpanded(True)

    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            self._selection = None
            self.selection_changed.emit()
            return

        data = items[0].data(0, Qt.UserRole) or {}
        if data.get("kind") != "task":
            self._selection = None
            self.selection_changed.emit()
            return

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
        self.selection_changed.emit()
