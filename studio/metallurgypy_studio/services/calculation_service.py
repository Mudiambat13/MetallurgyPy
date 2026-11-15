"""Use cases of Studio. No Qt here, so everything is testable without a display.

The service parses what the user typed, calls the Core public API, and turns
errors into messages an engineer can act on. Technical details go to the log.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from metallurgypy.core import CalculationResult, MetallurgyPyError, Quantity
from metallurgypy.records import (
    CalculationRecord,
    export_result_csv,
    export_result_json,
    load_record,
    save_record,
    verify,
)
from metallurgypy.precision import Measurement, UncertainResult, propagate_model
from metallurgypy.registry import (
    MODULE_CATALOG,
    ModelSpec,
    ModuleInfo,
    get_model,
    list_models,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class FieldInput:
    """What the user typed for one parameter: the value, its unit and an optional
    standard uncertainty (same unit). A blank uncertainty means the value is taken as exact."""

    text: str
    unit: str
    uncertainty: str = ""


@dataclass(frozen=True)
class RunOutcome:
    result: CalculationResult | None = None
    field_errors: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    uncertain: UncertainResult | None = None  # set when at least one input had an uncertainty

    @property
    def ok(self) -> bool:
        return self.result is not None


@dataclass(frozen=True)
class ModuleOverview:
    info: ModuleInfo
    models: tuple[ModelSpec, ...]

    @property
    def available(self) -> bool:
        return bool(self.models)


@dataclass(frozen=True)
class OpenedCalculation:
    record: CalculationRecord
    outcome: RunOutcome
    differences: tuple[str, ...]
    correlations: Mapping[tuple[str, str], float] = field(default_factory=dict)


def parse_number(text: str) -> float:
    """Parse a user-typed number. Accepts a decimal comma. Raises ``ValueError``."""
    cleaned = text.strip().replace(",", ".").replace(" ", "")
    if not cleaned:
        raise ValueError("empty")
    return float(cleaned)


class CalculationService:
    def models(self) -> tuple[ModelSpec, ...]:
        return list_models()

    def module_overview(self) -> tuple[ModuleOverview, ...]:
        return tuple(ModuleOverview(info, list_models(info.key)) for info in MODULE_CATALOG)

    def run(
        self,
        model_id: str,
        fields: Mapping[str, FieldInput],
        correlations: Mapping[tuple[str, str], float] | None = None,
    ) -> RunOutcome:
        try:
            spec = get_model(model_id)
        except MetallurgyPyError as exc:
            return RunOutcome(error=str(exc))

        inputs: dict[str, Quantity] = {}
        field_errors: dict[str, str] = {}
        for param in spec.parameters:
            entered = fields.get(param.name)
            if entered is None:
                field_errors[param.name] = "Required."
                continue
            try:
                inputs[param.name] = Quantity(parse_number(entered.text), entered.unit)
            except ValueError:
                field_errors[param.name] = "Enter a number, for example 2.5"
            except MetallurgyPyError as exc:
                field_errors[param.name] = str(exc)
        uncertainties: dict[str, float] = {}
        for param in spec.parameters:
            entered = fields.get(param.name)
            if entered is None or not entered.uncertainty.strip():
                continue
            try:
                u = parse_number(entered.uncertainty)
                if u < 0.0:
                    raise ValueError("negative")
                uncertainties[param.name] = u
            except ValueError:
                field_errors[param.name] = "The uncertainty must be a number >= 0, in the same unit."
        if field_errors:
            return RunOutcome(field_errors=field_errors)

        try:
            if uncertainties:
                measurements = {
                    p.name: Measurement(inputs[p.name].value, inputs[p.name].unit, uncertainties.get(p.name, 0.0))
                    for p in spec.parameters
                }
                uncertain = propagate_model(spec, measurements, correlations)
                return RunOutcome(result=uncertain.nominal, uncertain=uncertain)
            return RunOutcome(result=spec.run(inputs))
        except MetallurgyPyError as exc:
            log.info("Calculation %s rejected: %s", model_id, exc)
            message = str(exc)
            for param in spec.parameters:  # attach the message to the field it names
                if message.startswith(param.name):
                    return RunOutcome(field_errors={param.name: message})
            return RunOutcome(error=message)
        except Exception:
            log.exception("Unexpected error while running %s", model_id)
            return RunOutcome(error="Unexpected internal error. Details were written to the log.")

    # ---- persistence and export (thin wrappers over the Core) ----

    def save(
        self,
        path: str | os.PathLike[str],
        result: CalculationResult,
        *,
        name: str = "",
        notes: str = "",
        overwrite: bool = False,
        uncertain: UncertainResult | None = None,
    ) -> Path:
        return save_record(
            path, result, name=name, notes=notes, overwrite=overwrite, uncertainty=uncertain
        )

    def open(self, path: str | os.PathLike[str]) -> OpenedCalculation:
        """Reopen a saved calculation and check it still reproduces."""
        record = load_record(path)
        stored = (record.uncertainty or {}).get("inputs", {})
        fields = {}
        for name, q in record.inputs.items():
            u_text = ""
            if name in stored:
                try:
                    u_text = repr(Measurement(**{k: stored[name][k] for k in (
                        "value", "unit", "uncertainty", "kind", "coverage_factor", "method", "timestamp"
                    ) if k in stored[name]}).standard_uncertainty)
                except (MetallurgyPyError, TypeError):
                    u_text = ""
            fields[name] = FieldInput(repr(q.value), q.unit, "" if u_text in ("0.0", "") else u_text)
        correlations = {
            (str(a), str(b)): float(r)
            for a, b, r in (record.uncertainty or {}).get("correlations", [])
        }
        outcome = self.run(record.model_id, fields, correlations)
        differences = tuple(verify(record)) if outcome.ok else ()
        return OpenedCalculation(record, outcome, differences, correlations)

    def export_csv(
        self, path: str | os.PathLike[str], result: CalculationResult, *, overwrite: bool = False
    ) -> Path:
        return export_result_csv(path, result, overwrite=overwrite)

    def export_json(
        self, path: str | os.PathLike[str], result: CalculationResult, *, overwrite: bool = False
    ) -> Path:
        return export_result_json(path, result, overwrite=overwrite)
