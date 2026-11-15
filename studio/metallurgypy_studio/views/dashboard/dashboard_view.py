"""Dashboard. Every figure shown here comes from real application state."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from metallurgypy_studio import APP_NAME, __version__
from metallurgypy_studio.viewmodels.app_state import AppState


class DashboardView(QWidget):
    open_workspace = Signal()
    open_file = Signal(str)
    open_docs = Signal()

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self._state = state
        title = QLabel(f"Welcome to {APP_NAME}")
        title.setObjectName("Heading")
        version = QLabel(f"Version {__version__}")
        version.setObjectName("Hint")
        notice = QLabel(
            "Models in this version are documented engineering calculations, not validated "
            "industrial simulations. Check assumptions and validate results against measurements."
        )
        notice.setObjectName("Notice")
        notice.setWordWrap(True)

        start = QPushButton("New calculation")
        start.setObjectName("Primary")
        start.clicked.connect(self.open_workspace)
        docs = QPushButton("Documentation and tutorials")
        docs.clicked.connect(self.open_docs)
        quick = QHBoxLayout()
        quick.addWidget(start)
        quick.addWidget(docs)
        quick.addStretch(1)

        self.recent = QListWidget()
        self.recent.itemActivated.connect(lambda item: self.open_file.emit(item.data(Qt.ItemDataRole.UserRole)))
        recent_box = QGroupBox("Recent calculations (double-click to open)")
        QVBoxLayout(recent_box).addWidget(self.recent)

        self.session = QListWidget()
        session_box = QGroupBox("Calculations in this session")
        QVBoxLayout(session_box).addWidget(self.session)

        self.tasks = QLabel()
        self.tasks.setObjectName("Hint")

        layout = QVBoxLayout(self)
        for widget in (title, version, notice):
            layout.addWidget(widget)
        layout.addLayout(quick)
        row = QHBoxLayout()
        row.addWidget(recent_box)
        row.addWidget(session_box)
        layout.addLayout(row, 1)
        layout.addWidget(self.tasks)
        self.refresh()

    def refresh(self) -> None:
        self.recent.clear()
        if not self._state.settings.recent_files:
            self.recent.addItem("No saved calculation yet.")
            self.recent.item(0).setFlags(Qt.ItemFlag.NoItemFlags)  # placeholder row: not selectable
        for path in self._state.settings.recent_files:
            item = QListWidgetItem(f"{Path(path).name}    ({Path(path).parent})")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.recent.addItem(item)
        self.session.clear()
        if not self._state.session:
            self.session.addItem("Nothing calculated yet.")
        for entry in reversed(self._state.session):
            self.session.addItem(f"{entry.finished_at}  {entry.model_title}")
        n = self._state.running_tasks
        self.tasks.setText("Calculation running…" if n else "No calculation running.")
