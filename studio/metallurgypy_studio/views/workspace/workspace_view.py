"""Calculation Workspace: dynamic form, results, chart, assumptions, save and export.

The form is generated from the ``ParameterSpec`` list of the selected model, so
adding a model to the registry adds its form without any new widget code.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from metallurgypy_studio import DOCS_URL
from metallurgypy_studio.services.calculation_service import CalculationService, RunOutcome
from metallurgypy_studio.viewmodels.workspace_viewmodel import (
    ERROR,
    IDLE,
    OK,
    RUNNING,
    WorkspaceViewModel,
)
from metallurgypy_studio.widgets.chart_widget import ChartWidget
from metallurgypy_studio.workers.calc_worker import CalcWorker

KIND_LABELS = {"calculated": "calculated", "estimated": "estimated", "measured": "measured"}


class WorkspaceView(QWidget):
    status_changed = Signal(str)

    def __init__(self, vm: WorkspaceViewModel, service: CalculationService) -> None:
        super().__init__()
        self.vm = vm
        self._service = service
        self._workers: set[CalcWorker] = set()
        self._edits: dict[str, QLineEdit] = {}
        self._u_edits: dict[str, QLineEdit] = {}
        self._unit_boxes: dict[str, QComboBox] = {}
        self._error_labels: dict[str, QLabel] = {}
        self._build()
        vm.subscribe(self.refresh)
        self._rebuild_form()
        self.refresh()

    # ------------------------------ layout ---------------------------------- #

    def _build(self) -> None:
        self.model_box = QComboBox()
        for spec in self.vm.models():
            self.model_box.addItem(spec.title, spec.model_id)
        self.model_box.currentIndexChanged.connect(self._on_model_changed)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setObjectName("Hint")

        self.form_box = QGroupBox("Inputs")
        self.form = QFormLayout(self.form_box)

        self.calc_button = QPushButton("Calculate")
        self.calc_button.setObjectName("Primary")
        self.calc_button.clicked.connect(self._on_calculate)
        self.example_button = QPushButton("Fill with example")
        self.example_button.setToolTip("Fills the form with illustrative (fictional) values.")
        self.example_button.clicked.connect(self.vm.fill_example)
        self.docs_button = QPushButton("Documentation")
        self.docs_button.clicked.connect(self._open_docs)
        buttons = QHBoxLayout()
        buttons.addWidget(self.calc_button)
        buttons.addWidget(self.example_button)
        buttons.addWidget(self.docs_button)

        self.general_error = QLabel()
        self.general_error.setObjectName("ErrorText")
        self.general_error.setWordWrap(True)
        self.general_error.hide()

        left = QWidget()
        left_layout = QVBoxLayout(left)
        title = QLabel("Calculation Workspace")
        title.setObjectName("Heading")
        left_layout.addWidget(title)
        left_layout.addWidget(QLabel("Model"))
        left_layout.addWidget(self.model_box)
        left_layout.addWidget(self.description)
        left_layout.addWidget(self.form_box)
        left_layout.addLayout(buttons)
        left_layout.addWidget(self.general_error)
        left_layout.addStretch(1)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Quantity", "Value", "Unit", "Kind", "Std. uncertainty"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.warnings_label = QLabel()
        self.warnings_label.setObjectName("Notice")
        self.warnings_label.setWordWrap(True)
        self.verify_label = QLabel()
        self.verify_label.setObjectName("Notice")
        self.verify_label.setWordWrap(True)
        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)
        results_layout.addWidget(self.verify_label)
        results_layout.addWidget(self.warnings_label)
        results_layout.addWidget(self.table, 1)

        self.chart = ChartWidget()
        self.assumptions = QPlainTextEdit()
        self.assumptions.setReadOnly(True)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.tabs = QTabWidget()
        self.tabs.addTab(results_page, "Results")
        self.tabs.addTab(self.chart, "Chart")
        self.tabs.addTab(self.assumptions, "Assumptions")
        self.tabs.addTab(self.details, "Calculation details")

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Calculation name (optional)")
        self.name_edit.textChanged.connect(lambda t: setattr(self.vm, "name", t))
        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Notes saved with the calculation")
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.textChanged.connect(
            lambda: setattr(self.vm, "notes", self.notes_edit.toPlainText())
        )
        self.save_button = QPushButton("Save calculation…")
        self.save_button.clicked.connect(self._on_save)
        self.open_button = QPushButton("Open calculation…")
        self.open_button.clicked.connect(self._on_open)
        self.csv_button = QPushButton("Export CSV…")
        self.csv_button.clicked.connect(lambda: self._on_export("csv"))
        self.json_button = QPushButton("Export JSON…")
        self.json_button.clicked.connect(lambda: self._on_export("json"))
        self.png_button = QPushButton("Chart PNG…")
        self.png_button.clicked.connect(lambda: self._on_chart_export(".png"))
        self.svg_button = QPushButton("Chart SVG…")
        self.svg_button.clicked.connect(lambda: self._on_chart_export(".svg"))
        actions = QHBoxLayout()
        for button in (
            self.save_button,
            self.open_button,
            self.csv_button,
            self.json_button,
            self.png_button,
            self.svg_button,
        ):
            actions.addWidget(button)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.tabs, 1)
        right_layout.addWidget(self.name_edit)
        right_layout.addWidget(self.notes_edit)
        right_layout.addLayout(actions)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        outer = QVBoxLayout(self)
        outer.addWidget(splitter)

    def _rebuild_form(self) -> None:
        while self.form.rowCount():
            self.form.removeRow(0)
        self._edits.clear()
        self._u_edits.clear()
        self._unit_boxes.clear()
        self._error_labels.clear()
        spec = self.vm.spec
        self.description.setText(spec.description)
        for param in spec.parameters:
            edit = QLineEdit()
            edit.setPlaceholderText(f"{param.label}…")
            edit.setToolTip(param.description)
            edit.setAccessibleName(param.label)
            edit.textChanged.connect(lambda text, n=param.name: self.vm.set_field(n, text=text))
            unit_box = QComboBox()
            unit_box.addItems(param.units)
            unit_box.currentTextChanged.connect(
                lambda unit, n=param.name: self.vm.set_field(n, unit=unit)
            )
            error = QLabel()
            error.setObjectName("ErrorText")
            error.setWordWrap(True)
            error.hide()
            u_edit = QLineEdit()
            u_edit.setPlaceholderText("± u (optional)")
            u_edit.setToolTip(
                "Standard uncertainty of this value, in the same unit. Leave blank if the value is exact."
            )
            u_edit.setAccessibleName(f"{param.label} standard uncertainty")
            u_edit.setMaximumWidth(120)
            u_edit.textChanged.connect(
                lambda text, n=param.name: self.vm.set_field(n, uncertainty=text)
            )
            row = QHBoxLayout()
            row.addWidget(edit, 1)
            row.addWidget(unit_box)
            row.addWidget(u_edit)
            self._u_edits[param.name] = u_edit
            cell = QVBoxLayout()
            cell.addLayout(row)
            cell.addWidget(error)
            self.form.addRow(QLabel(param.label), cell)
            self._edits[param.name] = edit
            self._unit_boxes[param.name] = unit_box
            self._error_labels[param.name] = error
        self._sync_form_from_vm()

    def _sync_form_from_vm(self) -> None:
        for name, edit in self._edits.items():
            field = self.vm.fields[name]
            edit.blockSignals(True)
            edit.setText(field.text)
            edit.blockSignals(False)
            u_edit = self._u_edits[name]
            u_edit.blockSignals(True)
            u_edit.setText(field.uncertainty)
            u_edit.blockSignals(False)
            box = self._unit_boxes[name]
            box.blockSignals(True)
            box.setCurrentText(field.unit)
            box.blockSignals(False)

    # ------------------------------ updates --------------------------------- #

    def refresh(self) -> None:
        vm = self.vm
        index = self.model_box.findData(vm.spec.model_id)
        if index >= 0 and index != self.model_box.currentIndex():
            self.model_box.blockSignals(True)
            self.model_box.setCurrentIndex(index)
            self.model_box.blockSignals(False)
        if set(self._edits) != {p.name for p in vm.spec.parameters}:
            self._rebuild_form()
        elif (vm.status in (IDLE, OK) and vm.result is None) or vm.last_saved is not None:
            self._sync_form_from_vm()

        for name, edit in self._edits.items():
            message = vm.field_errors.get(name, "")
            self._error_labels[name].setText(message)
            self._error_labels[name].setVisible(bool(message))
            edit.setProperty("invalid", bool(message))
            edit.style().unpolish(edit)
            edit.style().polish(edit)
        self.general_error.setText(vm.error or "")
        self.general_error.setVisible(bool(vm.error))
        self.description.setText(vm.spec.description)

        busy = vm.status == RUNNING
        self.calc_button.setEnabled(not busy)
        self.calc_button.setText("Calculating…" if busy else "Calculate")

        has_result = vm.result is not None
        for button in (
            self.save_button,
            self.csv_button,
            self.json_button,
            self.png_button,
            self.svg_button,
        ):
            button.setEnabled(has_result)

        rows = vm.rows()
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            u_cell = f"± {row.uncertainty_text}" if row.uncertainty_text else ""
            for c, text in enumerate(
                (row.label, row.value_text, row.unit, KIND_LABELS.get(row.kind, row.kind), u_cell)
            ):
                self.table.setItem(r, c, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()

        warnings = vm.warnings
        self.warnings_label.setText("Warnings:\n• " + "\n• ".join(warnings) if warnings else "")
        self.warnings_label.setVisible(bool(warnings))
        if vm.differences:
            self.verify_label.setText(
                "This saved result does NOT match a fresh calculation:\n• "
                + "\n• ".join(vm.differences)
            )
        elif vm.last_saved is not None and has_result:
            self.verify_label.setText("Saved result reproduced by the installed model.")
        else:
            self.verify_label.setText("")
        self.verify_label.setVisible(bool(self.verify_label.text()))
        self.assumptions.setPlainText("\n".join(f"• {a}" for a in vm.assumptions))
        self.details.setPlainText(vm.details_text())
        self.chart.set_chart(vm.result.chart_data() if vm.result else None)
        for edit, text, setter in ((self.name_edit, vm.name, self.name_edit.setText),):
            if edit.text() != text:
                edit.blockSignals(True)
                setter(text)
                edit.blockSignals(False)
        if self.notes_edit.toPlainText() != vm.notes:
            self.notes_edit.blockSignals(True)
            self.notes_edit.setPlainText(vm.notes)
            self.notes_edit.blockSignals(False)
        self.status_changed.emit(
            {
                IDLE: "Ready",
                RUNNING: "Calculating…",
                OK: "Calculation complete",
                ERROR: "Input error",
            }[vm.status]
        )

    # ------------------------------ actions --------------------------------- #

    def _on_model_changed(self) -> None:
        self.vm.select_model(self.model_box.currentData())

    def _on_calculate(self) -> None:
        model_id, fields, correlations = self.vm.prepare_run()
        worker = CalcWorker(self._service, model_id, fields, correlations)
        self._workers.add(worker)

        def done(outcome: RunOutcome, w: CalcWorker = worker) -> None:
            self._workers.discard(w)
            self.vm.apply_outcome(outcome)

        worker.signals.finished.connect(done)
        QThreadPool.globalInstance().start(worker)

    def _open_docs(self) -> None:
        QDesktopServices.openUrl(QUrl(DOCS_URL + self.vm.spec.doc_page))

    def _suggested(self, suffix: str) -> str:
        folder = self.vm._state.settings.default_folder or str(Path.home())
        base = (self.vm.name.strip() or self.vm.spec.model_id).replace("/", "_")
        return str(Path(folder) / (base + suffix))

    def _run_file_action(self, action: object, path: str, success: str) -> None:
        """Run a save/export; on an existing file ask before overwriting."""
        try:
            try:
                action(path, overwrite=False)  # type: ignore[operator]
            except FileExistsError:
                answer = QMessageBox.question(
                    self, "Replace file?", f"{Path(path).name} already exists. Replace it?"
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
                action(path, overwrite=True)  # type: ignore[operator]
            QMessageBox.information(self, "Done", f"{success}\n{path}")
        except OSError as exc:
            QMessageBox.warning(self, "Could not write the file", str(exc))

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save calculation",
            self._suggested(".mpy.json"),
            "MetallurgyPy calculation (*.mpy.json)",
        )
        if path:
            if not path.endswith(".mpy.json"):
                path += ".mpy.json"
            self._run_file_action(self.vm.save, path, "Calculation saved.")

    def _on_export(self, kind: str) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {kind.upper()}",
            self._suggested("." + kind),
            f"{kind.upper()} (*.{kind})",
        )
        if path:
            action = self.vm.export_csv if kind == "csv" else self.vm.export_json
            self._run_file_action(action, path, "Results exported.")

    def _on_chart_export(self, suffix: str) -> None:
        chart = self.vm.result.chart_data() if self.vm.result else None
        if chart is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export chart", self._suggested(suffix), f"Image (*{suffix})"
        )
        if not path:
            return
        try:
            from metallurgypy.visualization import save_chart
        except ImportError as exc:
            QMessageBox.warning(self, "Chart export unavailable", str(exc))
            return
        self._run_file_action(
            lambda p, overwrite: save_chart(chart, p, overwrite=overwrite), path, "Chart exported."
        )

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open calculation",
            self.vm._state.settings.default_folder or str(Path.home()),
            "MetallurgyPy calculation (*.mpy.json);;All files (*)",
        )
        if path:
            self.open_path(path)

    def open_path(self, path: str) -> None:
        from metallurgypy.core import MetallurgyPyError

        try:
            self.vm.open_file(path)
        except (MetallurgyPyError, OSError) as exc:
            QMessageBox.warning(self, "Could not open the file", str(exc))
