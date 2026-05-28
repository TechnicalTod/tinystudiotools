"""Asset Manager main window (Maya only)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

from ..checks.runner import CheckRunner
from ..core.asset_name import normalize_asset_name
from ..core.context import StudioContext, resolve_context
from ..core.discovery import AssetDiscovery
from ..core.paths import preview_path_for_version, scene_path_for_version
from ..core.publish_service import PublishService
from ..core.schema import AssetPublishSchema, load_schema
from ..core.target import AssetPublishTarget
from ..core.variant import normalize_variant
from ..core.versioning import PublishEntry, VersionReservationError
from ..exporters.base import ExportError
from ..host import MayaHost
from genTools.uiUtils import load_qss
from .qt import Qt, QtWidgets
from .widgets.asset_tree_browser import AssetTreeBrowser
from .widgets.precheck_panel import PrecheckPanel
from .widgets.publish_form import PublishForm
from .widgets.publish_table import PublishTable
from .widgets.screenshot_panel import ScreenshotPanel

logger = logging.getLogger(__name__)


class AssetManagerWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        context: StudioContext,
        schema: AssetPublishSchema,
        host: MayaHost,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._schema = schema
        self._host = host
        self._discovery = AssetDiscovery(context, schema)
        self._service = PublishService(context, schema)
        self._checks = CheckRunner(schema, host=host)

        self.setWindowTitle(f"Asset Manager — {context.show}")
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(980, 620)

        self._build_ui()
        self._connect_signals()
        self._refresh_all()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        outer.addWidget(self._build_header())

        splitter = QtWidgets.QSplitter(Qt.Horizontal)

        self._asset_tree = AssetTreeBrowser(self._discovery)
        splitter.addWidget(self._asset_tree)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        mid = QtWidgets.QHBoxLayout()
        self._precheck_panel = PrecheckPanel()
        self._screenshot_panel = ScreenshotPanel()
        mid.addWidget(self._precheck_panel, 1)
        mid.addWidget(self._screenshot_panel, 1)
        right_layout.addLayout(mid)

        self._table = PublishTable()
        right_layout.addWidget(self._table, 1)

        self._form = PublishForm(schema=self._schema, default_variant=self._schema.default_variant)
        right_layout.addWidget(self._form)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 720])

        outer.addWidget(splitter, 1)
        self.setCentralWidget(central)
        self._status = self.statusBar()

    def _build_header(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        for text in (
            f"<b>Show:</b> {self._context.show}",
            f"<b>Host:</b> {self._host.label}",
            f"<b>User:</b> {self._context.username}",
            f"<b>Drive:</b> {self._context.base_show_dir}",
        ):
            label = QtWidgets.QLabel(text)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(label)
            layout.addStretch(1)
        return frame

    def _connect_signals(self) -> None:
        self._asset_tree.selection_changed.connect(self._on_tree_selection)
        self._form.target_changed.connect(self._refresh_all)
        self._form.publish_requested.connect(self._on_publish)
        self._form.load_requested.connect(self._on_load_selected)
        self._form.open_requested.connect(self._on_open_selected)
        self._form.refresh_requested.connect(self._on_refresh)
        self._table.selection_changed.connect(self._on_table_selection)
        self._table.open_requested.connect(self._open_entry)
        self._screenshot_panel.capture_btn.clicked.connect(self._on_capture)
        self._precheck_panel.run_requested.connect(self._on_run_checks)

    def _on_tree_selection(self) -> None:
        selection = self._asset_tree.current_selection()
        if selection is None:
            self._form.set_category(None, [])
            self._refresh_all()
            return

        assets = self._discovery.assets(selection.category)
        self._form.set_category(selection.category, assets)
        if selection.asset:
            self._form.set_asset_name(selection.asset)
        self._refresh_all()

    def _current_target(
        self,
        *,
        variant_override: Optional[str] = None,
        asset_override: Optional[str] = None,
        publish_type_override: Optional[str] = None,
        warn: bool = False,
    ) -> Optional[AssetPublishTarget]:
        category = self._form.category()
        if not category:
            return None

        asset_raw = asset_override if asset_override is not None else self._form.asset_name()
        variant_raw = variant_override if variant_override is not None else self._form.variant()
        publish_type = (
            publish_type_override
            if publish_type_override is not None
            else self._form.publish_type()
        )

        if not asset_raw.strip():
            return None

        try:
            asset = normalize_asset_name(asset_raw)
            variant = normalize_variant(variant_raw, self._schema)
        except ValueError as exc:
            if warn:
                self._warn("Invalid target", str(exc))
            return None

        if publish_type not in self._schema.publish_types:
            if warn:
                self._warn("Invalid target", f"Unknown asset type {publish_type!r}.")
            return None

        return AssetPublishTarget(
            category=category,
            asset=asset,
            publish_type=publish_type,
            variant=variant,
            dcc=self._schema.dcc,
        )

    def _refresh_checks(self) -> None:
        """Clear pre-checks on target change; user re-runs explicitly."""
        target = self._current_target()
        self._precheck_panel.clear()
        self._precheck_panel.set_run_enabled(target is not None)
        self._form.set_publish_enabled(target is not None)

    def _on_run_checks(self) -> None:
        target = self._current_target(warn=True)
        if target is None:
            return
        results = self._checks.run(target.publish_type, target=target)
        self._precheck_panel.set_results(results)
        if results:
            self._status.showMessage(
                f"Ran {len(results)} check(s) for {target.publish_type}.", 4000
            )

    def _refresh_table(self) -> None:
        target = self._current_target()
        if target is None:
            self._table.set_entries([])
            self._form.set_load_enabled(False)
            self._form.set_open_enabled(False)
            self._status.showMessage(
                "Select a category in the tree, then set asset name, variant, and asset type."
            )
            return

        entries = self._service.list_versions(target, include_all_variants=True)
        self._table.set_entries(entries)
        has_selection = bool(entries)
        self._form.set_load_enabled(has_selection)
        self._form.set_open_enabled(has_selection)
        folder = self._service.publish_dir(target)
        next_v = self._service.next_version_for_target(target)
        type_label = self._schema.get_publish_type(target.publish_type).label
        self._status.showMessage(
            f"{len(entries)} {type_label} publish(es) in {folder} — "
            f"next {target.variant}: v{next_v:03d}"
        )

    def _refresh_all(self) -> None:
        self._refresh_checks()
        self._refresh_table()

    def _on_table_selection(self, entry: Optional[PublishEntry]) -> None:
        enabled = entry is not None
        self._form.set_load_enabled(enabled)
        self._form.set_open_enabled(enabled)
        if entry is None:
            self._screenshot_panel.display_image(None)
            return
        preview = preview_path_for_version(
            entry.path,
            entry.asset,
            entry.publish_type,
            entry.variant,
            entry.version,
            padding=self._schema.version_padding,
        )
        self._screenshot_panel.display_image(preview)

    def _on_capture(self) -> None:
        tmp = Path(tempfile.gettempdir()) / "tinystudio_asset_manager_capture.png"
        if self._host.capture_viewport_screenshot(tmp):
            self._screenshot_panel.set_image_path(tmp)
            self._status.showMessage(f"Captured {tmp}", 5000)
        else:
            QtWidgets.QMessageBox.information(
                self,
                "Capture",
                "Viewport capture failed. Use Browse to pick an image instead.",
            )

    def _on_publish(self) -> None:
        target = self._current_target(warn=True)
        if target is None:
            return
        screenshot = self._screenshot_panel.screenshot_path()
        try:
            version_dir = self._service.publish(
                self._host,
                target,
                screenshot_path=screenshot,
            )
        except VersionReservationError as exc:
            self._warn("Could not reserve version", str(exc))
            return
        except ExportError as exc:
            self._warn("Export failed", str(exc))
            return
        except Exception as exc:
            logger.exception("Publish failed")
            self._warn("Publish failed", str(exc))
            return

        self._status.showMessage(f"Published {version_dir}", 8000)
        self._asset_tree.refresh()
        if self._form.category():
            self._form.set_category(
                self._form.category(),
                self._discovery.assets(self._form.category()),
            )
        self._form.set_asset_name(target.asset)
        self._refresh_all()

    def _scene_path_for_entry(self, entry: PublishEntry) -> Optional[Path]:
        return scene_path_for_version(
            entry.path,
            entry.asset,
            entry.publish_type,
            entry.variant,
            entry.version,
            padding=self._schema.version_padding,
        )

    def _on_load_selected(self) -> None:
        entry = self._table.current_entry()
        if entry is not None:
            self._load_entry(entry)

    def _on_open_selected(self) -> None:
        entry = self._table.current_entry()
        if entry is not None:
            self._open_entry(entry)

    def _load_entry(self, entry: PublishEntry) -> None:
        scene_path = self._scene_path_for_entry(entry)
        if scene_path is None:
            self._warn("Load failed", f"No Maya scene found in {entry.path}")
            return
        namespace = self._host.sanitize_namespace(entry.asset)
        try:
            self._host.reference_scene(scene_path, namespace)
        except Exception as exc:
            logger.exception("Load failed")
            self._warn("Load failed", str(exc))
            return
        self._status.showMessage(
            f"Referenced {scene_path.name} as {namespace}", 8000
        )

    def _open_entry(self, entry: PublishEntry) -> None:
        scene_path = self._scene_path_for_entry(entry)
        if scene_path is None:
            self._warn("Open failed", f"No Maya scene found in {entry.path}")
            return
        if self._host.is_scene_modified():
            confirm = QtWidgets.QMessageBox.question(
                self,
                "Unsaved changes",
                "The current scene has unsaved changes. Open the selected publish anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if confirm != QtWidgets.QMessageBox.Yes:
                return
        try:
            self._host.open_scene(scene_path)
        except Exception as exc:
            logger.exception("Open failed")
            self._warn("Open failed", str(exc))
            return
        self._status.showMessage(f"Opened {scene_path}", 8000)

    def _on_refresh(self) -> None:
        category = self._form.category()
        asset = self._form.asset_name()
        self._asset_tree.refresh()
        if category:
            self._form.set_category(category, self._discovery.assets(category))
            if asset:
                self._form.set_asset_name(asset)
        self._refresh_all()

    def _warn(self, title: str, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, title, message)


_MAYA_WINDOW_REF: Optional[AssetManagerWindow] = None


def _maya_main_window() -> Optional[QtWidgets.QWidget]:  # pragma: no cover
    try:
        import maya.OpenMayaUI as omui
        from shiboken6 import wrapInstance  # type: ignore[import-not-found]
    except ImportError:
        return None
    ptr = omui.MQtUtil.mainWindow()
    if not ptr:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def main() -> AssetManagerWindow:
    """Shelf entry point: open (or re-open) the Asset Manager window."""
    global _MAYA_WINDOW_REF
    context = resolve_context()
    schema = load_schema()
    host = MayaHost()
    parent = _maya_main_window()
    window = AssetManagerWindow(context, schema, host, parent=parent)
    window.setAttribute(Qt.WA_DeleteOnClose, True)
    window.show()
    _MAYA_WINDOW_REF = window
    return window
