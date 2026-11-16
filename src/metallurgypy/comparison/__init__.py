"""Side-by-side comparison of calculation scenarios (inputs, outputs, differences)."""

from __future__ import annotations

import csv
import io
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from metallurgypy.core.exceptions import InvalidParameterError, MetallurgyPyError
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity
from metallurgypy.records import _write_text, csv_safe

__all__ = ["Comparison", "ComparisonRow", "compare", "comparison_to_csv", "export_comparison_csv"]


@dataclass(frozen=True)
class ComparisonRow:
    """One quantity across scenarios. ``None`` = the scenario does not have it.

    ``difference`` and ``relative_difference`` are against the baseline scenario, in
    the baseline's unit. ``relative_difference`` is ``None`` when the baseline is 0.
    """

    section: str  # "input" or "output"
    name: str
    unit: str
    values: Mapping[str, float | None]
    difference: Mapping[str, float | None]
    relative_difference: Mapping[str, float | None]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Comparison:
    baseline: str
    scenarios: tuple[str, ...]
    rows: tuple[ComparisonRow, ...]
    warnings: tuple[str, ...] = ()

    def outputs(self) -> tuple[ComparisonRow, ...]:
        return tuple(r for r in self.rows if r.section == "output")

    def inputs(self) -> tuple[ComparisonRow, ...]:
        return tuple(r for r in self.rows if r.section == "input")


def compare(
    scenarios: Mapping[str, CalculationResult], *, baseline: str | None = None
) -> Comparison:
    """Compare two or more results. Values are converted to the baseline's unit; a quantity
    whose dimension differs between scenarios is flagged, not forced."""
    if len(scenarios) < 2:
        raise InvalidParameterError("Comparing needs at least two scenarios.")
    names = tuple(scenarios)
    base = baseline if baseline is not None else names[0]
    if base not in scenarios:
        raise InvalidParameterError(
            f"Baseline {base!r} is not one of the scenarios: {', '.join(names)}."
        )

    warnings: list[str] = []
    models = {r.provenance.model_id for r in scenarios.values()}
    if len(models) > 1:
        warnings.append(
            "Scenarios come from different models: only quantities with the same name are compared."
        )
    modes = {r.provenance.calculation_mode for r in scenarios.values()}
    if len(modes) > 1:
        warnings.append(
            "Scenarios use different calculation modes: " + ", ".join(sorted(modes)) + "."
        )

    rows: list[ComparisonRow] = []
    for section in ("input", "output"):
        per: dict[str, dict[str, tuple[float, str]]] = {}
        for sname, result in scenarios.items():
            items = (
                {k: (q.value, q.unit) for k, q in result.provenance.inputs.items()}
                if section == "input"
                else {o.name: (o.quantity.value, o.quantity.unit) for o in result.outputs()}
            )
            for key, vu in items.items():
                per.setdefault(key, {})[sname] = vu
        for key, found in per.items():
            ref = found.get(base)
            unit = ref[1] if ref else next(iter(found.values()))[1]
            values: dict[str, float | None] = {}
            notes: list[str] = []
            for sname in names:
                if sname not in found:
                    values[sname] = None
                    continue
                v, u = found[sname]
                if u == unit:
                    values[sname] = v
                    continue
                try:
                    values[sname] = Quantity(v, u).to(unit).value
                except MetallurgyPyError:
                    values[sname] = None
                    notes.append(f"{sname}: unit {u} is not comparable with {unit}")
            base_value = values.get(base)
            diff: dict[str, float | None] = {}
            rel: dict[str, float | None] = {}
            for sname in names:
                cur = values[sname]
                if sname == base or cur is None or base_value is None:
                    diff[sname] = rel[sname] = None
                    continue
                diff[sname] = cur - base_value
                rel[sname] = None if base_value == 0.0 else (cur - base_value) / abs(base_value)
            if (
                section == "input"
                and len({v for v in values.values() if v is not None}) <= 1
                and None not in values.values()
            ):
                continue  # identical inputs are not interesting in the comparison
            rows.append(ComparisonRow(section, key, unit, values, diff, rel, tuple(notes)))
    return Comparison(base, names, tuple(rows), tuple(warnings))


def comparison_to_csv(comparison: Comparison) -> str:
    buffer = io.StringIO()
    w = csv.writer(buffer, lineterminator="\n")
    head = ["section", "name", "unit"]
    for s in comparison.scenarios:
        head.append(csv_safe(s))
    for s in comparison.scenarios:
        if s != comparison.baseline:
            head += [csv_safe(f"{s} - {comparison.baseline}"), csv_safe(f"{s} relative")]
    w.writerow(head)
    for r in comparison.rows:
        line: list[str] = [r.section, csv_safe(r.name), csv_safe(r.unit)]
        line += ["" if r.values[s] is None else repr(r.values[s]) for s in comparison.scenarios]
        for s in comparison.scenarios:
            if s != comparison.baseline:
                d, rel = r.difference[s], r.relative_difference[s]
                line += ["" if d is None else repr(d), "" if rel is None else repr(rel)]
        w.writerow(line)
    return buffer.getvalue()


def export_comparison_csv(
    path: str | os.PathLike[str], comparison: Comparison, *, overwrite: bool = False
) -> Path:
    target = Path(path)
    _write_text(target, comparison_to_csv(comparison), overwrite=overwrite)
    return target
