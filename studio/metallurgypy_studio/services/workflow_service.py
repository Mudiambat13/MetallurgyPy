"""Use cases for data import, projects, comparison and reports. No Qt; everything is Core API calls."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from metallurgypy.comparison import Comparison, compare, export_comparison_csv
from metallurgypy.core import CalculationResult, Quantity
from metallurgypy.data_io import (
    BatchItem,
    ColumnMapping,
    ImportReport,
    Table,
    detect_column_types,
    guess_unit,
    import_table,
    read_table,
    run_batch,
    write_rejected_csv,
)
from metallurgypy.precision import UncertainResult
from metallurgypy.projects import Project, ProjectEntry
from metallurgypy.registry import get_model
from metallurgypy.reports import ReportEntry, build_report, write_html, write_pdf
from metallurgypy_studio.services.calculation_service import CalculationService

StrPath = str | os.PathLike[str]


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    detected_kind: str  # "number" | "text"
    guessed_unit: str | None


@dataclass(frozen=True)
class LoadedCalculation:
    entry: ProjectEntry
    result: CalculationResult
    uncertain: UncertainResult | None
    notes: str
    differences: tuple[str, ...]


class DataService:
    def read(
        self, path: StrPath, *, delimiter: str | None = None, decimal: str | None = None
    ) -> Table:
        return read_table(path, delimiter=delimiter, decimal=decimal)

    def describe(self, table: Table) -> tuple[ColumnInfo, ...]:
        kinds = detect_column_types(table)
        return tuple(ColumnInfo(c, kinds[c], guess_unit(c)) for c in table.columns)

    def import_rows(self, table: Table, mappings: Sequence[ColumnMapping]) -> ImportReport:
        return import_table(table, mappings)

    def run_batch(
        self, model_id: str, report: ImportReport, fixed: Mapping[str, Quantity] | None = None
    ) -> tuple[BatchItem, ...]:
        return run_batch(get_model(model_id), report.rows, fixed)

    def export_rejected(
        self, path: StrPath, report: ImportReport, *, overwrite: bool = False
    ) -> Path:
        return write_rejected_csv(path, report, overwrite=overwrite)


class ProjectService:
    def __init__(self, calculations: CalculationService) -> None:
        self._calc = calculations

    def create(self, folder: StrPath, name: str, description: str = "") -> Project:
        return Project.create(folder, name, description)

    def open(self, folder: StrPath) -> Project:
        return Project.open(folder)

    def add(
        self,
        project: Project,
        result: CalculationResult,
        name: str,
        *,
        notes: str = "",
        uncertain: UncertainResult | None = None,
    ) -> ProjectEntry:
        return project.add_calculation(result, name, notes=notes, uncertain=uncertain)

    def load(self, project: Project, entry_id: int) -> LoadedCalculation:
        """Reopen a project calculation by recomputing it through the registered model."""
        entry = project.entry(entry_id)
        opened = self._calc.open(project.calculation_path(entry_id))
        if opened.outcome.result is None:
            raise ValueError(opened.outcome.error or "The saved calculation can no longer be run.")
        return LoadedCalculation(
            entry,
            opened.outcome.result,
            opened.outcome.uncertain,
            opened.record.notes,
            opened.differences,
        )

    def compare(
        self, project: Project, entry_ids: Sequence[int], baseline_id: int | None = None
    ) -> Comparison:
        loaded = {e: self.load(project, e) for e in entry_ids}
        scenarios = {f"{lc.entry.name} (#{i})": lc.result for i, lc in loaded.items()}
        base = None
        if baseline_id is not None and baseline_id in loaded:
            base = f"{loaded[baseline_id].entry.name} (#{baseline_id})"
        return compare(scenarios, baseline=base)

    def export_comparison(
        self, path: StrPath, comparison: Comparison, *, overwrite: bool = False
    ) -> Path:
        return export_comparison_csv(path, comparison, overwrite=overwrite)

    def export_report(
        self,
        project: Project,
        entry_ids: Sequence[int],
        path: StrPath,
        *,
        fmt: str = "html",
        author: str = "",
        overwrite: bool = False,
    ) -> Path:
        entries = []
        for i in entry_ids:
            lc = self.load(project, i)
            entries.append(ReportEntry(lc.entry.name, lc.result, lc.uncertain, notes=lc.notes))
        doc = build_report(entries, title=f"{project.name} - calculation report", author=author)
        if fmt == "html":
            out = write_html(path, doc, overwrite=overwrite)
        elif fmt == "pdf":
            out = write_pdf(path, doc, overwrite=overwrite)
        else:
            raise ValueError("Report format must be 'html' or 'pdf'.")
        project.log_event("export_report", Path(path).name)
        return out

    def export_archive(self, project: Project, path: StrPath, *, overwrite: bool = False) -> Path:
        return project.export_archive(path, overwrite=overwrite)
