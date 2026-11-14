"""Module Explorer: the scientific modules, their models, and their documentation."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from metallurgypy_studio import DOCS_URL
from metallurgypy_studio.services.calculation_service import ModuleOverview


class ModulesView(QWidget):
    open_workspace = Signal()

    def __init__(self, overview: tuple[ModuleOverview, ...]) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        title = QLabel("Module Explorer")
        title.setObjectName("Heading")
        outer.addWidget(title)
        container = QWidget()
        column = QVBoxLayout(container)
        for module in overview:
            box = QGroupBox(module.info.title)
            inner = QVBoxLayout(box)
            description = QLabel(module.info.description)
            description.setWordWrap(True)
            inner.addWidget(description)
            if module.available:
                for spec in module.models:
                    inner.addWidget(QLabel(f"• {spec.title} (model version {spec.model_version})"))
            else:
                status = QLabel("Planned: not available in this version.")
                status.setObjectName("Hint")
                inner.addWidget(status)
            buttons = QHBoxLayout()
            if module.available:
                open_button = QPushButton("Open workspace")
                open_button.clicked.connect(self.open_workspace)
                buttons.addWidget(open_button)
            docs = QPushButton("Documentation")
            docs.clicked.connect(
                lambda _=False, page=module.info.doc_page: QDesktopServices.openUrl(QUrl(DOCS_URL + page))
            )
            buttons.addWidget(docs)
            buttons.addStretch(1)
            inner.addLayout(buttons)
            column.addWidget(box)
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        outer.addWidget(scroll)
