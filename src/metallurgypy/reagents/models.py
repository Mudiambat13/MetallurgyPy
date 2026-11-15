"""Reagent preparation and consumption. Equations: docs/scientific_methods/reagents.md.

No reagent property or dosage is built in: every value is supplied by the user.
"""

from __future__ import annotations

from metallurgypy.core.exceptions import InvalidParameterError, ModelDomainError
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.results import GenericResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

_Q = Quantity | float


class Dilution(BaseModel):
    """Dilute a stock solution to a target mass concentration (conserving the solute)."""

    MODEL_ID = "reagents.dilution"
    EQUATIONS = (
        "c1 * V1 = c2 * V2",
        "V1 = V2 * c2 / c1",
        "V_diluent = V2 - V1",
        "m_solute = c2 * V2",
    )
    ASSUMPTIONS = (
        "Volumes are additive (V_diluent = V2 - V1). Real solutions can show volume contraction "
        "or expansion on mixing, so for strong acids or concentrated solutions prepare to the final mark.",
        "Concentrations are mass concentrations (solute mass per solution volume) at the same temperature.",
        "Stock concentration and purity come from the user (label or assay).",
    )

    def __init__(
        self,
        stock_concentration: _Q,
        target_concentration: _Q,
        final_volume: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "stock_concentration": qty("stock_concentration", stock_concentration, unit="g/L", positive=True),
            "target_concentration": qty("target_concentration", target_concentration, unit="g/L", positive=True),
            "final_volume": qty("final_volume", final_volume, unit="L", positive=True),
        }

    def calculate(self) -> GenericResult:
        stock = self._inputs["stock_concentration"]
        target = self._inputs["target_concentration"]
        volume = self._inputs["final_volume"]
        c1 = stock.to("kg/m3").value
        c2 = target.to("kg/m3").value
        if c2 > c1:
            raise ModelDomainError(
                f"Target concentration ({target}) is higher than the stock concentration ({stock}): "
                "a solution cannot be diluted to a higher concentration."
            )
        v2 = volume.value
        v1 = v2 * c2 / c1
        diluent = v2 - v1
        solute_kg = c2 * volume.to("m3").value
        warnings = []
        if c2 == c1:
            warnings.append("Target equals stock concentration: no dilution is needed.")
        return self._result(
            [
                out("stock_volume", "Stock volume to take", v1, volume.unit),
                out("diluent_volume", "Diluent volume to add", diluent, volume.unit),
                out("dilution_factor", "Dilution factor (c1 / c2)", c1 / c2, "ratio"),
                out("solute_mass", "Solute mass in final solution", solute_kg, "kg"),
            ],
            warnings=warnings,
        )


class ConcentrationConversion(BaseModel):
    """Convert a mass concentration to a molar concentration."""

    MODEL_ID = "reagents.concentration_conversion"
    EQUATIONS = ("c_molar = rho / M",)
    ASSUMPTIONS = (
        "The molar mass is the one of the species the concentration refers to (user input).",
        "No speciation or ionic strength effect is considered.",
    )

    def __init__(
        self,
        mass_concentration: _Q,
        molar_mass: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "mass_concentration": qty("mass_concentration", mass_concentration, unit="g/L", non_negative=True),
            "molar_mass": qty("molar_mass", molar_mass, unit="g/mol", positive=True),
        }

    def calculate(self) -> GenericResult:
        rho = self._inputs["mass_concentration"].to("g/L").value
        molar_mass = self._inputs["molar_mass"].to("g/mol").value
        return self._result(
            [out("molar_concentration", "Molar concentration", rho / molar_mass, "mol/L")]
        )


class ReagentConsumption(BaseModel):
    """Reagent consumption per hour, per operating day and per campaign."""

    MODEL_ID = "reagents.consumption"
    EQUATIONS = (
        "m_active/h = d * Q_ore",
        "m_product/h = d * Q_ore / p",
        "m_product/day = m_product/h * h_day",
        "m_product/campaign = m_product/day * N_days",
    )
    ASSUMPTIONS = (
        "The dosage d is the mass of ACTIVE reagent per mass of ore; the commercial product mass divides by its purity p.",
        "Ore throughput is constant over the period; no start-up, stoppage or dosing losses are modelled.",
        "Dosage, purity and throughput are inputs; MetallurgyPy suggests no dosage.",
    )

    def __init__(
        self,
        ore_throughput: _Q,
        dosage: _Q,
        purity: _Q,
        operating_hours_per_day: _Q,
        campaign_duration: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        hours = qty("operating_hours_per_day", operating_hours_per_day, unit="h", positive=True)
        if hours.to("h").value > 24.0:
            raise InvalidParameterError(
                f"operating_hours_per_day = {hours} exceeds 24 h in a day."
            )
        self._inputs = {
            "ore_throughput": qty("ore_throughput", ore_throughput, unit="t/h", positive=True),
            "dosage": qty("dosage", dosage, unit="kg/t", allowed=("kg/t", "g/t", "%"), non_negative=True),
            "purity": qty("purity", purity, unit="fraction", allowed=("fraction", "%"), fraction=True),
            "operating_hours_per_day": hours,
            "campaign_duration": qty("campaign_duration", campaign_duration, unit="d", positive=True),
        }
        if self._inputs["purity"].to("fraction").value == 0.0:
            raise InvalidParameterError("purity must be strictly positive.")

    def calculate(self) -> GenericResult:
        i = self._inputs
        flow_kg_h = i["ore_throughput"].to("t/h").value * 1000.0
        dosage = i["dosage"].to("fraction").value
        purity = i["purity"].to("fraction").value
        hours = i["operating_hours_per_day"].to("h").value
        days = i["campaign_duration"].to("d").value

        active_h = dosage * flow_kg_h
        product_h = active_h / purity
        product_day = product_h * hours
        product_campaign = product_day * days
        ore_campaign_t = flow_kg_h * hours * days / 1000.0
        return self._result(
            [
                out("active_per_hour", "Active reagent per hour", active_h, "kg/h"),
                out("product_per_hour", "Commercial product per hour", product_h, "kg/h"),
                out("product_per_day", "Commercial product per operating day", product_day, "kg"),
                out("product_per_campaign", "Commercial product per campaign", product_campaign / 1000.0, "t"),
                out("ore_per_campaign", "Ore processed per campaign", ore_campaign_t, "t"),
                out("specific_consumption", "Commercial product per tonne of ore", dosage / purity * 1000.0, "kg/t"),
            ]
        )
