"""Playblast Manager main window (Maya only)."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Optional

from ..core.context import ContextError, StudioContext, resolve_context
from ..core.discovery import RenderRecord, list_renders
from ..core.path_parser import ShotContext, validate_scene_for_render
from ..core.render_service import RenderSettings, RenderValidationError, render
from ..core.schema import PlayblastSchema, load_schema
from ..host import MayaHost
from genTools.uiUtils import load_qss
from .qt import Qt, QtWidgets
from .widgets.camera_list import CameraListWidget
from .widgets.header_bar import HeaderBar
from .widgets.render_history import RenderHistoryWidget
from .widgets.settings_panel import SettingsPanel

logger = logging.getLogger(__name__)


class PlayblastManagerWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        context: StudioContext,
        schema: PlayblastSchema,
        host: MayaHost,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._schema = schema
        self._host = host
        self._shot: Optional[ShotContext] = None

        self.setWindowTitle(f"Playblast Manager — {context.show}")
        self.setStyleSheet(load_qss("dark.qss"))
        self.resize(1000, 720)

        self._build_ui()
        self._connect_signals()
        self.refresh()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        self._header = HeaderBar(self._context)
        outer.addWidget(self._header)

        self._banner = QtWidgets.QFrame()
        self._banner.setFrameShape(QtWidgets.QFrame.StyledPanel)
        banner_layout = QtWidgets.QHBoxLayout(self._banner)
        self._banner_label = QtWidgets.QLabel()
        self._banner_label.setWordWrap(True)
        banner_layout.addWidget(self._banner_label, 1)
        outer.addWidget(self._banner)

        main_splitter = QtWidgets.QSplitter(Qt.Vertical)

        setup = QtWidgets.QWidget()
        setup_layout = QtWidgets.QVBoxLayout(setup)
        setup_layout.setContentsMargins(0, 0, 0, 0)

        top_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self._camera_list = CameraListWidget()
        self._settings = SettingsPanel(self._schema)
        top_splitter.addWidget(self._camera_list)
        top_splitter.addWidget(self._settings)
        top_splitter.setStretchFactor(0, 2)
        top_splitter.setStretchFactor(1, 1)
        setup_layout.addWidget(top_splitter, 1)

        self._render_btn = QtWidgets.QPushButton("Render Selected Cameras")
        self._render_btn.setMinimumHeight(36)
        setup_layout.addWidget(self._render_btn)

        main_splitter.addWidget(setup)

        self._history = RenderHistoryWidget()
        main_splitter.addWidget(self._history)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([360, 300])

        outer.addWidget(main_splitter, 1)
        self.setCentralWidget(central)
        self._status = self.statusBar()

    def _connect_signals(self) -> None:
        self._render_btn.clicked.connect(self._on_render)
        self._history.refresh_button().clicked.connect(self.refresh)
        self._history.open_folder_button().clicked.connect(self._on_open_folder)
        self._camera_list.selection_changed.connect(self._update_render_enabled)

    def refresh(self) -> None:
        """Reload scene state, cameras, validation, and history."""
        scene = self._host.current_scene_path()
        scene_name = scene.name if scene else "—"
        modified = self._host.is_modified()

        self._shot, error = validate_scene_for_render(
            scene,
            self._context,
            is_modified=modified,
        )

        self._header.set_context(
            self._context,
            scene_name=scene_name,
            shot=self._shot,
        )

        start, end = self._host.playback_range()
        self._settings.set_playback_range(start, end)

        cameras = self._host.list_renderable_cameras()
        self._camera_list.set_cameras(cameras)

        if self._shot:
            records = list_renders(self._shot)
            self._history.set_records(records)
        else:
            self._history.set_records([])

        self._update_banner(error)
        self._update_render_enabled()

        if self._shot:
            self._status.showMessage(
                f"{len(cameras)} camera(s) — playblasts: {self._shot.playblasts_root}",
                5000,
            )
        else:
            self._status.showMessage("Scene path not recognised for this show.", 5000)

    def _update_banner(self, error: str) -> None:
        if error:
            self._banner.setVisible(True)
            self._banner_label.setText(error)
        else:
            self._banner.setVisible(False)

    def _update_render_enabled(self) -> None:
        can_render = (
            self._shot is not None
            and not self._host.is_modified()
            and bool(self._camera_list.selected_cameras())
        )
        self._render_btn.setEnabled(can_render)

    def _on_render(self) -> None:
        if self._shot is None:
            return

        cameras = self._camera_list.selected_cameras()
        if not cameras:
            return

        scene_start, scene_end = self._host.playback_range()
        start, end = self._settings.frame_range(scene_start, scene_end)
        settings = RenderSettings(
            start_frame=start,
            end_frame=end,
            show_ornaments=self._settings.show_ornaments(),
            display_mode=self._settings.display_mode(),
            quality=self._settings.quality(),
        )

        self._render_btn.setEnabled(False)
        try:
            render(
                self._host,
                self._context,
                self._shot,
                cameras,
                settings,
                self._schema,
                progress=self._status.showMessage,
            )
        except RenderValidationError as exc:
            QtWidgets.QMessageBox.warning(self, "Cannot render", str(exc))
            self.refresh()
            return
        except Exception as exc:
            logger.exception("Playblast render failed")
            QtWidgets.QMessageBox.warning(self, "Render failed", str(exc))
            self.refresh()
            return
        finally:
            self._update_render_enabled()

        self.refresh()
        self._status.showMessage(
            f"Rendered {len(cameras)} camera(s) to {self._shot.playblasts_root}",
            8000,
        )

    def _on_open_folder(self) -> None:
        record = self._history.current_record()
        if record is None:
            return
        path = record.directory
        if sys.platform == "win32":
            subprocess.run(["explorer", str(path)], check=False)
        else:
            QtWidgets.QMessageBox.information(self, "Open Folder", str(path))


_MAYA_WINDOW_REF: Optional[PlayblastManagerWindow] = None


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


def main() -> PlayblastManagerWindow:
    """Shelf entry point: open (or re-open) the Playblast Manager window."""
    global _MAYA_WINDOW_REF

    try:
        context = resolve_context()
    except ContextError as exc:
        QtWidgets.QMessageBox.critical(None, "Playblast Manager", str(exc))
        raise

    schema = load_schema()
    host = MayaHost()
    parent = _maya_main_window()
    window = PlayblastManagerWindow(context, schema, host, parent=parent)
    window.setAttribute(Qt.WA_DeleteOnClose, True)
    window.show()
    _MAYA_WINDOW_REF = window
    return window
