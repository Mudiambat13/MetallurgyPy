"""Registry metadata for the electrowinning model."""

from metallurgypy.core.units import Quantity
from metallurgypy.electrowinning.models import Electrowinning
from metallurgypy.registry import param, register_class

register_class(
    Electrowinning,
    module_key="electrowinning",
    title="Electrowinning (Faraday)",
    description="Theoretical and actual deposit, current density and energy for one period.",
    parameters=(
        param("current", "Total current", "Current through the cells.", "A"),
        param("duration", "Duration", "Electrolysis time.", "h"),
        param("molar_mass", "Molar mass of the deposit", "Molar mass of the deposited species.", "g/mol"),
        param("electrons", "Electrons per species (n)", "Electrons exchanged per deposited species.", "ratio", ("ratio",)),
        param("current_efficiency", "Current efficiency", "Share of the current that deposits metal.", "%", ("fraction", "%")),
        param("cell_voltage", "Cell voltage", "Voltage across the cell.", "V"),
        param("cathode_area", "Active cathode area", "Total active cathode area.", "m2"),
    ),
    example={
        "current": Quantity(10000.0, "A"),
        "duration": Quantity(24.0, "h"),
        "molar_mass": Quantity(63.5, "g/mol"),
        "electrons": Quantity(2.0, "ratio"),
        "current_efficiency": Quantity(90.0, "%"),
        "cell_voltage": Quantity(2.0, "V"),
        "cathode_area": Quantity(40.0, "m2"),
    },
    doc_page="scientific_methods/electrowinning/",
)
