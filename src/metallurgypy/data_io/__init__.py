"""Import of tabular data (CSV, JSON, optional XLSX) into validated quantities.

Source files are only ever read. Rows that cannot be used are *reported*
(row number and reasons), never silently dropped or "fixed".
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metallurgypy.core.exceptions import MetallurgyPyError
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity
from metallurgypy.records import _write_text, csv_safe
from metallurgypy.registry import ModelSpec, get_model

__all__ = [
    "BatchItem",
    "ColumnMapping",
    "ImportReport",
    "ImportedRow",
    "RejectedRow",
    "Table",
    "detect_column_types",
    "guess_unit",
    "import_table",
    "read_table",
    "run_batch",
    "write_rejected_csv",
]

_DECIMAL_COMMA = re.compile(r"^\s*[-+]?\d+,\d+\s*$")
_HEADER_UNIT = re.compile(r"[\[(]\s*([^\])]+?)\s*[\])]\s*$")


class DataImportError(MetallurgyPyError):
    """The file cannot be read as a table."""


@dataclass(frozen=True)
class Table:
    """Raw table: header names and rows of raw cell values (str, int, float or None)."""

    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    source: str = ""
    delimiter: str | None = None
    decimal: str = "."


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        first = sample.splitlines()[0] if sample else ""
        return max(",;\t|", key=first.count)


def read_table(
    path: str | os.PathLike[str],
    *,
    delimiter: str | None = None,
    decimal: str | None = None,
    encoding: str = "utf-8-sig",
    sheet: str | None = None,
) -> Table:
    """Read ``.csv``/``.txt``/``.tsv``, ``.json`` or ``.xlsx`` (needs ``openpyxl``)."""
    source = Path(path)
    if not source.is_file():
        raise DataImportError(f"{source} does not exist or is not a file.")
    suffix = source.suffix.lower()
    if suffix in (".csv", ".txt", ".tsv"):
        return _read_delimited(source, delimiter, decimal, encoding)
    if suffix == ".json":
        return _read_json(source, encoding)
    if suffix in (".xlsx", ".xlsm"):
        return _read_xlsx(source, sheet)
    raise DataImportError(
        f"Unsupported file type {suffix!r}. Use .csv, .tsv, .txt, .json or .xlsx."
    )


def _read_delimited(
    source: Path, delimiter: str | None, decimal: str | None, encoding: str
) -> Table:
    try:
        text = source.read_text(encoding=encoding)
    except UnicodeDecodeError:
        raise DataImportError(
            f"{source.name} is not valid {encoding}. Pass encoding='latin-1' (or the right one)."
        ) from None
    if not text.strip():
        raise DataImportError(f"{source.name} is empty.")
    delim = delimiter or (
        "\t" if source.suffix.lower() == ".tsv" else _sniff_delimiter(text[:4096])
    )
    records = [
        r for r in csv.reader(io.StringIO(text), delimiter=delim) if any(c.strip() for c in r)
    ]
    header, *body = records
    columns = tuple(c.strip() for c in header)
    if len(set(columns)) != len(columns) or "" in columns:
        raise DataImportError("Column names must be non-empty and unique.")
    rows = tuple(tuple(c.strip() for c in r) for r in body)
    if decimal is None:
        if delim == ",":
            decimal = "."
        else:
            decimal = "," if any(_DECIMAL_COMMA.match(c) for r in rows for c in r) else "."
    if decimal not in (".", ","):
        raise DataImportError("decimal must be '.' or ','.")
    return Table(columns, rows, source.name, delim, decimal)


def _read_json(source: Path, encoding: str) -> Table:
    try:
        data = json.loads(source.read_text(encoding=encoding))
    except json.JSONDecodeError as exc:
        raise DataImportError(f"{source.name} is not valid JSON: {exc}") from None
    if isinstance(data, dict) and "columns" in data and "rows" in data:
        columns = tuple(str(c) for c in data["columns"])
        rows = tuple(tuple(r) for r in data["rows"])
    elif isinstance(data, list) and data and all(isinstance(r, dict) for r in data):
        columns = tuple(dict.fromkeys(k for r in data for k in r))
        rows = tuple(tuple(r.get(c) for c in columns) for r in data)
    else:
        raise DataImportError(
            "JSON must be a list of objects or {'columns': [...], 'rows': [[...]]}."
        )
    return Table(columns, rows, source.name, None, ".")


def _read_xlsx(source: Path, sheet: str | None) -> Table:
    try:
        import openpyxl
    except ImportError:
        raise DataImportError(
            "Reading .xlsx needs the optional 'openpyxl' package. Install it, or export the sheet to CSV."
        ) from None
    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    try:
        ws = workbook[sheet] if sheet else workbook.active
        records = [r for r in ws.iter_rows(values_only=True) if any(c not in (None, "") for c in r)]
    except KeyError:
        raise DataImportError(f"Sheet {sheet!r} not found in {source.name}.") from None
    finally:
        workbook.close()
    if not records:
        raise DataImportError(f"{source.name} has no data.")
    header, *body = records
    columns = tuple("" if c is None else str(c).strip() for c in header)
    if len(set(columns)) != len(columns) or "" in columns:
        raise DataImportError("Column names must be non-empty and unique.")
    return Table(columns, tuple(tuple(r) for r in body), source.name, None, ".")


def _to_float(cell: Any, decimal: str) -> float:
    if isinstance(cell, bool):
        raise ValueError("a boolean is not a number")
    if isinstance(cell, (int, float)):
        value = float(cell)
    else:
        if cell is None:
            raise ValueError("empty")
        text = str(cell).strip().replace("\u00a0", "").replace(" ", "")
        if not text:
            raise ValueError("empty")
        if decimal == ",":
            text = text.replace(".", "").replace(",", ".")
        value = float(text)
    if not math.isfinite(value):
        raise ValueError("not finite")
    return value


def detect_column_types(table: Table, *, threshold: float = 0.8) -> dict[str, str]:
    """``'number'`` if at least ``threshold`` of the non-empty cells parse as numbers, else ``'text'``.

    A few typos therefore do not turn a numeric column into text; the bad cells are
    reported row by row when the data is imported.
    """
    kinds: dict[str, str] = {}
    for i, name in enumerate(table.columns):
        cells = [r[i] for r in table.rows if i < len(r) and r[i] not in (None, "")]
        good = 0
        for c in cells:
            try:
                _to_float(c, table.decimal)
                good += 1
            except ValueError:
                pass
        kinds[name] = "number" if cells and good / len(cells) >= threshold else "text"
    return kinds


def guess_unit(header: str) -> str | None:
    """Unit written at the end of a header, e.g. ``'Cu grade [%]'`` -> ``'%'`` (only if known)."""
    m = _HEADER_UNIT.search(header)
    if not m:
        return None
    try:
        Quantity(0.0, m.group(1))
    except MetallurgyPyError:
        return None
    return m.group(1)


@dataclass(frozen=True)
class ColumnMapping:
    """How one file column becomes one named value (``kind='number'`` needs a ``unit``)."""

    column: str
    name: str
    unit: str | None = None
    kind: str = "number"  # "number" | "text"
    required: bool = True
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True)
class ImportedRow:
    row_number: int  # 1-based data row (header excluded)
    values: Mapping[str, Quantity | str]


@dataclass(frozen=True)
class RejectedRow:
    row_number: int
    reasons: tuple[str, ...]
    raw: tuple[Any, ...]


@dataclass(frozen=True)
class ImportReport:
    source: str
    rows: tuple[ImportedRow, ...]
    rejected: tuple[RejectedRow, ...]
    warnings: tuple[str, ...] = field(default=())

    @property
    def total(self) -> int:
        return len(self.rows) + len(self.rejected)


def import_table(table: Table, mappings: Sequence[ColumnMapping]) -> ImportReport:
    """Validate every row against ``mappings``; unusable rows are reported, not dropped silently."""
    index = {name: i for i, name in enumerate(table.columns)}
    for m in mappings:
        if m.column not in index:
            raise DataImportError(
                f"Column {m.column!r} is not in the file. Found: {', '.join(table.columns)}"
            )
        if m.kind == "number" and not m.unit:
            raise DataImportError(f"Column {m.column!r} is numeric: give its unit explicitly.")
        if m.kind not in ("number", "text"):
            raise DataImportError(f"Unknown kind {m.kind!r} for column {m.column!r}.")
        if m.kind == "number":
            try:
                Quantity(0.0, m.unit or "")
            except MetallurgyPyError as exc:
                raise DataImportError(f"Column {m.column!r}: {exc}") from None
    names = [m.name for m in mappings]
    if len(set(names)) != len(names):
        raise DataImportError("Two columns are mapped to the same name.")

    good: list[ImportedRow] = []
    bad: list[RejectedRow] = []
    for n, raw in enumerate(table.rows, start=1):
        reasons: list[str] = []
        values: dict[str, Quantity | str] = {}
        for m in mappings:
            cell = raw[index[m.column]] if index[m.column] < len(raw) else None
            if cell is None or (isinstance(cell, str) and not cell.strip()):
                if m.required:
                    reasons.append(f"{m.column}: missing value")
                continue
            if m.kind == "text":
                values[m.name] = str(cell).strip()
                continue
            try:
                number = _to_float(cell, table.decimal)
            except ValueError as exc:
                reasons.append(f"{m.column}: {cell!r} is not a valid number ({exc})")
                continue
            if m.minimum is not None and number < m.minimum:
                reasons.append(f"{m.column}: {number:g} is below the minimum {m.minimum:g}")
            elif m.maximum is not None and number > m.maximum:
                reasons.append(f"{m.column}: {number:g} is above the maximum {m.maximum:g}")
            else:
                values[m.name] = Quantity(number, m.unit or "")
        if reasons:
            bad.append(RejectedRow(n, tuple(reasons), tuple(raw)))
        else:
            good.append(ImportedRow(n, values))
    warnings: tuple[str, ...] = ()
    if bad:
        warnings = (f"{len(bad)} of {len(table.rows)} rows were rejected; see the report.",)
    return ImportReport(table.source, tuple(good), tuple(bad), warnings)


@dataclass(frozen=True)
class BatchItem:
    row_number: int
    result: CalculationResult | None
    error: str | None = None


def run_batch(
    model: str | ModelSpec,
    rows: Sequence[ImportedRow],
    fixed: Mapping[str, Quantity] | None = None,
) -> tuple[BatchItem, ...]:
    """Run one registered model on each imported row (``fixed`` supplies shared parameters).

    A failing row gives an item with ``error`` set; the other rows still run.
    """
    spec = get_model(model) if isinstance(model, str) else model
    items: list[BatchItem] = []
    for row in rows:
        inputs: dict[str, Quantity] = dict(fixed or {})
        inputs.update({k: v for k, v in row.values.items() if isinstance(v, Quantity)})
        try:
            items.append(BatchItem(row.row_number, spec.run(inputs)))
        except MetallurgyPyError as exc:
            items.append(BatchItem(row.row_number, None, str(exc)))
    return tuple(items)


def write_rejected_csv(
    path: str | os.PathLike[str], report: ImportReport, *, overwrite: bool = False
) -> Path:
    """Write the rejected rows and their reasons to a *new* file (the source is never touched)."""
    buffer = io.StringIO()
    w = csv.writer(buffer, lineterminator="\n")
    w.writerow(["row", "reasons", "raw_values"])
    for r in report.rejected:
        w.writerow(
            [
                r.row_number,
                csv_safe(" | ".join(r.reasons)),
                csv_safe(" ; ".join("" if c is None else str(c) for c in r.raw)),
            ]
        )
    target = Path(path)
    _write_text(target, buffer.getvalue(), overwrite=overwrite)
    return target
