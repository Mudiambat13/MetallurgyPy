"""Registry metadata for the flotation models."""

from metallurgypy.core.units import GRADE_UNITS, Quantity
from metallurgypy.flotation.models import FlotationBalance, FlotationKinetics
from metallurgypy.registry import param, register_class

_DOC = "scientific_methods/flotation/"

register_class(
    FlotationBalance,
    module_key="flotation",
    title="Concentrate / tailings balance",
    description="Mass pull, metal recovery and enrichment from feed, concentrate and tailings grades.",
    parameters=(
        param("feed_mass", "Feed mass", "Mass of the feed (> 0).", "t"),
        param(
            "feed_grade", "Feed grade", "Mass fraction of the metal in the feed.", "%", GRADE_UNITS
        ),
        param(
            "concentrate_grade",
            "Concentrate grade",
            "Mass fraction of the metal in the concentrate.",
            "%",
            GRADE_UNITS,
        ),
        param(
            "tailings_grade",
            "Tailings grade",
            "Mass fraction of the metal in the tailings.",
            "%",
            GRADE_UNITS,
        ),
    ),
    example={
        "feed_mass": Quantity(1000.0, "t"),
        "feed_grade": Quantity(1.5, "%"),
        "concentrate_grade": Quantity(25.0, "%"),
        "tailings_grade": Quantity(0.2, "%"),
    },
    doc_page=_DOC,
)
register_class(
    FlotationKinetics,
    module_key="flotation",
    title="First-order kinetics",
    description="Recovery versus time from an ultimate recovery and a rate constant.",
    parameters=(
        param(
            "ultimate_recovery",
            "Ultimate recovery",
            "Plateau recovery reached for long times.",
            "%",
            ("fraction", "%"),
        ),
        param("rate_constant", "Rate constant k", "First-order flotation rate constant.", "1/min"),
        param("time", "Flotation time", "Time at which the recovery is wanted.", "min"),
    ),
    example={
        "ultimate_recovery": Quantity(90.0, "%"),
        "rate_constant": Quantity(0.5, "1/min"),
        "time": Quantity(8.0, "min"),
    },
    doc_page=_DOC,
)
