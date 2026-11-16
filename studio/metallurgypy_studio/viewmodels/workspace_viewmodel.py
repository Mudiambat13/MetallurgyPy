"""State and logic of the Calculation Workspace, independent of Qt.

The view binds to this object: it reads fields, rows and messages, and calls
``prepare_run`` / ``apply_outcome`` (asynchronous path used by the GUI) or
``calculate`` (synchronous path used by tests and scripts).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from metallurgypy.core import CalculationResult
from metallurgypy.precision import UncertainResult, format_with_uncertainty
from metallurgypy.registry import ModelSpec
from metallurgypy_studio.services.calculation_service import (
    CalculationService,
    FieldInput,
    OpenedCalculation,
    RunOutcome,
)
from metallurgypy_studio.viewmodels.app_state import AppState, format_number

IDLE, RUNNING, OK, ERROR = "idle", "running", "ok", "error"


@dataclass(frozen=True)
class ResultRow:
    name: str
    label: str
    value_text: str
    unit: str
    kind: str
    uncertainty_text: str = ""  # propagated standard uncertainty, "" when the inputs were exact


class WorkspaceViewModel:
    def __init__(self, service: CalculationService, state: AppState) -> None:
        self._service = service
        self._state = state
        self._listeners: list[Callable[[], None]] = []
        self.spec: ModelSpec = service.models()[0]
        self.fields: dict[str, FieldInput] = {}
        self.status = IDLE
        self.result: CalculationResult | None = None
        self.field_errors: dict[str, str] = {}
        self.error: str | None = None
        self.notes = ""
        self.name = ""
        self.differences: tuple[str, ...] = ()
        self.last_saved: Path | None = None
        self.uncertain: UncertainResult | None = None
        self.correlations: dict[tuple[str, str], float] = {}
        self._reset_fields()

    # ---- observation ----

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def notify(self) -> None:
        for listener in self._listeners:
            listener()

    # ---- model and fields ----

    def models(self) -> tuple[ModelSpec, ...]:
        return self._service.models()

    def select_model(self, model_id: str) -> None:
        if model_id == self.spec.model_id:
            return
        self.spec = next(m for m in self.models() if m.model_id == model_id)
        self._reset_fields()
        self._clear_result()
        self.notify()

    def _reset_fields(self) -> None:
        self.fields = {p.name: FieldInput("", p.default_unit) for p in self.spec.parameters}

    def _clear_result(self) -> None:
        self.status = IDLE
        self.result = None
        self.field_errors = {}
        self.error = None
        self.differences = ()
        self.last_saved = None
        self.uncertain = None

    def set_field(
        self,
        name: str,
        *,
        text: str | None = None,
        unit: str | None = None,
        uncertainty: str | None = None,
    ) -> None:
        current = self.fields[name]
        self.fields[name] = FieldInput(
            current.text if text is None else text,
            current.unit if unit is None else unit,
            current.uncertainty if uncertainty is None else uncertainty,
        )

    def fill_example(self) -> None:
        """Fill the form with the illustrative (fictional) example of the model."""
        self.fields = {
            name: FieldInput(repr(q.value), q.unit) for name, q in self.spec.example.items()
        }
        self.correlations = {}
        self._clear_result()
        self.notify()

    # ---- running ----

    def prepare_run(
        self,
    ) -> tuple[str, dict[str, FieldInput], dict[tuple[str, str], float]]:
        self.status = RUNNING
        self.field_errors = {}
        self.error = None
        self.notify()
        return self.spec.model_id, dict(self.fields), dict(self.correlations)

    def apply_outcome(self, outcome: RunOutcome) -> None:
        self.field_errors = dict(outcome.field_errors)
        self.error = outcome.error
        self.differences = ()
        self.last_saved = None
        self.uncertain = outcome.uncertain
        if outcome.result is not None:
            self.result = outcome.result
            self.status = OK
            self._state.log_calculation(self.spec.title)
        else:
            self.result = None
            self.status = ERROR
        self.notify()

    def calculate(self) -> None:
        model_id, fields, correlations = self.prepare_run()
        self.apply_outcome(self._service.run(model_id, fields, correlations))

    # ---- what the view shows ----

    def rows(self) -> list[ResultRow]:
        """Result rows formatted with the display precision. The result itself is untouched."""
        if self.result is None:
            return []
        digits = self._state.settings.display_digits
        rows = []
        for o in self.result.outputs():
            u_text = ""
            if self.uncertain is not None and o.name in self.uncertain.outputs:
                u = self.uncertain.outputs[o.name].standard_uncertainty
                u_text = format_number(u, min(digits, 3)) if u > 0.0 else "0"
            rows.append(
                ResultRow(
                    o.name,
                    o.label,
                    format_number(o.quantity.value, digits),
                    o.quantity.unit,
                    o.kind,
                    u_text,
                )
            )
        return rows

    def uncertainty_budget_text(self) -> str:
        """Plain-text uncertainty budget: method, warnings, and each input's share of the variance."""
        if self.uncertain is None:
            return ""
        lines = [
            f"Method: {self.uncertain.method}",
            "Standard uncertainties u(y) (coverage factor k = 1):",
        ]
        for o in self.uncertain.outputs.values():
            if o.standard_uncertainty == 0.0:
                continue
            shown = format_with_uncertainty(o.value, o.standard_uncertainty)
            lines.append(f"  {o.label}: {shown} {o.unit}")
            for inp, share in sorted(o.contributions.items(), key=lambda kv: -abs(kv[1])):
                if abs(share) >= 0.0005:
                    lines.append(f"      {inp}: {share:.1%} of the variance")
        if self.uncertain.warnings:
            lines += ["", "Warnings:", *(f"  - {w}" for w in self.uncertain.warnings)]
        return "\n".join(lines)

    @property
    def warnings(self) -> tuple[str, ...]:
        return self.result.warnings if self.result else ()

    @property
    def assumptions(self) -> tuple[str, ...]:
        return self.result.provenance.assumptions if self.result else ()

    def details_text(self) -> str:
        if self.result is None:
            return ""
        p = self.result.provenance
        lines = [
            f"Model: {p.model_id} (version {p.model_version})",
            f"Method: {p.method}",
            f"Calculation mode: {p.calculation_mode}",
            f"Convergence: {p.convergence}",
            f"Tolerances: relative {p.tolerances.rel:g}, absolute {p.tolerances.abs:g}",
            f"MetallurgyPy {p.software_version}, calculated {p.timestamp}",
            "",
            "Equations:",
            *(f"  {e}" for e in p.equations),
            "",
            "Inputs (as used, unrounded):",
            *(f"  {k} = {q.value!r} {q.unit}" for k, q in p.inputs.items()),
        ]
        budget = self.uncertainty_budget_text()
        if budget:
            lines += ["", "Uncertainty budget:", budget]
        return "\n".join(lines)

    # ---- persistence and export ----

    def save(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
        if self.result is None:
            raise ValueError("There is no result to save.")
        saved = self._service.save(
            path,
            self.result,
            name=self.name,
            notes=self.notes,
            overwrite=overwrite,
            uncertain=self.uncertain,
        )
        self.last_saved = saved
        self._state.settings.add_recent(saved)
        self.notify()
        return saved

    def export_csv(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
        if self.result is None:
            raise ValueError("There is no result to export.")
        return self._service.export_csv(path, self.result, overwrite=overwrite)

    def export_json(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
        if self.result is None:
            raise ValueError("There is no result to export.")
        return self._service.export_json(path, self.result, overwrite=overwrite)

    def open_file(self, path: str | os.PathLike[str]) -> OpenedCalculation:
        """Reopen a saved calculation: restore model, inputs and notes, recompute, verify."""
        opened = self._service.open(path)
        record = opened.record
        self.spec = next(m for m in self.models() if m.model_id == record.model_id)
        self.fields = {
            name: FieldInput(
                repr(q.value),
                q.unit,
                opened.outcome.uncertain.inputs[name].standard_uncertainty.__repr__()
                if opened.outcome.uncertain is not None
                and opened.outcome.uncertain.inputs[name].standard_uncertainty > 0.0
                else "",
            )
            for name, q in record.inputs.items()
        }
        self.correlations = dict(opened.correlations)
        self.name, self.notes = record.name, record.notes
        self.apply_outcome(opened.outcome)
        self.differences = opened.differences
        self.last_saved = Path(path)
        self._state.settings.add_recent(path)
        self.notify()
        return opened
