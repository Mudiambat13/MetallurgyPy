"""Electrowinning from Faraday's law. Equations: docs/scientific_methods/electrowinning.md."""

from __future__ import annotations

from metallurgypy.core.constants import FARADAY
from metallurgypy.core.exceptions import InvalidParameterError
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.results import ChartData, GenericResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

_Q = Quantity | float


class Electrowinning(BaseModel):
    """Theoretical and actual deposit, current density and energy of one electrolysis period."""

    MODEL_ID = "electrowinning.faraday"
    EQUATIONS = (
        "m_theoretical = I * t * M / (n * F)",
        "m_actual = eta * m_theoretical",
        "j = I / A",
        "E = U * I * t",
        "e = E / m_actual",
    )
    ASSUMPTIONS = (
        "One electrode reaction with a fixed number of electrons n per deposited species; side reactions enter only through the current efficiency eta.",
        "Current, current efficiency and cell voltage are constant over the period; the cell voltage is an input, not predicted.",
        "Theoretical and actual production are reported separately: the actual one is only as good as the efficiency supplied.",
        "Deposit quality, short circuits and process upsets are not modelled.",
        "Faraday constant F = N_A * e, exact in the 2019 SI definition.",
    )

    def __init__(
        self,
        current: _Q,
        duration: _Q,
        molar_mass: _Q,
        electrons: _Q,
        current_efficiency: _Q,
        cell_voltage: _Q,
        cathode_area: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        efficiency = qty(
            "current_efficiency", current_efficiency, unit="fraction", allowed=("fraction", "%"), fraction=True
        )
        if efficiency.to("fraction").value == 0.0:
            raise InvalidParameterError("current_efficiency must be strictly positive.")
        self._inputs = {
            "current": qty("current", current, unit="A", positive=True),
            "duration": qty("duration", duration, unit="h", positive=True),
            "molar_mass": qty("molar_mass", molar_mass, unit="g/mol", positive=True),
            "electrons": qty("electrons", electrons, unit="ratio", allowed=("ratio",), positive=True),
            "current_efficiency": efficiency,
            "cell_voltage": qty("cell_voltage", cell_voltage, unit="V", positive=True),
            "cathode_area": qty("cathode_area", cathode_area, unit="m2", positive=True),
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        current = i["current"].to("A").value
        seconds = i["duration"].to("s").value
        molar_mass_kg = i["molar_mass"].to("g/mol").value / 1000.0
        n = i["electrons"].value
        eta = i["current_efficiency"].to("fraction").value
        voltage = i["cell_voltage"].value
        area = i["cathode_area"].to("m2").value

        m_theo = current * seconds * molar_mass_kg / (n * FARADAY)
        m_actual = eta * m_theo
        energy_j = voltage * current * seconds
        energy_kwh = energy_j / 3_600_000.0
        specific = energy_kwh / (m_actual / 1000.0)  # kWh per tonne deposited
        warnings = []
        if n != int(n):
            warnings.append(f"Electrons per species is not an integer ({n!r}): check the half-reaction.")
        if eta == 1.0:
            warnings.append("Current efficiency is exactly 100 %: actual equals theoretical production.")
        chart = ChartData(
            title="Deposited mass",
            categories=("Theoretical", "Actual", "Lost to side reactions"),
            values=(m_theo, m_actual, m_theo - m_actual),
            unit="kg",
            source=f"Electrowinning {self.MODEL_VERSION}, calculated",
        )
        return self._result(
            [
                out("theoretical_mass", "Theoretical deposited mass", m_theo, "kg"),
                out("actual_mass", "Actual deposited mass (at given efficiency)", m_actual, "kg"),
                out("production_rate", "Actual production rate", m_actual / (seconds / 3600.0), "kg/h"),
                out("current_density", "Current density", current / area, "A/m2"),
                out("energy", "Electrical energy", energy_kwh, "kWh"),
                out("specific_energy", "Specific energy (per tonne deposited)", specific, "kWh/t"),
            ],
            warnings=warnings,
            chart=chart,
        )
