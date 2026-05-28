"""Workfile Publisher main window.

The window is the only widget the host launcher cares about. It owns:

* The resolved :class:`StudioContext` (read-only header).
* A :class:`PublishService` (versioning + path build).
* A :class:`HostAdapter` (DCC-specific verbs).
* Workfile tree browser, workfile table, and publish form (split layout).

Two convenience constructors:

* :func:`show_in_maya` - parents the window to Maya's main window and keeps
  a strong reference so Maya's GC doesn't collect it.
* :func:`show_standalone` - boots its own ``QApplication`` for local dev.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..adapters import HostAdapter, HostAdapterError, build_adapter
from ..core import path_schema as ps
from ..core.context import StudioContext, resolve_context
from ..core.discovery import ShowDiscovery
from ..core.publish_service import PublishService, WorkfileTarget
from ..core.versioning import VersionReservationError, WorkfileEntry
from .qt import Qt, QtCore, QtGui, QtWidgets
from .widgets.publish_form import PublishForm
from .widgets.workfile_table import WorkfileTable
from .widgets.workfile_tree_browser import WorkfileTreeBrowser

logger = logging.getLogger(__name__)


class WorkfilePublisherWindow(QtWidgets.QMainWindow):
    """Main publisher window."""

    def __init__(
        self,
        context: StudioContext,
        schema: ps.PathSchema,
        adapter: HostAdapter,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._schema = schema
        self._adapter = adapter
        self._discovery = ShowDiscovery(context)
        self._service = PublishService(context, schema)

        self.setWindowTitle(f"Workfile Publisher — {context.show}")
        self.setStyleSheet(self._load_maya_stylesheet())
        self.resize(980, 620)

        self._build_ui()
        self._connect_signals()
        self._refresh_table()

    # ------------------------------------------------------------- access
    @property
    def adapter(self) -> HostAdapter:
        return self._adapter

    @staticmethod
    def _load_maya_stylesheet() -> str:
        try:
            from genTools.uiUtils import load_qss

            return load_qss("dark.qss")
        except Exception:
            return ""

    # -------------------------------------------------------------- build
    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._build_header())

        splitter = QtWidgets.QSplitter(Qt.Horizontal)

        self._workfile_tree = WorkfileTreeBrowser(
            self._discovery, self._schema, dcc=self._adapter.name
        )
        splitter.addWidget(self._workfile_tree)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._table = WorkfileTable()
        right_layout.addWidget(self._table, 1)

        self._form = PublishForm(default_variant=self._schema.default_variant)
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
        host = QtWidgets.QLabel(f"<b>Host:</b> {self._adapter.label}")
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
        self._workfile_tree.selection_changed.connect(self._refresh_table)
        self._form.publish_requested.connect(self._on_publish)
        self._form.open_requested.connect(self._on_open_selected)
        self._form.refresh_requested.connect(self._on_refresh)
        self._table.open_requested.connect(self._open_entry)
        self._table.selection_changed.connect(self._on_table_selection_changed)

    # ---------------------------------------------------------- helpers
    def _target_for_action(self, variant_override: Optional[str] = None) -> Optional[WorkfileTarget]:
        base = self._workfile_tree.current_target()
        if base is None:
            return None
        variant = variant_override or self._form.variant()
        try:
            cleaned = ps.normalize_variant(variant, self._schema)
        except ValueError as exc:
            self._warn("Invalid variant", str(exc))
            return None
        return WorkfileTarget(
            kind=base.kind,
            dcc=base.dcc,
            task=base.task,
            variant=cleaned,
            category=base.category,
            asset=base.asset,
            episode=base.episode,
            sequence=base.sequence,
            shot=base.shot,
        )

    def _refresh_table(self) -> None:
        target = self._target_for_action()
        if target is None:
            self._table.set_entries([])
            self._form.set_publish_enabled(False)
            self._form.set_open_enabled(False)
            self._status.showMessage(
                "Select a task in the show tree (e.g. episodes → … → sh010 → layout)."
            )
            return

        entries = self._service.list_for_target(target, include_all_variants=True)
        self._table.set_entries(entries)
        self._form.set_publish_enabled(True)
        self._form.set_open_enabled(bool(entries))
        folder = self._service.workfile_dir(target)
        variant_entries = [e for e in entries if e.variant == target.variant]
        next_version = (max(e.version for e in variant_entries) + 1) if variant_entries else 1
        self._status.showMessage(
            f"{len(entries)} workfile(s) in {folder} — next "
            f"{target.variant} publish: v{next_version:03d}"
        )

    def _on_table_selection_changed(self, entry: Optional[WorkfileEntry]) -> None:
        self._form.set_open_enabled(entry is not None)

    # ---------------------------------------------------------- actions
    def _on_publish(self, variant: str) -> None:
        target = self._target_for_action(variant_override=variant)
        if target is None:
            return
        try:
            saved = self._service.publish(self._adapter, target)
        except HostAdapterError as exc:
            self._warn("Publish failed", str(exc))
            return
        except VersionReservationError as exc:
            self._warn("Could not reserve version", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected publish failure")
            self._warn("Publish failed", str(exc))
            return

        self._status.showMessage(f"Published {saved}", 8000)
        self._refresh_table()

    def _on_open_selected(self) -> None:
        entry = self._table.current_entry()
        if entry is None:
            return
        self._open_entry(entry)

    def _open_entry(self, entry: WorkfileEntry) -> None:
        if self._adapter.is_modified():
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
            self._service.open_workfile(self._adapter, entry.path)
        except HostAdapterError as exc:
            self._warn("Open failed", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected open failure")
            self._warn("Open failed", str(exc))
            return
        self._status.showMessage(f"Opened {entry.path}", 8000)

    def _on_refresh(self) -> None:
        self._workfile_tree.refresh()
        self._refresh_table()

    # ---------------------------------------------------------- close
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        stop = getattr(self._adapter, "stop", None)
        if callable(stop):
            try:
                stop()
            except Exception:  # pragma: no cover - defensive
                logger.exception("adapter.stop() raised")
        super().closeEvent(event)

    # ---------------------------------------------------------- dialogs
    def _warn(self, title: str, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, title, message)


# ---------------------------------------------------------------------------
# Convenience constructors


def _load_default_schema() -> ps.PathSchema:
    return ps.load_schema(ps.default_schema_path())


def _maya_main_window():  # pragma: no cover - only runs in Maya
    """Return Maya's main window as a QWidget for parenting."""
    try:
        import maya.OpenMayaUI as omui
        from shiboken6 import wrapInstance  # type: ignore[import-not-found]

        ptr = omui.MQtUtil.mainWindow()
        if ptr is None:
            return None
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        pass
    try:
        import maya.OpenMayaUI as omui
        from shiboken2 import wrapInstance  # type: ignore[import-not-found]

        ptr = omui.MQtUtil.mainWindow()
        if ptr is None:
            return None
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        return None


