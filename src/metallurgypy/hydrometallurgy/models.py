"""Hydrometallurgy. Equations: docs/scientific_methods/hydrometallurgy.md.

Stoichiometric and balance calculations are kept apart from kinetics: the
first-order leaching curve is an empirical model, not a mechanism.
"""

from __future__ import annotations

import math

from metallurgypy.core.exceptions import InvalidParameterError, ModelDomainError
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.results import ChartData, GenericResult
from metallurgypy.core.units import GRADE_UNITS, Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

_Q = Quantity | float


class LeachingYield(BaseModel):
    """Extraction yield of a leach from solid assays, cross-checked with the solution assay."""

    MODEL_ID = "hydrometallurgy.leaching_yield"
    EQUATIONS = (
        "m_feed = F * g_feed",
        "m_residue = R * g_res",
        "extraction (solids) = 1 - m_residue / m_feed",
        "m_dissolved (solids) = m_feed - m_residue",
        "m_solution = V * C",
        "gap = m_dissolved (solids) - m_solution",
    )
    ASSUMPTIONS = (
        "Single metal, same dry basis for solid masses and grades.",
        "The solid-based extraction is the reference; the solution-based amount is a cross-check.",
        "The gap is a reconciliation difference, not a verdict: assay error, entrained or wash solution, "
        "precipitation and sampling all contribute. MetallurgyPy sets no acceptance threshold.",
    )

    def __init__(
        self,
        feed_mass: _Q,
        feed_grade: _Q,
        residue_mass: _Q,
        residue_grade: _Q,
        solution_volume: _Q,
        solution_concentration: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "feed_mass": qty("feed_mass", feed_mass, unit="t", positive=True),
            "feed_grade": qty(
                "feed_grade", feed_grade, unit="fraction", allowed=GRADE_UNITS, fraction=True
            ),
            "residue_mass": qty("residue_mass", residue_mass, unit="t", positive=True),
            "residue_grade": qty(
                "residue_grade", residue_grade, unit="fraction", allowed=GRADE_UNITS, fraction=True
            ),
            "solution_volume": qty(
                "solution_volume", solution_volume, unit="m3", non_negative=True
            ),
            "solution_concentration": qty(
                "solution_concentration", solution_concentration, unit="g/L", non_negative=True
            ),
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        feed_kg = i["feed_mass"].to("kg").value
        residue_kg = i["residue_mass"].to("kg").value
        m_feed = feed_kg * i["feed_grade"].to("fraction").value
        m_res = residue_kg * i["residue_grade"].to("fraction").value
        if m_feed == 0.0:
            raise ModelDomainError(
                "Feed contains no metal (grade is zero): extraction is undefined."
            )
        dissolved = m_feed - m_res
        m_solution = (
            i["solution_volume"].to("m3").value * i["solution_concentration"].to("kg/m3").value
        )
        warnings = []
        if m_res > m_feed:
            warnings.append(
                "Residue holds more metal than the feed: extraction is negative; check the assays."
            )
        if residue_kg > feed_kg:
            warnings.append(
                "Residue mass exceeds feed mass: unusual for a leach; check the masses."
            )
        if m_solution > m_feed:
            warnings.append("Metal in solution exceeds the metal in the feed: inconsistent data.")
        return self._result(
            [
                out("metal_feed", "Metal in feed", m_feed, "kg"),
                out("metal_residue", "Metal in residue", m_res, "kg"),
                out(
                    "extraction_solids", "Extraction (solid basis)", dissolved / m_feed, "fraction"
                ),
                out("metal_dissolved_solids", "Metal dissolved (solid basis)", dissolved, "kg"),
                out("metal_solution", "Metal in solution (solution basis)", m_solution, "kg"),
                out(
                    "reconciliation_gap",
                    "Reconciliation gap (solids - solution)",
                    dissolved - m_solution,
                    "kg",
                ),
            ],
            warnings=warnings,
        )


class LeachKinetics(BaseModel):
    """Empirical first-order leaching curve with a maximum extraction."""

    MODEL_ID = "hydrometallurgy.leach_kinetics_first_order"
    EQUATIONS = (
        "X(t) = X_max * (1 - exp(-k * t))",
        "t_90 = ln(10) / k   (time to reach 90 % of X_max)",
    )
    ASSUMPTIONS = (
        "Empirical single-rate model: it does not represent a mechanism (shrinking core, diffusion, passivation) "
        "and does not describe every ore or set of conditions.",
        "X_max and k are fitted by the user for a given ore, temperature, acidity and particle size; none is supplied.",
        "Valid only inside the time range of the data the parameters were fitted on.",
    )
    _POINTS = 60

    def __init__(
        self,
        maximum_extraction: _Q,
        rate_constant: _Q,
        time: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        x_max = qty(
            "maximum_extraction",
            maximum_extraction,
            unit="fraction",
            allowed=("fraction", "%"),
            fraction=True,
        )
        if x_max.to("fraction").value == 0.0:
            raise InvalidParameterError("maximum_extraction must be strictly positive.")
        self._inputs = {
            "maximum_extraction": x_max,
            "rate_constant": qty("rate_constant", rate_constant, unit="1/h", positive=True),
            "time": qty("time", time, unit="h", positive=True),
        }

    def calculate(self) -> GenericResult:
        x_max = self._inputs["maximum_extraction"].to("fraction").value
        k = self._inputs["rate_constant"].to("1/h").value
        t = self._inputs["time"].to("h").value
        extraction = x_max * (1.0 - math.exp(-k * t))
        xs = tuple(t * j / self._POINTS for j in range(self._POINTS + 1))
        ys = tuple(x_max * (1.0 - math.exp(-k * x)) for x in xs)
        chart = ChartData(
            title="Leaching extraction vs time",
            categories=(),
            values=ys,
            unit="fraction",
            source=f"LeachKinetics {self.MODEL_VERSION}, calculated from the given X_max and k",
            kind="line",
            x=xs,
            x_label="Time (h)",
            y_label="Extraction (fraction)",
        )
        return self._result(
            [
                out("extraction", "Extraction at time t", extraction, "fraction"),
                out("time_90", "Time to reach 90 % of maximum extraction", math.log(10.0) / k, "h"),
            ],
            chart=chart,
        )


class Neutralization(BaseModel):
    """Stoichiometric amount of base needed to neutralize free acidity."""

    MODEL_ID = "hydrometallurgy.neutralization"
    EQUATIONS = (
        "n_H = V * c_H",
        "n_base = n_H / z",
        "m_base = n_base * M / p",
    )
    ASSUMPTIONS = (
        "Stoichiometric only: c_H is the free acidity in mol of H+ per litre; z is the number of OH- delivered per formula unit of base.",
        "No buffering, hydrolysis of dissolved metals, precipitation or gypsum formation is modelled, so the real consumption is usually higher.",
        "Base molar mass, purity and equivalents are supplied by the user.",
    )

    def __init__(
        self,
        solution_volume: _Q,
        free_acidity: _Q,
        base_molar_mass: _Q,
        base_equivalents: _Q,
        base_purity: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        purity = qty(
            "base_purity", base_purity, unit="fraction", allowed=("fraction", "%"), fraction=True
        )
        if purity.to("fraction").value == 0.0:
            raise InvalidParameterError("base_purity must be strictly positive.")
        self._inputs = {
            "solution_volume": qty("solution_volume", solution_volume, unit="m3", positive=True),
            "free_acidity": qty("free_acidity", free_acidity, unit="mol/L", non_negative=True),
            "base_molar_mass": qty("base_molar_mass", base_molar_mass, unit="g/mol", positive=True),
            "base_equivalents": qty(
                "base_equivalents",
                base_equivalents,
                unit="ratio",
                allowed=("ratio",),
                positive=True,
            ),
            "base_purity": purity,
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        n_h = i["solution_volume"].to("m3").value * i["free_acidity"].to("mol/m3").value  # mol
        n_base = n_h / i["base_equivalents"].value
        m_pure_kg = n_base * i["base_molar_mass"].to("g/mol").value / 1000.0
        m_commercial_kg = m_pure_kg / i["base_purity"].to("fraction").value
        warnings = [
            "Stoichiometric minimum only: actual consumption is higher when metals hydrolyse or precipitate."
        ]
        if n_h == 0.0:
            warnings.append("Free acidity is zero: nothing to neutralize.")
        return self._result(
            [
                out("acid_amount", "Free acid (H+) to neutralize", n_h, "mol"),
                out("base_amount", "Base needed (formula units)", n_base, "mol"),
                out("base_mass_pure", "Base mass (pure)", m_pure_kg, "kg"),
                out(
                    "base_mass_commercial",
                    "Base mass (commercial, at given purity)",
                    m_commercial_kg,
                    "kg",
                ),
            ],
            warnings=warnings,
        )


class PrecipitationYield(BaseModel):
    """Precipitation yield from the dissolved concentration before and after."""

    MODEL_ID = "hydrometallurgy.precipitation_yield"
    EQUATIONS = (
        "m_precipitated = (C0 - Cf) * V",
        "yield = (C0 - Cf) / C0",
    )
    ASSUMPTIONS = (
        "The solution volume is unchanged by the precipitation reagent (no dilution); use the final volume otherwise.",
        "The metal removed from solution reports entirely to the solid (no adsorption on other solids, no volatilisation).",
        "No equilibrium or solubility-product model: concentrations are measured values.",
    )

    def __init__(
        self,
        solution_volume: _Q,
        initial_concentration: _Q,
        final_concentration: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "solution_volume": qty("solution_volume", solution_volume, unit="m3", positive=True),
            "initial_concentration": qty(
                "initial_concentration", initial_concentration, unit="g/L", positive=True
            ),
            "final_concentration": qty(
                "final_concentration", final_concentration, unit="g/L", non_negative=True
            ),
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        c0 = i["initial_concentration"].to("kg/m3").value
        cf = i["final_concentration"].to("kg/m3").value
        if cf > c0:
            raise ModelDomainError(
                "Final concentration is higher than the initial one: this is re-dissolution, not precipitation."
            )
        volume = i["solution_volume"].to("m3").value
        return self._result(
            [
                out("precipitated_mass", "Metal precipitated", (c0 - cf) * volume, "kg"),
                out("yield", "Precipitation yield", (c0 - cf) / c0, "fraction"),
                out("residual_mass", "Metal left in solution", cf * volume, "kg"),
            ]
        )
