"""Run a calculation on the Qt thread pool and deliver the outcome to the GUI thread."""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import QObject, QRunnable, Signal

from metallurgypy_studio.services.calculation_service import (
    CalculationService,
    FieldInput,
    RunOutcome,
)


class CalcSignals(QObject):
    finished = Signal(object)  # carries a RunOutcome


class CalcWorker(QRunnable):
    """The caller must keep a reference until ``finished`` is received.

    Auto-deletion is disabled so the signal object cannot disappear while a
    queued signal is still in flight.
    """

    def __init__(
        self, service: CalculationService, model_id: str, fields: Mapping[str, FieldInput]
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.signals = CalcSignals()
        self._service = service
        self._model_id = model_id
        self._fields = dict(fields)

    def run(self) -> None:
        outcome: RunOutcome = self._service.run(self._model_id, self._fields)
        self.signals.finished.emit(outcome)
