"""Registry metadata for the hydrometallurgy models."""

from metallurgypy.core.units import GRADE_UNITS, Quantity
from metallurgypy.hydrometallurgy.models import (
    LeachingYield,
    LeachKinetics,
    Neutralization,
    PrecipitationYield,
)
from metallurgypy.registry import param, register_class

_DOC = "scientific_methods/hydrometallurgy/"

register_class(
    LeachingYield,
    module_key="hydrometallurgy",
    title="Leaching extraction yield",
    description="Extraction from solid assays, cross-checked with the solution assay.",
    parameters=(
        param("feed_mass", "Feed mass", "Dry mass of solids fed.", "t"),
        param("feed_grade", "Feed grade", "Metal mass fraction in the feed.", "%", GRADE_UNITS),
        param("residue_mass", "Residue mass", "Dry mass of leach residue.", "t"),
        param("residue_grade", "Residue grade", "Metal mass fraction in the residue.", "%", GRADE_UNITS),
        param("solution_volume", "Pregnant solution volume", "Volume of leach solution.", "m3"),
        param("solution_concentration", "Solution concentration", "Metal concentration in the solution.", "g/L"),
    ),
    example={
        "feed_mass": Quantity(100.0, "t"),
        "feed_grade": Quantity(2.0, "%"),
        "residue_mass": Quantity(92.0, "t"),
        "residue_grade": Quantity(0.5, "%"),
        "solution_volume": Quantity(300.0, "m3"),
        "solution_concentration": Quantity(5.0, "g/L"),
    },
    doc_page=_DOC,
)
register_class(
    LeachKinetics,
    module_key="hydrometallurgy",
    title="First-order leach kinetics",
    description="Empirical extraction versus time from a maximum extraction and a rate constant.",
    parameters=(
        param("maximum_extraction", "Maximum extraction", "Plateau extraction for long times.", "%", ("fraction", "%")),
        param("rate_constant", "Rate constant k", "First-order rate constant.", "1/h"),
        param("time", "Leaching time", "Time at which the extraction is wanted.", "h"),
    ),
    example={
        "maximum_extraction": Quantity(95.0, "%"),
        "rate_constant": Quantity(0.3, "1/h"),
        "time": Quantity(12.0, "h"),
    },
    doc_page=_DOC,
)
register_class(
    Neutralization,
    module_key="hydrometallurgy",
    title="Neutralization (stoichiometric)",
    description="Stoichiometric base needed to neutralize free acidity.",
    parameters=(
        param("solution_volume", "Solution volume", "Volume to neutralize.", "m3"),
        param("free_acidity", "Free acidity", "Mol of H+ per litre.", "mol/L"),
        param("base_molar_mass", "Base molar mass", "Molar mass of the base formula unit.", "g/mol"),
        param("base_equivalents", "OH- per formula unit", "Hydroxide delivered per formula unit.", "ratio", ("ratio",)),
        param("base_purity", "Base purity", "Active share of the commercial base.", "%", ("fraction", "%")),
    ),
    example={
        "solution_volume": Quantity(100.0, "m3"),
        "free_acidity": Quantity(0.1, "mol/L"),
        "base_molar_mass": Quantity(56.0, "g/mol"),
        "base_equivalents": Quantity(2.0, "ratio"),
        "base_purity": Quantity(90.0, "%"),
    },
    doc_page=_DOC,
)
register_class(
    PrecipitationYield,
    module_key="hydrometallurgy",
    title="Precipitation yield",
    description="Metal precipitated and yield from concentrations before and after.",
    parameters=(
        param("solution_volume", "Solution volume", "Volume treated (assumed unchanged).", "m3"),
        param("initial_concentration", "Initial concentration", "Dissolved metal before precipitation.", "g/L"),
        param("final_concentration", "Final concentration", "Dissolved metal after precipitation.", "g/L"),
    ),
    example={
        "solution_volume": Quantity(50.0, "m3"),
        "initial_concentration": Quantity(4.0, "g/L"),
        "final_concentration": Quantity(0.2, "g/L"),
    },
    doc_page=_DOC,
)
