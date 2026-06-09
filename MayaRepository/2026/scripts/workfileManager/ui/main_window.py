"""Workfile Manager main window (Maya only)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from genTools.uiUtils import load_qss, maya_main_window, show_singleton_qt_window

from ..core import path_schema as ps
from ..core.context import StudioContext, resolve_context
from ..core.discovery import ShowDiscovery
from ..core.publish_service import PublishService, WorkfileTarget
from ..core.versioning import VersionReservationError, WorkfileEntry
from ..host import MayaHost, MayaHostError
from .qt import Qt, QtCore, QtGui, QtWidgets
from .widgets.publish_form import PublishForm
from .widgets.workfile_table import WorkfileTable
from .widgets.workfile_tree_browser import WorkfileTreeBrowser, WorkfileTreeSelection

logger = logging.getLogger(__name__)


class WorkfileManagerWindow(QtWidgets.QMainWindow):
    """Main workfile manager window."""

    def __init__(
        self,
        context: StudioContext,
        schema: ps.PathSchema,
        host: MayaHost,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._schema = schema
        self._host = host
        self._discovery = ShowDiscovery(context)
        self._service = PublishService(context, schema)

        self.setWindowTitle(f"Workfile Manager — {context.show}")
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(980, 620)

        self._build_ui()
        self._connect_signals()
        self._refresh_all()

    @property
    def host(self) -> MayaHost:
        return self._host

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._build_header())

        splitter = QtWidgets.QSplitter(Qt.Horizontal)

        self._workfile_tree = WorkfileTreeBrowser(
            self._discovery, self._schema, dcc=self._host.name
        )
        splitter.addWidget(self._workfile_tree)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._table = WorkfileTable()
        right_layout.addWidget(self._table, 1)

        self._form = PublishForm(
            schema=self._schema,
            dcc=self._host.name,
            default_variant=self._schema.default_variant,
        )
        right_layout.addWidget(self._form)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 720])

        layout.addWidget(splitter, 1)

        self.setCentralWidget(central)

        self._status = self.statusBar()
        self._status.showMessage("Ready.")

    def _build_header(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        title = QtWidgets.QLabel(f"<b>Show:</b> {self._context.show}")
        host = QtWidgets.QLabel(f"<b>Host:</b> {self._host.label}")
        user = QtWidgets.QLabel(f"<b>User:</b> {self._context.username}")
        drive = QtWidgets.QLabel(f"<b>Drive:</b> {self._context.base_show_dir}")
        for w in (title, host, user, drive):
            w.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(host)
        layout.addStretch(1)
        layout.addWidget(user)
        layout.addStretch(1)
        layout.addWidget(drive)
        return frame

    def _connect_signals(self) -> None:
        self._workfile_tree.selection_changed.connect(self._on_tree_selection)
        self._form.target_changed.connect(self._refresh_all)
        self._form.publish_requested.connect(self._on_publish)
        self._form.open_requested.connect(self._on_open_selected)
        self._form.refresh_requested.connect(self._on_refresh)
        self._table.open_requested.connect(self._open_entry)
        self._table.selection_changed.connect(self._on_table_selection_changed)

    def _tree_selection(self) -> Optional[WorkfileTreeSelection]:
        return self._workfile_tree.current_selection()

    def _build_target(
        self,
        *,
        variant_override: Optional[str] = None,
        require_task_leaf: bool = False,
        warn: bool = False,
    ) -> Optional[WorkfileTarget]:
        selection = self._tree_selection()
        if selection is None:
            return None
        if require_task_leaf and not selection.task:
            return None

        if selection.task:
            task = selection.task
        else:
            task = self._form.task()

        if not task:
            if warn:
                self._warn("Invalid target", "Select a workfile type.")
            return None

        variant = variant_override if variant_override is not None else self._form.variant()
        try:
            cleaned_variant = ps.normalize_variant(variant, self._schema)
        except ValueError as exc:
            if warn:
                self._warn("Invalid variant", str(exc))
            return None

        allowed = self._schema.get_dcc(self._host.name).tasks_for(selection.kind)
        if task not in allowed:
            if warn:
                self._warn("Invalid target", f"Unknown workfile type {task!r}.")
            return None

        category = selection.category
        asset = selection.asset
        episode = selection.episode
        sequence = selection.sequence
        shot = selection.shot

        if selection.kind == "asset":
            if not category:
                return None
            asset_raw = asset if asset else self._form.top_level_name()
            if not asset_raw.strip():
                if warn:
                    self._warn("Invalid target", "Asset name is required.")
                return None
            try:
                asset = ps.normalize_asset_name(asset_raw)
            except ValueError as exc:
                if warn:
                    self._warn("Invalid target", str(exc))
                return None
        elif selection.kind == "shot":
            if not (episode and sequence and shot):
                if warn:
                    self._warn(
                        "Invalid target",
                        "Select a production-created shot in the tree before saving."
                    )
                return None
            try:
                shot = ps.normalize_shot_name(shot)
            except ValueError as exc:
                if warn:
                    self._warn("Invalid target", str(exc))
                return None
        else:
            return None

        return WorkfileTarget(
            kind=selection.kind,
            dcc=self._host.name,
            task=task,
            variant=cleaned_variant,
            category=category,
            asset=asset,
            episode=episode,
            sequence=sequence,
            shot=shot,
        )

    def _browse_target(self) -> Optional[WorkfileTarget]:
        return self._build_target(require_task_leaf=True)

    def _publish_target(
        self,
        *,
        variant_override: Optional[str] = None,
        warn: bool = False,
    ) -> Optional[WorkfileTarget]:
        return self._build_target(variant_override=variant_override, warn=warn)

    @staticmethod
    def _restore_path_for_target(target: WorkfileTarget) -> str:
        if target.kind == "asset":
            return f"asset/{target.category}/{target.asset}/{target.task}"
        return f"shot/{target.episode}/{target.sequence}/{target.shot}/{target.task}"

    def _on_tree_selection(self) -> None:
        selection = self._tree_selection()
        if selection is None:
            self._form.set_context(None)
            self._form.set_name_context(None, [])
            self._refresh_all()
            return

        self._form.set_context(selection.kind)
        if selection.kind == "asset" and selection.category:
            self._form.set_name_context(
                "asset", self._discovery.assets(selection.category)
            )
            if selection.asset:
                self._form.set_top_level_name(selection.asset)
        elif (
            selection.kind == "shot"
            and selection.episode
            and selection.sequence
        ):
            self._form.set_name_context("shot", [])
        if selection.task:
            self._form.set_task(selection.task)
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        browse_target = self._browse_target()
        publish_target = self._publish_target()

        if browse_target is None:
            self._table.set_entries([])
            self._form.set_open_enabled(False)
            selection = self._tree_selection()
            if selection is None:
                self._status.showMessage(
                    "Select a category in Assets or a sequence in Episodes, "
                    "then set name, workfile type, and variant."
                )
            elif not selection.task:
                if selection.kind == "asset" and not selection.asset:
                    self._status.showMessage(
                        "Set asset name, workfile type, and variant to save, "
                        "or select a workfile type in the tree to browse versions."
                    )
                elif selection.kind == "shot" and not selection.shot:
                    self._status.showMessage(
                        "Select a production-created shot in the tree before saving."
                    )
                else:
                    self._status.showMessage(
                        "Select a workfile type in the tree to browse versions, "
                        "or pick a type below to save."
                    )
            else:
                self._status.showMessage(
                    "Select a workfile type in the tree, or pick a type below to save."
                )
        else:
            entries = self._service.list_for_target(
                browse_target, include_all_variants=True
            )
            self._table.set_entries(entries)
            self._form.set_open_enabled(bool(entries))
            folder = self._service.workfile_dir(browse_target)
            variant_entries = [
                e for e in entries if e.variant == browse_target.variant
            ]
            next_version = (
                (max(e.version for e in variant_entries) + 1)
                if variant_entries
                else 1
            )
            self._status.showMessage(
                f"{len(entries)} workfile(s) in {folder} — next "
                f"{browse_target.variant} save: v{next_version:03d}"
            )

        self._form.set_publish_enabled(publish_target is not None)

    def _on_table_selection_changed(self, entry: Optional[WorkfileEntry]) -> None:
        self._form.set_open_enabled(entry is not None)

    def _confirm_publish_path(self, path: Path) -> bool:
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Question)
        box.setWindowTitle("Confirm save path")
        box.setText("Save this workfile?")
        box.setInformativeText(f"The workfile will be saved here:\n\n{path}")
        box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        box.setDefaultButton(QtWidgets.QMessageBox.Yes)
        try:
            box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        except AttributeError:
            pass

        exec_fn = getattr(box, "exec", None) or getattr(box, "exec_")
        return exec_fn() == QtWidgets.QMessageBox.Yes

    def _on_publish(self, variant: str) -> None:
        target = self._publish_target(variant_override=variant, warn=True)
        if target is None:
            return
        try:
            reserved = self._service.reserve_publish_path(target)
        except MayaHostError as exc:
            self._warn("Save failed", str(exc))
            return
        except VersionReservationError as exc:
            self._warn("Could not reserve version", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected save failure")
            self._warn("Save failed", str(exc))
            return

        if not self._confirm_publish_path(reserved):
            self._service.release_reserved_path(reserved)
            self._status.showMessage("Save cancelled.", 4000)
            return

        try:
            saved = self._service.publish_reserved(self._host, reserved)
        except MayaHostError as exc:
            self._warn("Save failed", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected save failure")
            self._warn("Save failed", str(exc))
            return

        self._status.showMessage(f"Saved {saved}", 8000)
        self._workfile_tree.refresh(
            restore_path=self._restore_path_for_target(target)
        )
        selection = self._tree_selection()
        if selection and selection.kind == "asset" and selection.category:
            self._form.set_name_context(
                "asset", self._discovery.assets(selection.category)
            )
        elif (
            selection
            and selection.kind == "shot"
            and selection.episode
            and selection.sequence
        ):
            self._form.set_name_context("shot", [])
        if target.kind == "asset" and target.asset:
            self._form.set_top_level_name(target.asset)
        self._on_tree_selection()

    def _on_open_selected(self) -> None:
        entry = self._table.current_entry()
        if entry is None:
            return
        self._open_entry(entry)

    def _open_entry(self, entry: WorkfileEntry) -> None:
        if self._host.is_modified():
            confirm = QtWidgets.QMessageBox.question(
                self,
                "Unsaved changes",
                "The current scene has unsaved changes. Open the selected workfile anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if confirm != QtWidgets.QMessageBox.Yes:
                return
        try:
            self._service.open_workfile(self._host, entry.path)
        except MayaHostError as exc:
            self._warn("Open failed", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected open failure")
            self._warn("Open failed", str(exc))
            return
        self._status.showMessage(f"Opened {entry.path}", 8000)

    def _on_refresh(self) -> None:
        selection = self._tree_selection()
        top_level_name = self._form.top_level_name()
        self._workfile_tree.refresh()
        if selection and selection.kind == "asset" and selection.category:
            self._form.set_name_context(
                "asset", self._discovery.assets(selection.category)
            )
        elif (
            selection
            and selection.kind == "shot"
            and selection.episode
            and selection.sequence
        ):
            self._form.set_name_context("shot", [])
        if top_level_name and selection and selection.kind == "asset":
            self._form.set_top_level_name(top_level_name)
        self._refresh_all()

    def _warn(self, title: str, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, title, message)


def _load_default_schema() -> ps.PathSchema:
    return ps.load_schema(ps.default_schema_path())


def show() -> WorkfileManagerWindow:  # pragma: no cover - exercised inside Maya
    """Shelf entry point: open (or focus) the Workfile Manager window."""
    parent = maya_main_window()

    def factory() -> WorkfileManagerWindow:
        context = resolve_context()
        schema = _load_default_schema()
        host = MayaHost()
        return WorkfileManagerWindow(context, schema, host, parent=parent)

    return show_singleton_qt_window(
        "workfile_manager",
        factory,
        host="maya",
        parent=parent,
    )


main = show
