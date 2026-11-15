"""View models for Data Import and Projects (compare, reports). Independent of Qt."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from metallurgypy.comparison import Comparison
from metallurgypy.core import Quantity
from metallurgypy.core.exceptions import MetallurgyPyError
from metallurgypy.data_io import BatchItem, ColumnMapping, ImportReport, Table
from metallurgypy.projects import Project, ProjectEntry
from metallurgypy_studio.services.calculation_service import parse_number
from metallurgypy_studio.services.workflow_service import ColumnInfo, DataService, ProjectService
from metallurgypy_studio.viewmodels.workspace_viewmodel import WorkspaceViewModel


class _Observable:
    def __init__(self) -> None:
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def notify(self) -> None:
        for listener in self._listeners:
            listener()


@dataclass
class ColumnChoice:
    info: ColumnInfo
    use: bool
    name: str
    unit: str
    kind: str
    minimum: str = ""
    maximum: str = ""


class ImportViewModel(_Observable):
    """Pick a file, say what each column means (name + unit), validate, optionally run a model per row."""

    def __init__(self, data: DataService, models: list[str]) -> None:
        super().__init__()
        self._data = data
        self.model_ids = models
        self.table: Table | None = None
        self.choices: list[ColumnChoice] = []
        self.report: ImportReport | None = None
        self.batch: tuple[BatchItem, ...] = ()
        self.error: str | None = None
        self.model_id = models[0] if models else ""
        self.fixed: dict[str, tuple[str, str]] = {}  # parameter -> (text, unit) shared by all rows

    def load(self, path: str | os.PathLike[str], *, delimiter: str | None = None, decimal: str | None = None) -> bool:
        self.report, self.batch, self.error = None, (), None
        try:
            self.table = self._data.read(path, delimiter=delimiter, decimal=decimal)
        except MetallurgyPyError as exc:
            self.table, self.choices, self.error = None, [], str(exc)
            self.notify()
            return False
        self.choices = [
            ColumnChoice(i, i.detected_kind == "number" and i.guessed_unit is not None, i.name,
                         i.guessed_unit or "", i.detected_kind)
            for i in self._data.describe(self.table)
        ]
        self.notify()
        return True

    def validate(self) -> bool:
        """Validate every row; the result is in ``report`` (never silently dropping rows)."""
        self.batch, self.error = (), None
        if self.table is None:
            self.error = "Load a file first."
            self.notify()
            return False
        try:
            mappings = [
                ColumnMapping(
                    c.info.name, c.name.strip(), c.unit.strip() or None, c.kind,
                    minimum=parse_number(c.minimum) if c.minimum.strip() else None,
                    maximum=parse_number(c.maximum) if c.maximum.strip() else None,
                )
                for c in self.choices if c.use
            ]
            if not mappings:
                raise ValueError("Select at least one column.")
            self.report = self._data.import_rows(self.table, mappings)
        except (MetallurgyPyError, ValueError) as exc:
            self.report, self.error = None, str(exc)
            self.notify()
            return False
        self.notify()
        return True

    def run_model(self) -> bool:
        if self.report is None:
            self.error = "Validate the data first."
            self.notify()
            return False
        try:
            fixed = {n: Quantity(parse_number(t), u) for n, (t, u) in self.fixed.items() if t.strip()}
            self.batch = self._data.run_batch(self.model_id, self.report, fixed)
            self.error = None
        except (MetallurgyPyError, ValueError) as exc:
            self.batch, self.error = (), str(exc)
            self.notify()
            return False
        self.notify()
        return True

    def summary(self) -> str:
        if self.report is None:
            return ""
        rep = self.report
        text = f"{len(rep.rows)} valid row(s), {len(rep.rejected)} rejected, out of {rep.total}."
        if self.batch:
            ok = sum(1 for b in self.batch if b.result is not None)
            text += f" Model run: {ok} succeeded, {len(self.batch) - ok} failed."
        return text

    def export_rejected(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
        if self.report is None or not self.report.rejected:
            raise ValueError("There are no rejected rows to export.")
        return self._data.export_rejected(path, self.report, overwrite=overwrite)


class ProjectViewModel(_Observable):
    def __init__(self, service: ProjectService, workspace: WorkspaceViewModel) -> None:
        super().__init__()
        self._service = service
        self._workspace = workspace
        self.project: Project | None = None
        self.comparison: Comparison | None = None
        self.error: str | None = None
        self.message = ""

    # every action returns True/False and puts a human message in ``error`` or ``message``
    def _guard(self, action: Callable[[], str]) -> bool:
        self.error, self.message = None, ""
        try:
            self.message = action()
        except (MetallurgyPyError, ValueError, OSError) as exc:
            self.error = str(exc)
        self.notify()
        return self.error is None

    def create(self, folder: str | os.PathLike[str], name: str, description: str = "") -> bool:
        def go() -> str:
            self.project = self._service.create(folder, name, description)
            return f"Project {self.project.name!r} created."
        return self._guard(go)

    def open(self, folder: str | os.PathLike[str]) -> bool:
        def go() -> str:
            self.project = self._service.open(folder)
            self.comparison = None
            return f"Project {self.project.name!r} opened."
        return self._guard(go)

    def entries(self) -> tuple[ProjectEntry, ...]:
        return self.project.entries() if self.project else ()

    def history_lines(self) -> list[str]:
        return [f"{h.timestamp}  {h.action}  {h.detail}" for h in self.project.history()] if self.project else []

    def add_current(self, name: str) -> bool:
        def go() -> str:
            if self.project is None:
                raise ValueError("Open or create a project first.")
            if self._workspace.result is None:
                raise ValueError("Run a calculation first; there is nothing to add.")
            entry = self._service.add(
                self.project, self._workspace.result, name or self._workspace.spec.title,
                notes=self._workspace.notes, uncertain=self._workspace.uncertain,
            )
            return f"Added {entry.name!r}."
        return self._guard(go)

    def open_in_workspace(self, entry_id: int) -> bool:
        def go() -> str:
            if self.project is None:
                raise ValueError("Open a project first.")
            self._workspace.open_file(self.project.calculation_path(entry_id))
            return "Calculation reopened and recomputed."
        return self._guard(go)

    def remove(self, entry_id: int) -> bool:
        def go() -> str:
            if self.project is None:
                raise ValueError("Open a project first.")
            self.project.remove_entry(entry_id)
            return "Unlisted. The file was kept on disk."
        return self._guard(go)

    def compare(self, entry_ids: list[int], baseline_id: int | None = None) -> bool:
        def go() -> str:
            if self.project is None:
                raise ValueError("Open a project first.")
            self.comparison = self._service.compare(self.project, entry_ids, baseline_id)
            return f"Compared {len(entry_ids)} calculations."
        return self._guard(go)

    def export_comparison(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> bool:
        def go() -> str:
            if self.comparison is None:
                raise ValueError("Run a comparison first.")
            return f"Saved {self._service.export_comparison(path, self.comparison, overwrite=overwrite)}"
        return self._guard(go)

    def export_report(self, entry_ids: list[int], path: str | os.PathLike[str], *, fmt: str = "html",
                      author: str = "", overwrite: bool = False) -> bool:
        def go() -> str:
            if self.project is None:
                raise ValueError("Open a project first.")
            if not entry_ids:
                raise ValueError("Select at least one calculation for the report.")
            return f"Saved {self._service.export_report(self.project, entry_ids, path, fmt=fmt, author=author, overwrite=overwrite)}"
        return self._guard(go)

    def export_archive(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> bool:
        def go() -> str:
            if self.project is None:
                raise ValueError("Open a project first.")
            return f"Saved {self._service.export_archive(self.project, path, overwrite=overwrite)}"
        return self._guard(go)
