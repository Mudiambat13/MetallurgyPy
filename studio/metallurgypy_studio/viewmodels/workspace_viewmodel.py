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

    def set_field(self, name: str, *, text: str | None = None, unit: str | None = None) -> None:
        current = self.fields[name]
        self.fields[name] = FieldInput(
            current.text if text is None else text, current.unit if unit is None else unit
        )

    def fill_example(self) -> None:
        """Fill the form with the illustrative (fictional) example of the model."""
        self.fields = {
            name: FieldInput(repr(q.value), q.unit) for name, q in self.spec.example.items()
        }
        self._clear_result()
        self.notify()

    # ---- running ----

    def prepare_run(self) -> tuple[str, dict[str, FieldInput]]:
        self.status = RUNNING
        self.field_errors = {}
        self.error = None
        self.notify()
        return self.spec.model_id, dict(self.fields)

    def apply_outcome(self, outcome: RunOutcome) -> None:
        self.field_errors = dict(outcome.field_errors)
        self.error = outcome.error
        self.differences = ()
        self.last_saved = None
        if outcome.result is not None:
            self.result = outcome.result
            self.status = OK
            self._state.log_calculation(self.spec.title)
        else:
            self.result = None
            self.status = ERROR
        self.notify()

    def calculate(self) -> None:
        model_id, fields = self.prepare_run()
        self.apply_outcome(self._service.run(model_id, fields))

    # ---- what the view shows ----

    def rows(self) -> list[ResultRow]:
        """Result rows formatted with the display precision. The result itself is untouched."""
        if self.result is None:
            return []
        digits = self._state.settings.display_digits
        return [
            ResultRow(o.name, o.label, format_number(o.quantity.value, digits), o.quantity.unit, o.kind)
            for o in self.result.outputs()
        ]

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
        return "\n".join(lines)

    # ---- persistence and export ----

    def save(self, path: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
        if self.result is None:
            raise ValueError("There is no result to save.")
        saved = self._service.save(path, self.result, name=self.name, notes=self.notes, overwrite=overwrite)
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
            name: FieldInput(repr(q.value), q.unit) for name, q in record.inputs.items()
        }
        self.name, self.notes = record.name, record.notes
        self.apply_outcome(opened.outcome)
        self.differences = opened.differences
        self.last_saved = Path(path)
        self._state.settings.add_recent(path)
        self.notify()
        return opened
