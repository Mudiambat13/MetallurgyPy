"""Result objects shared by all models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

from metallurgypy.core.provenance import Provenance
from metallurgypy.core.units import Quantity

ValueKind = Literal["calculated", "estimated", "measured"]


@dataclass(frozen=True)
class OutputItem:
    """One named output value. ``kind`` lets interfaces tell calculated, estimated
    and measured values apart."""

    name: str
    label: str
    quantity: Quantity
    kind: ValueKind = "calculated"


@dataclass(frozen=True)
class ChartData:
    """The data behind a result chart, so every interface plots exactly the result.

    ``kind="bar"`` plots ``values`` against ``categories``. ``kind="line"`` plots
    ``values`` against the numeric ``x``.
    """

    title: str
    categories: tuple[str, ...]
    values: tuple[float, ...]
    unit: str
    source: str
    kind: Literal["bar", "line"] = "bar"
    x: tuple[float, ...] = ()
    x_label: str = ""
    y_label: str = ""


@dataclass(frozen=True, kw_only=True)
class CalculationResult(ABC):
    """Base class of results. Values are stored unrounded; rounding is for display only."""

    provenance: Provenance
    warnings: tuple[str, ...] = ()

    @abstractmethod
    def outputs(self) -> tuple[OutputItem, ...]:
        """All output values in presentation order."""

    def chart_data(self) -> ChartData | None:
        """Data for the default chart of this result, if it has one."""
        return None

    def get(self, name: str) -> Quantity:
        for item in self.outputs():
            if item.name == name:
                return item.quantity
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outputs": [
                {
                    "name": o.name,
                    "label": o.label,
                    "value": o.quantity.value,
                    "unit": o.quantity.unit,
                    "kind": o.kind,
                }
                for o in self.outputs()
            ],
            "warnings": list(self.warnings),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, kw_only=True)
class GenericResult(CalculationResult):
    """Result made of a flat list of outputs (used by most models)."""

    items: tuple[OutputItem, ...]
    chart: ChartData | None = None

    def outputs(self) -> tuple[OutputItem, ...]:
        return self.items

    def chart_data(self) -> ChartData | None:
        return self.chart
