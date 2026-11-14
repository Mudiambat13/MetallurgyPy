"""Settings: theme, display precision, default folder."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from metallurgypy_studio.viewmodels.app_state import MAX_DIGITS, MIN_DIGITS, THEMES, AppSettings


class SettingsView(QWidget):
    changed = Signal()

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        title = QLabel("Settings")
        title.setObjectName("Heading")

        self.theme = QComboBox()
        for name in THEMES:
            self.theme.addItem(name.capitalize(), name)
        self.theme.setCurrentIndex(THEMES.index(settings.theme))
        self.theme.currentIndexChanged.connect(self._on_theme)

        self.digits = QSpinBox()
        self.digits.setRange(MIN_DIGITS, MAX_DIGITS)
        self.digits.setValue(settings.display_digits)
        self.digits.valueChanged.connect(self._on_digits)
        hint = QLabel(
            "Display precision only changes what is shown. The engine always keeps full precision, "
            "and saved files and exports contain unrounded values."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)

        self.folder = QLineEdit(settings.default_folder)
        self.folder.setPlaceholderText("Home folder")
        self.folder.editingFinished.connect(self._on_folder)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(browse)

        form = QFormLayout()
        form.addRow("Theme", self.theme)
        form.addRow("Significant digits shown", self.digits)
        form.addRow("", hint)
        form.addRow("Default folder", folder_row)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addStretch(1)

    def _on_theme(self) -> None:
        self._settings.theme = self.theme.currentData()
        self.changed.emit()

    def _on_digits(self, value: int) -> None:
        self._settings.display_digits = value
        self.changed.emit()

    def _on_folder(self) -> None:
        self._settings.default_folder = self.folder.text().strip()
        self.changed.emit()

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Default folder", self.folder.text())
        if path:
            self.folder.setText(path)
            self._on_folder()