_MAYA_WINDOW_REF: Optional[WorkfilePublisherWindow] = None


def show_in_maya() -> WorkfilePublisherWindow:  # pragma: no cover - exercised inside Maya
    """Open the publisher parented to Maya's main window."""
    global _MAYA_WINDOW_REF
    context = resolve_context()
    schema = _load_default_schema()
    adapter = build_adapter("maya")
    parent = _maya_main_window()
    window = WorkfilePublisherWindow(context, schema, adapter, parent=parent)
    window.setAttribute(Qt.WA_DeleteOnClose, True)
    window.show()
    _MAYA_WINDOW_REF = window
    return window


def show_standalone(
    host: str,
    *,
    cli_show: Optional[str] = None,
    cli_base_show_dir: Optional[str] = None,
) -> int:
    """Run the publisher with its own QApplication.

    Used for local UI development.

    Returns:
        The Qt event loop exit code.
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    try:
        context = resolve_context(
            cli_show=cli_show,
            cli_base_show_dir=cli_base_show_dir,
            allow_cli_override=host == "standalone",
        )
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            None,
            "Workfile Publisher",
            f"Cannot start the publisher:\n\n{exc}",
        )
        return 1

    try:
        schema = _load_default_schema()
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            None, "Workfile Publisher", f"Bad path schema:\n\n{exc}"
        )
        return 1

    try:
        adapter = build_adapter(host)
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            None, "Workfile Publisher", f"Cannot build host adapter:\n\n{exc}"
        )
        return 1

    # Start AE heartbeat if applicable.
    start = getattr(adapter, "start", None)
    if callable(start):
        try:
            start()
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("adapter.start() failed: %s", exc)

    window = WorkfilePublisherWindow(context, schema, adapter)
    window.show()
    return app.exec()
