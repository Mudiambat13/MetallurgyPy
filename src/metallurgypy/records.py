"""Saving, reopening, verifying and exporting calculations.

File format
-----------
A calculation is stored as UTF-8 JSON (``format = "metallurgypy.calculation"``)
with an integer ``format_version``. Floats are written with their shortest
round-trip representation, so no precision is lost. Non-finite numbers are
refused.

Security
--------
A file is data. Reopening one looks the model up by its ``model_id`` in the
registry and re-runs it from the stored inputs; nothing in the file is ever
imported or executed.

Migration
---------
Older versions are upgraded through ``_MIGRATIONS`` (``{from_version: function}``).
Only version 1 exists so far. A file written by a *newer* version is refused.
"""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from metallurgypy.core.exceptions import MetallurgyPyError, RecordFormatError
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances
from metallurgypy.registry import get_model
from metallurgypy.version import __version__

FORMAT_NAME = "metallurgypy.calculation"
FORMAT_VERSION = 1
FILE_SUFFIX = ".mpy.json"

_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}


@dataclass(frozen=True)
class CalculationRecord:
    """A saved calculation: inputs, the result as it was stored, and free-text notes."""

    model_id: str
    inputs: dict[str, Quantity]
    result: dict[str, Any]
    name: str = ""
    notes: str = ""
    format_version: int = FORMAT_VERSION
    saved_with: str = ""


def _write_text(path: Path, text: str, *, overwrite: bool) -> None:
    """Write ``text`` atomically; refuse to replace an existing file unless allowed."""
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; refusing to overwrite it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def save_record(
    path: str | os.PathLike[str],
    result: CalculationResult,
    *,
    name: str = "",
    notes: str = "",
    overwrite: bool = False,
) -> Path:
    """Save ``result`` with its inputs so it can be reopened and verified."""
    target = Path(path)
    payload = {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "saved_with": __version__,
        "name": name,
        "notes": notes,
        "model_id": result.provenance.model_id,
        "inputs": {k: {"value": q.value, "unit": q.unit} for k, q in result.provenance.inputs.items()},
        "result": result.to_dict(),
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    _write_text(target, text, overwrite=overwrite)
    return target


def _parse_inputs(raw: Any) -> dict[str, Quantity]:
    if not isinstance(raw, dict) or not raw:
        raise RecordFormatError("'inputs' must be a non-empty object.")
    inputs: dict[str, Quantity] = {}
    for key, item in raw.items():
        if not isinstance(item, dict) or "value" not in item or "unit" not in item:
            raise RecordFormatError(f"Input {key!r} must have 'value' and 'unit'.")
        try:
            inputs[str(key)] = Quantity(item["value"], item["unit"])
        except MetallurgyPyError as exc:
            raise RecordFormatError(f"Input {key!r} is invalid: {exc}") from None
    return inputs


def load_record(path: str | os.PathLike[str]) -> CalculationRecord:
    """Read a saved calculation. Raises :class:`RecordFormatError` if it is not usable."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RecordFormatError(f"{source.name} is not valid JSON: {exc}") from None
    if not isinstance(data, dict) or data.get("format") != FORMAT_NAME:
        raise RecordFormatError(f"{source.name} is not a MetallurgyPy calculation file.")
    version = data.get("format_version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise RecordFormatError("'format_version' must be a positive integer.")
    if version > FORMAT_VERSION:
        raise RecordFormatError(
            f"{source.name} uses format version {version}, newer than the version "
            f"{FORMAT_VERSION} this release understands. Update MetallurgyPy."
        )
    while version < FORMAT_VERSION:
        data = _MIGRATIONS[version](data)
        version += 1

    model_id = data.get("model_id")
    result = data.get("result")
    if not isinstance(model_id, str) or not model_id:
        raise RecordFormatError("'model_id' must be a non-empty string.")
    if not isinstance(result, dict) or not isinstance(result.get("outputs"), list):
        raise RecordFormatError("'result' must be an object with an 'outputs' list.")
    return CalculationRecord(
        model_id=model_id,
        inputs=_parse_inputs(data.get("inputs")),
        result=result,
        name=str(data.get("name", "")),
        notes=str(data.get("notes", "")),
        format_version=version,
        saved_with=str(data.get("saved_with", "")),
    )


def recompute(record: CalculationRecord) -> CalculationResult:
    """Re-run the registered model with the stored inputs."""
    return get_model(record.model_id).run(record.inputs)


def verify(
    record: CalculationRecord, tolerances: Tolerances = DEFAULT_TOLERANCES
) -> list[str]:
    """Compare the stored outputs with a fresh calculation.

    Returns a list of human-readable differences; an empty list means the saved
    result is reproduced by the installed version of the model.
    """
    fresh = recompute(record)
    differences: list[str] = []
    stored_version = record.result.get("provenance", {}).get("model_version")
    if stored_version != fresh.provenance.model_version:
        differences.append(
            f"model version changed: saved with {stored_version}, now {fresh.provenance.model_version}"
        )
    fresh_by_name = {o.name: o.quantity for o in fresh.outputs()}
    for item in record.result["outputs"]:
        name = item.get("name")
        if name not in fresh_by_name:
            differences.append(f"output {name!r} no longer exists")
            continue
        now = fresh_by_name[name]
        if item.get("unit") != now.unit:
            differences.append(f"{name}: unit changed from {item.get('unit')} to {now.unit}")
        elif not tolerances.isclose(float(item["value"]), now.value):
            differences.append(f"{name}: saved {item['value']!r}, recomputed {now.value!r}")
    return differences


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #


def result_to_csv(result: CalculationResult) -> str:
    """CSV with inputs then outputs. Values keep full round-trip precision."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["section", "name", "label", "value", "unit", "kind"])
    for name, quantity in result.provenance.inputs.items():
        writer.writerow(["input", name, name, repr(quantity.value), quantity.unit, "input"])
    for item in result.outputs():
        writer.writerow(
            ["output", item.name, item.label, repr(item.quantity.value), item.quantity.unit, item.kind]
        )
    return buffer.getvalue()


def export_result_csv(
    path: str | os.PathLike[str], result: CalculationResult, *, overwrite: bool = False
) -> Path:
    target = Path(path)
    _write_text(target, result_to_csv(result), overwrite=overwrite)
    return target


def export_result_json(
    path: str | os.PathLike[str], result: CalculationResult, *, overwrite: bool = False
) -> Path:
    target = Path(path)
    text = json.dumps(result.to_dict(), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    _write_text(target, text, overwrite=overwrite)
    return target
