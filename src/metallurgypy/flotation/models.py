"""Flotation. Equations: docs/scientific_methods/flotation.md."""

from __future__ import annotations

import math

from metallurgypy.core.exceptions import InvalidParameterError
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.results import ChartData, GenericResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances
from metallurgypy.mass_balance.models import TwoProductBalance

_Q = Quantity | float


class FlotationBalance(TwoProductBalance):
    """Concentrate/tailings balance of a flotation circuit from the three grades.

    Same equations and domain rules as :class:`TwoProductBalance`; the flotation
    wording is: recovery of metal to the concentrate, mass pull (mass yield) and
    enrichment ratio.
    """

    MODEL_ID = "flotation.balance"


class FlotationKinetics(BaseModel):
    """Classical first-order flotation recovery curve with an ultimate recovery."""

    MODEL_ID = "flotation.kinetics_first_order"
    EQUATIONS = (
        "R(t) = R_inf * (1 - exp(-k * t))",
        "t_95 = ln(20) / k   (time to reach 95 % of R_inf)",
    )
    ASSUMPTIONS = (
        "A single rate constant k describes the whole feed (one floatability class). Real ores usually need several.",
        "R_inf and k are empirical, valid for the ore, reagents and cell conditions where they were fitted; MetallurgyPy supplies none.",
        "Time is flotation (residence) time in the cell, with no scale-up factor applied.",
    )
    _POINTS = 60

    def __init__(
        self,
        ultimate_recovery: _Q,
        rate_constant: _Q,
        time: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        r_inf = qty(
            "ultimate_recovery",
            ultimate_recovery,
            unit="fraction",
            allowed=("fraction", "%"),
            fraction=True,
        )
        if r_inf.to("fraction").value == 0.0:
            raise InvalidParameterError("ultimate_recovery must be strictly positive.")
        self._inputs = {
            "ultimate_recovery": r_inf,
            "rate_constant": qty("rate_constant", rate_constant, unit="1/min", positive=True),
            "time": qty("time", time, unit="min", positive=True),
        }

    def calculate(self) -> GenericResult:
        r_inf = self._inputs["ultimate_recovery"].to("fraction").value
        k = self._inputs["rate_constant"].to("1/min").value
        t = self._inputs["time"].to("min").value
        recovery = r_inf * (1.0 - math.exp(-k * t))
        xs = tuple(t * j / self._POINTS for j in range(self._POINTS + 1))
        ys = tuple(r_inf * (1.0 - math.exp(-k * x)) for x in xs)
        chart = ChartData(
            title="Flotation recovery vs time",
            categories=(),
            values=ys,
            unit="fraction",
            source=f"FlotationKinetics {self.MODEL_VERSION}, calculated from the given R_inf and k",
            kind="line",
            x=xs,
            x_label="Time (min)",
            y_label="Recovery (fraction)",
        )
        warnings = []
        if k * t < 0.05:
            warnings.append(
                "k * t is very small: the recovery is still in the initial linear part of the curve."
            )
        return self._result(
            [
                out("recovery", "Recovery at time t", recovery, "fraction"),
                out(
                    "remaining_recoverable",
                    "Recoverable fraction not yet recovered",
                    r_inf - recovery,
                    "fraction",
                ),
                out(
                    "time_95", "Time to reach 95 % of ultimate recovery", math.log(20.0) / k, "min"
                ),
            ],
            chart=chart,
            warnings=warnings,
        )
