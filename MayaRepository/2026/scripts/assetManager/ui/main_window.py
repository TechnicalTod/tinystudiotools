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
from .widgets.setdec_tree_browser import SetDecTreeBrowser, list_setdec_versions

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
        self.resize(1650, 930)

        self._build_ui()
        self._connect_signals()
        self._refresh_all()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        outer.addWidget(self._build_header())

        splitter = QtWidgets.QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        self._asset_tree = AssetTreeBrowser(self._discovery, self._schema)
        self._setdec_tree = SetDecTreeBrowser(self._context)
        self._browser_tabs = QtWidgets.QTabWidget()
        self._browser_tabs.addTab(self._asset_tree, "Assets")
        self._browser_tabs.addTab(self._setdec_tree, "Set Dec")
        splitter.addWidget(self._browser_tabs)

        center = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center)
        center_layout.setContentsMargins(8, 0, 8, 0)
        center_layout.setSpacing(12)

        self._table = PublishTable()
        center_layout.addWidget(self._table, 1)

        self._form = PublishForm(schema=self._schema, default_variant=self._schema.default_variant)
        center_layout.addWidget(self._form)

        splitter.addWidget(center)

        right_splitter = QtWidgets.QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(6)
        self._screenshot_panel = ScreenshotPanel()
        self._precheck_panel = PrecheckPanel()
        right_splitter.addWidget(self._screenshot_panel)
        right_splitter.addWidget(self._precheck_panel)
        right_splitter.setStretchFactor(0, 0)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([260, 420])
        splitter.addWidget(right_splitter)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([330, 780, 420])

        outer.addWidget(splitter, 1)
        self.setCentralWidget(central)
        self._status = self.statusBar()

    def _build_header(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(24)
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
        self._browser_tabs.currentChanged.connect(self._on_browser_tab_changed)
        self._asset_tree.selection_changed.connect(self._on_tree_selection)
        self._setdec_tree.selection_changed.connect(self._on_setdec_tree_selection)
        self._form.target_changed.connect(self._refresh_all)
        self._form.publish_requested.connect(self._on_publish)
        self._form.refresh_requested.connect(self._on_refresh)
        self._table.selection_changed.connect(self._on_table_selection)
        self._table.reference_requested.connect(self._reference_entry)
        self._table.import_requested.connect(self._import_entry)
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
        if selection.publish_type:
            self._form.set_publish_type(selection.publish_type)
        self._refresh_all()

    def _on_setdec_tree_selection(self) -> None:
        self._refresh_all()

    def _on_browser_tab_changed(self, _index: int) -> None:
        setdec_mode = self._is_setdec_mode()
        self._form.setEnabled(not setdec_mode)
        self._refresh_all()

    def _is_setdec_mode(self) -> bool:
        return self._browser_tabs.currentWidget() is self._setdec_tree

    def _tree_selection(self):
        if self._is_setdec_mode():
            return None
        return self._asset_tree.current_selection()

    def _browse_target(self) -> Optional[AssetPublishTarget]:
        """Target for browsing published versions — requires a publish type in the tree."""
        selection = self._tree_selection()
        if selection is None or not selection.publish_type:
            return None
        return self._current_target(
            asset_override=selection.asset,
            publish_type_override=selection.publish_type,
        )

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

        selection = self._tree_selection()
        if publish_type_override is not None:
            publish_type = publish_type_override
        elif selection is not None and selection.publish_type:
            publish_type = selection.publish_type
        else:
            publish_type = self._form.publish_type()

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
        if self._is_setdec_mode():
            self._precheck_panel.clear()
            self._precheck_panel.set_run_enabled(False)
            self._form.set_publish_enabled(False)
            return

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
        if self._is_setdec_mode():
            self._refresh_setdec_table()
            return

        browse_target = self._browse_target()
        if browse_target is None:
            self._table.set_entries([])
            selection = self._tree_selection()
            if selection is None:
                self._status.showMessage(
                    "Select a category in the tree, then set asset name, variant, and asset type."
                )
            elif selection.asset and not selection.publish_type:
                self._status.showMessage(
                    "Select a publish type in the tree to browse versions, or publish a new type below."
                )
            else:
                self._status.showMessage(
                    "Select a publish type in the tree, or set asset name, variant, and asset type to publish."
                )
            return

        entries = self._service.list_versions(browse_target, include_all_variants=True)
        self._table.set_entries(entries)
        folder = self._service.publish_dir(browse_target)
        next_v = self._service.next_version_for_target(
            self._current_target(
                asset_override=browse_target.asset,
                publish_type_override=browse_target.publish_type,
                variant_override=browse_target.variant,
            )
            or browse_target
        )
        type_label = self._schema.get_publish_type(browse_target.publish_type).label
        variant = self._form.variant() or self._schema.default_variant
        self._status.showMessage(
            f"{len(entries)} {type_label} publish(es) in {folder} — "
            f"next {variant}: v{next_v:03d}"
        )

    def _refresh_setdec_table(self) -> None:
        selection = self._setdec_tree.current_selection()
        if selection is None or not selection.asset or not selection.variant:
            self._table.set_entries([])
            if selection is None:
                self._status.showMessage("Select a Set Dec group, asset, and variant.")
            elif selection.asset is None:
                self._status.showMessage("Select a Set Dec asset.")
            else:
                self._status.showMessage("Select a Set Dec variant to browse versions.")
            return

        entries = list_setdec_versions(
            self._setdec_tree.setdec_root,
            selection.group,
            selection.asset,
            selection.variant,
        )
        self._table.set_entries(entries)
        folder = (
            self._setdec_tree.setdec_root
            / selection.group
            / selection.asset
            / selection.variant
        )
        self._status.showMessage(
            f"{len(entries)} Set Dec publish(es) in {folder}"
        )

    def _refresh_all(self) -> None:
        self._refresh_checks()
        self._refresh_table()

    def _on_table_selection(self, entry: Optional[PublishEntry]) -> None:
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
                "Viewport capture failed. Try again or publish without a screenshot.",
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

    def _reference_entry(self, entry: PublishEntry) -> None:
        scene_path = self._scene_path_for_entry(entry)
        if scene_path is None:
            self._warn("Reference failed", f"No Maya scene found in {entry.path}")
            return
        namespace = self._host.sanitize_namespace(entry.asset)
        try:
            self._host.reference_scene(scene_path, namespace)
        except Exception as exc:
            logger.exception("Reference failed")
            self._warn("Reference failed", str(exc))
            return
        self._status.showMessage(
            f"Referenced {scene_path.name} as {namespace}", 8000
        )

    def _import_entry(self, entry: PublishEntry) -> None:
        scene_path = self._scene_path_for_entry(entry)
        if scene_path is None:
            self._warn("Import failed", f"No Maya scene found in {entry.path}")
            return
        try:
            self._host.import_scene(scene_path)
        except Exception as exc:
            logger.exception("Import failed")
            self._warn("Import failed", str(exc))
            return
        self._status.showMessage(f"Imported {scene_path.name}", 8000)

    def _open_entry(self, entry: PublishEntry) -> None:
        scene_path = self._scene_path_for_entry(entry)
        if scene_path is None:
            self._warn("Open failed", f"No Maya scene found in {entry.path}")
            return
        message = (
            "Opening this publish will replace the current Maya scene.\n\n"
            f"{scene_path}\n\n"
            "Continue?"
        )
        if self._host.is_scene_modified():
            message = (
                "The current scene has unsaved changes.\n\n"
                + message
            )
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Open published scene",
            message,
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
        if self._is_setdec_mode():
            self._setdec_tree.refresh()
            self._refresh_all()
            return

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
