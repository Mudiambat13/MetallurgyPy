"""Main window: top bar, side navigation and the stacked views."""

from __future__ import annotations

import contextlib
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from metallurgypy_studio import APP_NAME, DOCS_URL, __version__
from metallurgypy_studio.services.calculation_service import CalculationService
from metallurgypy_studio.services.workflow_service import DataService, ProjectService
from metallurgypy_studio.viewmodels.app_state import AppSettings, AppState
from metallurgypy_studio.viewmodels.workflow_viewmodels import ImportViewModel, ProjectViewModel
from metallurgypy_studio.viewmodels.workspace_viewmodel import WorkspaceViewModel
from metallurgypy_studio.views.dashboard.dashboard_view import DashboardView
from metallurgypy_studio.views.modules.modules_view import ModulesView
from metallurgypy_studio.views.settings.settings_view import SettingsView
from metallurgypy_studio.views.workflow.import_view import ImportView
from metallurgypy_studio.views.workflow.project_view import ProjectView
from metallurgypy_studio.views.workspace.workspace_view import WorkspaceView

STYLES = Path(__file__).parent / "resources" / "styles"
PAGES = ("Dashboard", "Modules", "Calculation", "Data Import", "Projects", "Settings")


def settings_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(base or Path.home() / ".metallurgypy") / "studio_settings.json"


def apply_theme(app: QApplication, theme: str) -> None:
    try:
        app.setStyleSheet((STYLES / f"{theme}.qss").read_text(encoding="utf-8"))
    except OSError:
        app.setStyleSheet("")  # fall back to the native style rather than failing


class MainWindow(QMainWindow):
    def __init__(
        self, app: QApplication, settings: AppSettings, config_file: Path | None = None
    ) -> None:
        super().__init__()
        self._app = app
        self._config_file = config_file
        self.state = AppState(settings=settings)
        self.service = CalculationService()
        self.vm = WorkspaceViewModel(self.service, self.state)
        self.import_vm = ImportViewModel(DataService(), [m.model_id for m in self.service.models()])
        self.project_vm = ProjectViewModel(ProjectService(self.service), self.vm)
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(1200, 760)

        self.status = QLabel("Ready")
        self.status.setObjectName("StatusLabel")
        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        top = QWidget()
        top.setObjectName("TopBar")
        top_layout = QHBoxLayout(top)
        top_layout.addWidget(title)
        top_layout.addStretch(1)
        top_layout.addWidget(self.status)

        self.nav = QListWidget()
        self.nav.setObjectName("Sidebar")
        self.nav.setFixedWidth(190)
        self.nav.addItems(PAGES)
        self.nav.setAccessibleName("Navigation")

        self.dashboard = DashboardView(self.state)
        self.modules = ModulesView(self.service.module_overview())
        self.workspace = WorkspaceView(self.vm, self.service)
        self.import_view = ImportView(self.import_vm)
        self.project_view = ProjectView(self.project_vm)
        self.settings_view = SettingsView(settings)
        self.stack = QStackedWidget()
        for page in (
            self.dashboard,
            self.modules,
            self.workspace,
            self.import_view,
            self.project_view,
            self.settings_view,
        ):
            self.stack.addWidget(page)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        root = QWidget()
        column = QVBoxLayout(root)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(top)
        column.addLayout(body, 1)
        self.setCentralWidget(root)

        self.nav.currentRowChanged.connect(self._on_nav)
        self.workspace.status_changed.connect(self.status.setText)
        self.vm.subscribe(self.dashboard.refresh)
        self.project_view.open_workspace.connect(lambda: self.nav.setCurrentRow(2))
        self.dashboard.open_workspace.connect(lambda: self.nav.setCurrentRow(2))
        self.modules.open_workspace.connect(lambda: self.nav.setCurrentRow(2))
        self.dashboard.open_docs.connect(lambda: QDesktopServices.openUrl(QUrl(DOCS_URL)))
        self.dashboard.open_file.connect(self._open_recent)
        self.settings_view.changed.connect(self._on_settings_changed)
        self.nav.setCurrentRow(0)
        self._on_settings_changed()

    def _on_nav(self, row: int) -> None:
        if row >= 0:
            self.stack.setCurrentIndex(row)
            if row == 0:
                self.dashboard.refresh()

    def _open_recent(self, path: str) -> None:
        self.workspace.open_path(path)
        self.nav.setCurrentRow(2)

    def _on_settings_changed(self) -> None:
        apply_theme(self._app, self.state.settings.theme)
        self.workspace.chart.set_dark(self.state.settings.theme == "dark")
        self.vm.notify()  # re-render numbers with the new display precision

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._config_file is not None:
            # losing a preference must never block closing the application
            with contextlib.suppress(OSError):
                self.state.settings.save(self._config_file)
        super().closeEvent(event)
