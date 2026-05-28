"""Read-only header showing show, scene, shot, and user."""

from __future__ import annotations

from typing import Optional

from ..qt import Qt, QtWidgets
from ...core.context import StudioContext
from ...core.path_parser import ShotContext


class HeaderBar(QtWidgets.QFrame):
    def __init__(self, context: StudioContext, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        self._show_lbl = QtWidgets.QLabel()
        self._scene_lbl = QtWidgets.QLabel()
        self._shot_lbl = QtWidgets.QLabel()
        self._user_lbl = QtWidgets.QLabel()

        for label in (self._show_lbl, self._scene_lbl, self._shot_lbl, self._user_lbl):
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(label)

        layout.addStretch(1)
        self.set_context(context, scene_name="—", shot=None)

    def set_context(
        self,
        context: StudioContext,
        *,
        scene_name: str,
        shot: Optional[ShotContext],
    ) -> None:
        self._show_lbl.setText(f"<b>Show:</b> {context.show}")
        self._scene_lbl.setText(f"<b>Scene:</b> {scene_name}")
        shot_text = shot.shot_label if shot else "—"
        self._shot_lbl.setText(f"<b>Shot:</b> {shot_text}")
        self._user_lbl.setText(f"<b>User:</b> {context.username}")
