"""Data Import: choose a file, map columns to named values with units, validate, run a model per row."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from metallurgypy_studio.viewmodels.workflow_viewmodels import ImportViewModel


class ImportView(QWidget):
    def __init__(self, vm: ImportViewModel) -> None:
        super().__init__()
        self.vm = vm
        title = QLabel("Data Import")
        title.setObjectName("Heading")
        hint = QLabel(
            "Choose a CSV, JSON or Excel file, say what each column is (name and unit), then validate. "
            "Rows that cannot be used are listed with the reason; your file is never modified."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)

        self.open_btn = QPushButton("Open data file…")
        self.open_btn.clicked.connect(self._open)
        self.model_box = QComboBox()
        self.model_box.addItems(vm.model_ids)
        self.model_box.currentTextChanged.connect(lambda t: setattr(vm, "model_id", t))
        self.validate_btn = QPushButton("Validate rows")
        self.validate_btn.clicked.connect(self._validate)
        self.run_btn = QPushButton("Run model on valid rows")
        self.run_btn.clicked.connect(self._run)
        self.reject_btn = QPushButton("Export rejected rows…")
        self.reject_btn.clicked.connect(self._export_rejected)
        bar = QHBoxLayout()
        for w in (self.open_btn, self.validate_btn, QLabel("Model:"), self.model_box, self.run_btn, self.reject_btn):
            bar.addWidget(w)
        bar.addStretch(1)

        self.columns = QTableWidget(0, 6)
        self.columns.setHorizontalHeaderLabels(["Use", "Column", "Name", "Unit", "Min", "Max"])
        self.columns.setAccessibleName("Column mapping")
        self.results = QTableWidget(0, 2)
        self.results.setHorizontalHeaderLabels(["Row", "Outcome"])
        self.results.setAccessibleName("Import and model results")
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setWordWrap(True)

        layout = QVBoxLayout(self)
        for w in (title, hint):
            layout.addWidget(w)
        layout.addLayout(bar)
        layout.addWidget(self.columns, 2)
        layout.addWidget(self.summary)
        layout.addWidget(self.error)
        layout.addWidget(self.results, 2)
        vm.subscribe(self.refresh)
        self.refresh()

    def _open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open data file", "", "Data (*.csv *.tsv *.txt *.json *.xlsx);;All files (*)"
        )
        if path:
            self.vm.load(path)

    def _sync_choices(self) -> None:
        for r, choice in enumerate(self.vm.choices):
            use = self.columns.cellWidget(r, 0)
            if isinstance(use, QCheckBox):
                choice.use = use.isChecked()
            for col, attr in ((2, "name"), (3, "unit"), (4, "minimum"), (5, "maximum")):
                w = self.columns.cellWidget(r, col)
                if isinstance(w, QLineEdit):
                    setattr(choice, attr, w.text())

    def _validate(self) -> None:
        self._sync_choices()
        self.vm.validate()

    def _run(self) -> None:
        self.vm.run_model()

    def _export_rejected(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export rejected rows", "rejected_rows.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            self.vm.export_rejected(path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def refresh(self) -> None:
        # rebuild the mapping table only when the file (not the validation state) changed
        if self.columns.rowCount() != len(self.vm.choices):
            self.columns.setRowCount(len(self.vm.choices))
            for r, c in enumerate(self.vm.choices):
                use = QCheckBox()
                use.setChecked(c.use)
                use.setAccessibleName(f"Use column {c.info.name}")
                self.columns.setCellWidget(r, 0, use)
                label = QTableWidgetItem(c.info.name)
                label.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.columns.setItem(r, 1, label)
                for col, text in ((2, c.name), (3, c.unit), (4, c.minimum), (5, c.maximum)):
                    self.columns.setCellWidget(r, col, QLineEdit(text))
        self.summary.setText(self.vm.summary())
        self.error.setText(self.vm.error or "")
        rows: list[tuple[str, str]] = []
        if self.vm.report is not None:
            rows += [(str(r.row_number), "rejected: " + "; ".join(r.reasons)) for r in self.vm.report.rejected]
        for item in self.vm.batch:
            outcome = "ok" if item.result is not None else f"model error: {item.error}"
            rows.append((str(item.row_number), outcome))
        self.results.setRowCount(len(rows))
        for r, (a, b) in enumerate(rows):
            self.results.setItem(r, 0, QTableWidgetItem(a))
            self.results.setItem(r, 1, QTableWidgetItem(b))
