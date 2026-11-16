"""Registry metadata for the reagent models."""

from metallurgypy.core.units import Quantity
from metallurgypy.reagents.models import ConcentrationConversion, Dilution, ReagentConsumption
from metallurgypy.registry import param, register_class

_DOC = "scientific_methods/reagents/"

register_class(
    Dilution,
    module_key="reagents",
    title="Solution dilution",
    description="Stock and diluent volumes to prepare a solution of a given mass concentration.",
    parameters=(
        param(
            "stock_concentration",
            "Stock concentration",
            "Mass concentration of the stock solution.",
            "g/L",
        ),
        param(
            "target_concentration",
            "Target concentration",
            "Mass concentration wanted (not above the stock).",
            "g/L",
        ),
        param("final_volume", "Final volume", "Volume of solution to prepare.", "L"),
    ),
    example={
        "stock_concentration": Quantity(100.0, "g/L"),
        "target_concentration": Quantity(10.0, "g/L"),
        "final_volume": Quantity(50.0, "L"),
    },
    doc_page=_DOC,
)
register_class(
    ConcentrationConversion,
    module_key="reagents",
    title="Mass to molar concentration",
    description="Molar concentration from a mass concentration and the molar mass of the species.",
    parameters=(
        param(
            "mass_concentration",
            "Mass concentration",
            "Mass of species per volume of solution.",
            "g/L",
        ),
        param("molar_mass", "Molar mass", "Molar mass of that species.", "g/mol"),
    ),
    example={"mass_concentration": Quantity(40.0, "g/L"), "molar_mass": Quantity(40.0, "g/mol")},
    doc_page=_DOC,
)
register_class(
    ReagentConsumption,
    module_key="reagents",
    title="Reagent consumption",
    description="Hourly, daily and campaign consumption from a dosage per tonne of ore.",
    parameters=(
        param("ore_throughput", "Ore throughput", "Ore treated per unit time.", "t/h"),
        param(
            "dosage",
            "Dosage (active reagent)",
            "Active reagent mass per mass of ore.",
            "kg/t",
            ("kg/t", "g/t", "%"),
        ),
        param(
            "purity",
            "Purity of the product",
            "Active share of the commercial product.",
            "%",
            ("fraction", "%"),
        ),
        param(
            "operating_hours_per_day",
            "Operating hours per day",
            "Hours of operation per day (at most 24).",
            "h",
        ),
        param("campaign_duration", "Campaign duration", "Length of the campaign.", "d"),
    ),
    example={
        "ore_throughput": Quantity(100.0, "t/h"),
        "dosage": Quantity(2.0, "kg/t"),
        "purity": Quantity(95.0, "%"),
        "operating_hours_per_day": Quantity(20.0, "h"),
        "campaign_duration": Quantity(30.0, "d"),
    },
    doc_page=_DOC,
)
