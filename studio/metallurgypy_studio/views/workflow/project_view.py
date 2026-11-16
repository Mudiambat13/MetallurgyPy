"""Projects: create/open a project, add calculations, compare them, export reports and archives."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from metallurgypy_studio.viewmodels.workflow_viewmodels import ProjectViewModel


class ProjectView(QWidget):
    open_workspace = Signal()

    def __init__(self, vm: ProjectViewModel) -> None:
        super().__init__()
        self.vm = vm
        title = QLabel("Projects")
        title.setObjectName("Heading")
        self.name_label = QLabel("No project open")
        self.new_btn = QPushButton("New project…")
        self.open_btn = QPushButton("Open project…")
        self.add_btn = QPushButton("Add current calculation")
        self.reopen_btn = QPushButton("Reopen selected")
        self.remove_btn = QPushButton("Unlist selected")
        self.compare_btn = QPushButton("Compare selected")
        self.report_btn = QPushButton("Export report…")
        self.csv_btn = QPushButton("Export comparison…")
        self.zip_btn = QPushButton("Export archive…")
        self.new_btn.clicked.connect(self._new)
        self.open_btn.clicked.connect(self._open)
        self.add_btn.clicked.connect(self._add)
        self.reopen_btn.clicked.connect(self._reopen)
        self.remove_btn.clicked.connect(self._remove)
        self.compare_btn.clicked.connect(self._compare)
        self.report_btn.clicked.connect(self._report)
        self.csv_btn.clicked.connect(self._export_comparison)
        self.zip_btn.clicked.connect(self._archive)

        row1, row2 = QHBoxLayout(), QHBoxLayout()
        for w in (self.new_btn, self.open_btn, self.add_btn, self.reopen_btn, self.remove_btn):
            row1.addWidget(w)
        for w in (self.compare_btn, self.csv_btn, self.report_btn, self.zip_btn):
            row2.addWidget(w)
        row1.addStretch(1)
        row2.addStretch(1)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setAccessibleName("Calculations in the project")
        self.table = QTableWidget(0, 0)
        self.table.setAccessibleName("Comparison")
        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setAccessibleName("Project history")
        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.name_label)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.table, 2)
        layout.addWidget(self.history, 1)
        layout.addWidget(self.message)
        layout.addWidget(self.error)
        vm.subscribe(self.refresh)
        self.refresh()

    def _selected_ids(self) -> list[int]:
        return [int(i.data(Qt.ItemDataRole.UserRole)) for i in self.list.selectedItems()]

    def _new(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose an empty folder for the new project"
        )
        if not folder:
            return
        name, ok = QInputDialog.getText(self, "New project", "Project name:")
        if ok:
            self.vm.create(folder, name)

    def _open(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Open a project folder")
        if folder:
            self.vm.open(folder)

    def _add(self) -> None:
        name, ok = QInputDialog.getText(self, "Add calculation", "Name of this calculation:")
        if ok:
            self.vm.add_current(name.strip())

    def _reopen(self) -> None:
        ids = self._selected_ids()
        if len(ids) == 1 and self.vm.open_in_workspace(ids[0]):
            self.open_workspace.emit()

    def _remove(self) -> None:
        for i in self._selected_ids():
            self.vm.remove(i)

    def _compare(self) -> None:
        ids = self._selected_ids()
        self.vm.compare(ids, ids[0] if ids else None)

    def _export_comparison(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export comparison", "comparison.csv", "CSV (*.csv)"
        )
        if path:
            self.vm.export_comparison(path)

    def _report(self) -> None:
        path, selected = QFileDialog.getSaveFileName(
            self, "Export report", "report.html", "HTML (*.html);;PDF (*.pdf)"
        )
        if not path:
            return
        fmt = "pdf" if path.lower().endswith(".pdf") or "PDF" in selected else "html"
        self.vm.export_report(
            self._selected_ids() or [e.id for e in self.vm.entries()], path, fmt=fmt
        )

    def _archive(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export project archive", "project.zip", "ZIP (*.zip)"
        )
        if path:
            self.vm.export_archive(path)

    def refresh(self) -> None:
        p = self.vm.project
        self.name_label.setText(f"Project: {p.name}" if p else "No project open")
        self.list.clear()
        for e in self.vm.entries():
            item = QListWidgetItem(f"#{e.id}  {e.name}  ({e.model_id}, {e.saved})")
            item.setData(Qt.ItemDataRole.UserRole, e.id)
            self.list.addItem(item)
        self.history.setPlainText("\n".join(self.vm.history_lines()))
        self.message.setText(self.vm.message)
        self.error.setText(self.vm.error or "")
        cmp = self.vm.comparison
        if cmp is None:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        others = [s for s in cmp.scenarios if s != cmp.baseline]
        headers = ["Quantity", "Unit", *cmp.scenarios, *[f"{s} - baseline" for s in others]]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(cmp.rows))
        for r, row in enumerate(cmp.rows):
            cells = [f"{row.section}: {row.name}", row.unit]
            cells += [
                "" if row.values[s] is None else f"{row.values[s]:.6g}" for s in cmp.scenarios
            ]
            cells += [
                "" if row.difference[s] is None else f"{row.difference[s]:+.6g}" for s in others
            ]
            for c, text in enumerate(cells):
                self.table.setItem(r, c, QTableWidgetItem(text))
