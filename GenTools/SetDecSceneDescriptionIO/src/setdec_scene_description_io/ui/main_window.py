"""SetDec scene-description IO window (shared by Maya and Unreal).

Layout mirrors Workfile Manager / Asset Manager:

* Read-only header (show, host, user, drive)
* Left tree: environments → variants
* Right: version table + import/export form
* Status bar
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from ..adapters import SceneAdapter, build_adapter
from ..core.context import ContextError, StudioContext, resolve_context
from ..core.discovery import EnvDiscovery
from ..core.paths import SceneSchema, load_scene_schema
from ..core.scene_service import SceneDescriptionService, SceneTarget
from ..core.versioning import SceneDescriptionEntry
from .qt import Qt, QtWidgets
from .widgets.env_tree_browser import EnvTreeBrowser, EnvTreeSelection
from .widgets.scene_form import SceneForm
from .widgets.version_table import VersionTable

logger = logging.getLogger(__name__)


class SceneDescriptionWindow(QtWidgets.QMainWindow):
    """Main window for importing and exporting SetDec scene descriptions."""

    def __init__(
        self,
        context: StudioContext,
        schema: SceneSchema,
        adapter: SceneAdapter,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._schema = schema
        self._adapter = adapter
        self._discovery = EnvDiscovery(context, schema)
        self._service = SceneDescriptionService(context, adapter, schema)

        self.setWindowTitle(f"SetDec Scene Description — {context.show}")
        self.setStyleSheet(_load_stylesheet())
        self.resize(980, 620)

        self._build_ui()
        self._connect_signals()
        self._refresh_all()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._build_header())

        splitter = QtWidgets.QSplitter(Qt.Horizontal)

        self._env_tree = EnvTreeBrowser(self._discovery)
        splitter.addWidget(self._env_tree)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._table = VersionTable()
        right_layout.addWidget(self._table, 1)

        self._form = SceneForm(schema=self._schema)
        right_layout.addWidget(self._form)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 720])

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
        for widget in (title, host, user, drive):
            widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(host)
        layout.addStretch(1)
        layout.addWidget(user)
        layout.addStretch(1)
        layout.addWidget(drive)
        return frame

    def _connect_signals(self) -> None:
        self._env_tree.selection_changed.connect(self._on_tree_selection)
        self._form.target_changed.connect(self._refresh_all)
        self._form.export_requested.connect(self._on_export)
        self._form.import_requested.connect(self._on_import_selected)
        self._form.refresh_requested.connect(self._on_refresh)
        self._table.selection_changed.connect(self._on_table_selection)
        self._table.import_requested.connect(self._import_entry)

    def _tree_selection(self) -> Optional[EnvTreeSelection]:
        return self._env_tree.current_selection()

    def _browse_target(self) -> Optional[SceneTarget]:
        selection = self._tree_selection()
        if selection is None or not selection.variant:
            return None
        return SceneTarget(env=selection.env, variant=selection.variant)

    def _export_target(self, *, warn: bool = False) -> Optional[SceneTarget]:
        selection = self._tree_selection()
        env_raw = self._form.environment()
        variant_raw = self._form.variant()

        if selection and selection.env and not env_raw:
            env_raw = selection.env
        if selection and selection.variant and not variant_raw:
            variant_raw = selection.variant

        target = self._service.build_target(env_raw, variant_raw, warn=warn)
        if target is None and warn:
            self._warn("Invalid target", "Set an environment name and variant to export.")
        return target

    def _on_tree_selection(self) -> None:
        selection = self._tree_selection()
        self._form.set_environments(self._discovery.environments())
        if selection is None:
            self._refresh_all()
            return
        self._form.set_environment(selection.env)
        if selection.variant:
            self._form.set_variant(selection.variant)
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_table()
        export_target = self._export_target()
        self._form.set_export_enabled(export_target is not None)
        if export_target is not None:
            self._form.set_next_version(self._service.next_version_label(export_target))

    def _refresh_table(self) -> None:
        browse_target = self._browse_target()
        if browse_target is None:
            self._table.set_entries([])
            self._form.set_import_enabled(False)
            selection = self._tree_selection()
            if selection is None:
                self._status.showMessage(
                    "Select an environment in the tree, then set name and variant to export."
                )
            elif not selection.variant:
                self._status.showMessage(
                    "Select a variant in the tree to browse versions, "
                    "or set a variant below to export."
                )
            else:
                self._status.showMessage("Select a variant in the tree to browse versions.")
            return

        entries = self._service.list_for_target(browse_target)
        self._table.set_entries(entries)
        self._form.set_import_enabled(bool(entries))
        folder = self._service.paths.variant_folder(
            self._context.show, browse_target.env, browse_target.variant
        )
        next_label = self._service.next_version_label(browse_target)
        self._form.set_next_version(next_label)
        self._status.showMessage(
            f"{len(entries)} scene description(s) in {folder} — next export: {next_label}"
        )

    def _on_table_selection(self, entry: Optional[SceneDescriptionEntry]) -> None:
        self._form.set_import_enabled(entry is not None)

    def _on_export(self) -> None:
        target = self._export_target(warn=True)
        if target is None:
            return

        next_label = self._service.next_version_label(target)
        usd_path = self._service.paths.scene_description_file(
            self._context.show, target.env, target.variant, next_label
        )

        if not self._confirm_action(
            "Export scene description",
            f"Export the current scene to:\n\n{usd_path}",
        ):
            self._status.showMessage("Export cancelled.", 4000)
            return

        try:
            saved = self._service.export_scene(target)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Export failed")
            self._warn("Export failed", str(exc))
            return

        if saved is None:
            self._warn("Export failed", "Nothing was written. Is the ENV hierarchy present?")
            return

        self._status.showMessage(f"Exported {saved}", 8000)
        restore = f"{target.env}/{target.variant}"
        self._env_tree.refresh(restore_path=restore)
        self._form.set_environment(target.env)
        self._form.set_variant(target.variant)
        self._on_tree_selection()

    def _on_import_selected(self) -> None:
        entry = self._table.current_entry()
        if entry is None:
            return
        self._import_entry(entry)

    def _import_entry(self, entry: SceneDescriptionEntry) -> None:
        if not self._confirm_action(
            "Import scene description",
            f"Rebuild the scene from:\n\n{entry.path}",
        ):
            self._status.showMessage("Import cancelled.", 4000)
            return
        try:
            self._service.import_scene(entry)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Import failed")
            self._warn("Import failed", str(exc))
            return
        self._status.showMessage(f"Imported {entry.path}", 8000)

    def _on_refresh(self) -> None:
        env = self._form.environment()
        variant = self._form.variant()
        self._env_tree.refresh()
        self._form.set_environments(self._discovery.environments())
        if env:
            self._form.set_environment(env)
        if variant:
            self._form.set_variant(variant)
        self._refresh_all()

    def _confirm_action(self, title: str, message: str) -> bool:
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Question)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        box.setDefaultButton(QtWidgets.QMessageBox.Yes)
        try:
            box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        except AttributeError:
            pass
        exec_fn = getattr(box, "exec", None) or getattr(box, "exec_")
        return exec_fn() == QtWidgets.QMessageBox.Yes

    def _warn(self, title: str, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, title, message)


# ---------------------------------------------------------------------------
# Helpers


def _load_stylesheet() -> str:
    try:
        from genTools.uiUtils import load_qss

        return load_qss("dark.qss")
    except Exception:
        return ""


SETDEC_WINDOW_KEY = "setdec_scene_description"


def show(
    host: str = "standalone",
    *,
    cli_show: Optional[str] = None,
    cli_base_show_dir: Optional[str] = None,
    allow_cli_override: bool = False,
) -> SceneDescriptionWindow:
    """Open (or focus) the SetDec scene-description window for the given host."""
    from genTools.studio_python_path import ensure_gen_tools_shared

    ensure_gen_tools_shared()
    from studioUiUtils import maya_main_window, show_singleton_qt_window

    if host == "maya":
        parent = maya_main_window()
        qt_host = "maya"
    elif host == "unreal":
        parent = None
        qt_host = "unreal"
    else:
        parent = None
        qt_host = "standalone"

    def factory() -> SceneDescriptionWindow:
        try:
            return _make_window(
                host if host in ("maya", "unreal") else "standalone",
                cli_show=cli_show,
                cli_base_show_dir=cli_base_show_dir,
                allow_cli_override=allow_cli_override,
                parent=parent if host == "maya" else None,
            )
        except ContextError as exc:
            QtWidgets.QMessageBox.critical(
                parent if host == "maya" else None,
                "SetDec Scene Description",
                str(exc),
            )
            raise

    return show_singleton_qt_window(
        SETDEC_WINDOW_KEY,
        factory,
        host=qt_host,
        parent=parent,
    )


def show_in_maya() -> SceneDescriptionWindow:  # pragma: no cover
    """Backward-compatible Maya entry point."""
    return show(host="maya")


def show_in_unreal() -> SceneDescriptionWindow:  # pragma: no cover
    """Backward-compatible Unreal entry point."""
    return show(host="unreal")


def _make_window(
    host: str,
    *,
    cli_show: Optional[str] = None,
    cli_base_show_dir: Optional[str] = None,
    allow_cli_override: bool = False,
    parent: Optional[QtWidgets.QWidget] = None,
) -> SceneDescriptionWindow:
    context = resolve_context(
        cli_show=cli_show,
        cli_base_show_dir=cli_base_show_dir,
        allow_cli_override=allow_cli_override,
    )
    schema = load_scene_schema()
    adapter = build_adapter(host)
    return SceneDescriptionWindow(context, schema, adapter, parent=parent)


def show_standalone(
    *,
    cli_show: Optional[str] = None,
    cli_base_show_dir: Optional[str] = None,
) -> int:
    """Run the window with its own QApplication (local UI dev)."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    try:
        window = _make_window(
            "standalone",
            cli_show=cli_show,
            cli_base_show_dir=cli_base_show_dir,
            allow_cli_override=True,
        )
    except ContextError as exc:
        QtWidgets.QMessageBox.critical(
            None,
            "SetDec Scene Description",
            str(exc),
        )
        return 1
    window.show()
    return app.exec()
