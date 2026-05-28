"""Pre-publish check results list.

Pre-publish checks are **advisory** in v1: the user clicks *Run checks* to
populate this panel. Selecting a different publish type clears the panel
to avoid stale results, and the outcome never gates the *Publish* button.
"""

from __future__ import annotations

from typing import List, Optional

from ...checks.runner import CheckResult
from ..qt import Qt, QtGui, QtWidgets, Signal


class PrecheckPanel(QtWidgets.QGroupBox):
    run_requested = Signal()

    _EMPTY_HINT = "No checks run yet — click \"Run checks\" to validate the scene."

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Pre-checks (advisory)", parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QtWidgets.QHBoxLayout()
        self._summary = QtWidgets.QLabel("")
        self._summary.setStyleSheet("color: #a8a8a8; background: transparent; border: none;")
        self.run_button = QtWidgets.QPushButton("Run checks")
        header.addWidget(self._summary, 1)
        header.addWidget(self.run_button, 0)
        layout.addLayout(header)

        self._list = QtWidgets.QListWidget()
        self._list.setMinimumHeight(100)
        layout.addWidget(self._list)

        self.run_button.clicked.connect(self.run_requested)
        self.clear()

    def clear(self) -> None:
        """Reset the panel to its empty state."""
        self._list.clear()
        placeholder = QtWidgets.QListWidgetItem(self._EMPTY_HINT)
        placeholder.setFlags(Qt.NoItemFlags)
        placeholder.setForeground(QtGui.QBrush(QtGui.QColor(140, 140, 140)))
        self._list.addItem(placeholder)
        self._summary.setText("Not run")

    def set_run_enabled(self, enabled: bool) -> None:
        self.run_button.setEnabled(enabled)

    def set_results(self, results: List[CheckResult]) -> None:
        self._list.clear()
        errors = warnings = passes = 0
        for result in results:
            item = QtWidgets.QListWidgetItem(result.message)
            if result.passed:
                passes += 1
                item.setIcon(self._icon(QtGui.QColor(80, 180, 100)))
            elif result.severity == "warning":
                warnings += 1
                item.setIcon(self._icon(QtGui.QColor(220, 180, 60)))
            else:
                errors += 1
                item.setIcon(self._icon(QtGui.QColor(220, 80, 80)))
            item.setToolTip(f"{result.check_id} ({result.severity})")
            self._list.addItem(item)

        summary_parts: list[str] = []
        if errors:
            summary_parts.append(f"{errors} error(s)")
        if warnings:
            summary_parts.append(f"{warnings} warning(s)")
        if passes:
            summary_parts.append(f"{passes} pass")
        self._summary.setText(" · ".join(summary_parts) or "No checks defined.")

    @staticmethod
    def _icon(color: QtGui.QColor) -> QtGui.QIcon:
        pix = QtGui.QPixmap(12, 12)
        pix.fill(color)
        return QtGui.QIcon(pix)
