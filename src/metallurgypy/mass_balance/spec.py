"""Registry metadata for the mass balance models (controlled, declarative)."""

from __future__ import annotations

from collections.abc import Mapping

from metallurgypy.core.units import GRADE_UNITS, MASS_UNITS, RATIO_UNITS, Quantity
from metallurgypy.mass_balance.models import MassBalance, TwoProductBalance
from metallurgypy.registry import ModelSpec, ParameterSpec, register

_FEED_MASS = ParameterSpec("feed_mass", "Feed mass", "Mass of the feed stream (> 0).", MASS_UNITS, "t")
_FEED_GRADE = ParameterSpec(
    "feed_grade", "Feed grade", "Mass fraction of the metal in the feed.", GRADE_UNITS, "%"
)


def _recovery_balance(v: Mapping[str, Quantity]) -> MassBalance:
    return MassBalance(v["feed_mass"], v["feed_grade"], v["recovery"])


def _two_product(v: Mapping[str, Quantity]) -> TwoProductBalance:
    return TwoProductBalance(
        v["feed_mass"], v["feed_grade"], v["concentrate_grade"], v["tailings_grade"]
    )


register(
    ModelSpec(
        model_id=MassBalance.MODEL_ID,
        module_key="mass_balance",
        title="Metal balance from recovery",
        description="Contained, recovered and remaining metal from a feed mass, its grade and a recovery.",
        model_version=MassBalance.MODEL_VERSION,
        parameters=(
            _FEED_MASS,
            _FEED_GRADE,
            ParameterSpec(
                "recovery",
                "Recovery",
                "Share of the contained metal reporting to the product (not the mass yield).",
                RATIO_UNITS,
                "%",
            ),
        ),
        factory=_recovery_balance,
        example={
            "feed_mass": Quantity(1000.0, "t"),
            "feed_grade": Quantity(2.5, "%"),
            "recovery": Quantity(92.0, "%"),
        },
        doc_page="scientific_methods/mass_balance/",
    )
)

register(
    ModelSpec(
        model_id=TwoProductBalance.MODEL_ID,
        module_key="mass_balance",
        title="Two-product balance from grades",
        description="Concentrate and tailings masses, mass yield and recovery from the three grades.",
        model_version=TwoProductBalance.MODEL_VERSION,
        parameters=(
            _FEED_MASS,
            _FEED_GRADE,
            ParameterSpec(
                "concentrate_grade", "Concentrate grade", "Mass fraction of the metal in the concentrate.", GRADE_UNITS, "%"
            ),
            ParameterSpec(
                "tailings_grade", "Tailings grade", "Mass fraction of the metal in the tailings.", GRADE_UNITS, "%"
            ),
        ),
        factory=_two_product,
        example={
            "feed_mass": Quantity(1000.0, "t"),
            "feed_grade": Quantity(2.0, "%"),
            "concentrate_grade": Quantity(20.0, "%"),
            "tailings_grade": Quantity(0.4, "%"),
        },
        doc_page="scientific_methods/mass_balance/",
    )
)
