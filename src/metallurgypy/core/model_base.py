"""Base class that removes boilerplate from models.

A model declares ``MODEL_ID``, ``MODEL_VERSION``, ``EQUATIONS`` and
``ASSUMPTIONS`` as class attributes, stores its normalised inputs in
``self._inputs`` and builds its result with :meth:`_result`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from metallurgypy.core.modes import CalculationMode, resolve_mode
from metallurgypy.core.provenance import Provenance
from metallurgypy.core.results import ChartData, GenericResult, OutputItem
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances


class BaseModel:
    MODEL_ID: ClassVar[str]
    MODEL_VERSION: ClassVar[str] = "1.0"
    EQUATIONS: ClassVar[tuple[str, ...]] = ()
    ASSUMPTIONS: ClassVar[tuple[str, ...]] = ()
    METHOD: ClassVar[str] = "Closed-form evaluation in float64"
    SUPPORTED_MODES: ClassVar[tuple[CalculationMode, ...]] = (CalculationMode.STANDARD,)

    def __init__(
        self,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        self._mode = resolve_mode(mode, self.SUPPORTED_MODES)
        self._tol = tolerances
        self._inputs: dict[str, Quantity] = {}

    def _result(
        self,
        items: Iterable[OutputItem],
        *,
        chart: ChartData | None = None,
        warnings: Iterable[str] = (),
        convergence: str = "not_applicable",
        method: str | None = None,
    ) -> GenericResult:
        provenance = Provenance(
            model_id=self.MODEL_ID,
            model_version=self.MODEL_VERSION,
            method=method or self.METHOD,
            equations=self.EQUATIONS,
            assumptions=self.ASSUMPTIONS,
            inputs=dict(self._inputs),
            tolerances=self._tol,
            calculation_mode=self._mode.value,
            convergence=convergence,
        )
        return GenericResult(
            provenance=provenance, warnings=tuple(warnings), items=tuple(items), chart=chart
        )


def out(name: str, label: str, value: float, unit: str) -> OutputItem:
    """Shorthand for a calculated output."""
    return OutputItem(name, label, Quantity(value, unit))
