"""Filtration. Equations: docs/scientific_methods/filtration.md."""

from __future__ import annotations

from metallurgypy.core.exceptions import ModelDomainError
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.results import ChartData, GenericResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

_Q = Quantity | float


class ConstantPressureFiltration(BaseModel):
    """Time and rate to collect a filtrate volume through an incompressible cake at constant pressure."""

    MODEL_ID = "filtration.constant_pressure_cake"
    EQUATIONS = (
        "dt/dV = K * V + B",
        "K = mu * alpha * c / (A^2 * dP)",
        "B = mu * R_m / (A * dP)",
        "t(V) = K * V^2 / 2 + B * V",
        "rate(V) = 1 / (K * V + B)",
        "m_cake,dry = c * V",
    )
    ASSUMPTIONS = (
        "Constant pressure drop, incompressible cake (alpha constant), constant medium resistance R_m.",
        "c is the dry-solids mass deposited per unit volume of filtrate (not the slurry solids concentration).",
        "Darcy flow through the cake and medium, no settling during filtration, no cake washing or deliquoring.",
        "alpha and R_m are measured for the slurry and filter used (user inputs).",
    )
    _POINTS = 60

    def __init__(
        self,
        viscosity: _Q,
        cake_resistance: _Q,
        solids_per_filtrate: _Q,
        medium_resistance: _Q,
        area: _Q,
        pressure_drop: _Q,
        filtrate_volume: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "viscosity": qty("viscosity", viscosity, unit="mPa.s", positive=True),
            "cake_resistance": qty("cake_resistance", cake_resistance, unit="m/kg", positive=True),
            "solids_per_filtrate": qty("solids_per_filtrate", solids_per_filtrate, unit="kg/m3", positive=True),
            "medium_resistance": qty("medium_resistance", medium_resistance, unit="1/m", non_negative=True),
            "area": qty("area", area, unit="m2", positive=True),
            "pressure_drop": qty("pressure_drop", pressure_drop, unit="kPa", positive=True),
            "filtrate_volume": qty("filtrate_volume", filtrate_volume, unit="m3", positive=True),
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        mu = i["viscosity"].to("Pa.s").value
        alpha = i["cake_resistance"].value
        c = i["solids_per_filtrate"].to("kg/m3").value
        r_m = i["medium_resistance"].to("1/m").value
        area = i["area"].to("m2").value
        dp = i["pressure_drop"].to("Pa").value
        v = i["filtrate_volume"].to("m3").value

        k = mu * alpha * c / (area**2 * dp)
        b = mu * r_m / (area * dp)
        t_s = k * v * v / 2.0 + b * v
        final_rate_m3_s = 1.0 / (k * v + b)
        average_rate_m3_h = v / t_s * 3600.0
        xs = tuple(v * j / self._POINTS for j in range(self._POINTS + 1))
        ys = tuple((k * x * x / 2.0 + b * x) / 60.0 for x in xs)
        chart = ChartData(
            title="Filtration time vs filtrate volume",
            categories=(),
            values=ys,
            unit="min",
            source=f"ConstantPressureFiltration {self.MODEL_VERSION}, calculated",
            kind="line",
            x=xs,
            x_label="Filtrate volume (m3)",
            y_label="Time (min)",
        )
        return self._result(
            [
                out("filtration_time", "Filtration time", t_s / 60.0, "min"),
                out("average_rate", "Average filtrate rate", average_rate_m3_h, "m3/h"),
                out("final_rate", "Filtrate rate at the end", final_rate_m3_s * 3600.0, "m3/h"),
                out("dry_cake_mass", "Dry cake mass", c * v, "kg"),
            ],
            chart=chart,
        )


class CakeMoisture(BaseModel):
    """Moisture of a filter cake from its wet and dry masses."""

    MODEL_ID = "filtration.cake_moisture"
    EQUATIONS = (
        "m_water = m_wet - m_dry",
        "moisture (wet basis) = m_water / m_wet",
        "moisture (dry basis) = m_water / m_dry",
    )
    ASSUMPTIONS = (
        "Wet mass is weighed before drying and dry mass after drying to constant mass (user measurements).",
        "All mass lost on drying is counted as water; soluble salts and volatile species are not separated.",
        "Moisture is reported on both bases: they differ and must not be mixed up.",
    )

    def __init__(
        self,
        wet_cake_mass: _Q,
        dry_cake_mass: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "wet_cake_mass": qty("wet_cake_mass", wet_cake_mass, unit="kg", positive=True),
            "dry_cake_mass": qty("dry_cake_mass", dry_cake_mass, unit="kg", positive=True),
        }

    def calculate(self) -> GenericResult:
        wet = self._inputs["wet_cake_mass"]
        dry = self._inputs["dry_cake_mass"].to(wet.unit)
        if dry.value > wet.value:
            raise ModelDomainError(
                f"Dry mass ({dry}) exceeds wet mass ({wet}): the cake cannot gain mass on drying."
            )
        water = wet.value - dry.value
        warnings = ["Dry mass equals wet mass: the cake has zero moisture."] if water == 0.0 else []
        return self._result(
            [
                out("water_mass", "Water mass", water, wet.unit),
                out("moisture_wet_basis", "Moisture, wet basis", water / wet.value, "fraction"),
                out("moisture_dry_basis", "Moisture, dry basis", water / dry.value, "fraction"),
            ],
            warnings=warnings,
        )
