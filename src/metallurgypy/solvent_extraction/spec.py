"""Registry metadata for the solvent extraction models."""

from metallurgypy.core.units import Quantity
from metallurgypy.registry import param, register_class
from metallurgypy.solvent_extraction.models import (
    CountercurrentExtraction,
    SingleStageExtraction,
    StagesRequired,
    StrippingStage,
)

_DOC = "scientific_methods/solvent_extraction/"
_D = ("ratio",)

register_class(
    SingleStageExtraction,
    module_key="solvent_extraction",
    title="Single-stage extraction",
    description="One equilibrium stage with a constant distribution coefficient.",
    parameters=(
        param(
            "feed_concentration",
            "Aqueous feed concentration",
            "Metal concentration in the aqueous feed.",
            "g/L",
        ),
        param(
            "distribution_coefficient",
            "Distribution coefficient D",
            "C_org / C_aq at equilibrium (your system).",
            "ratio",
            _D,
        ),
        param("oa_ratio", "O/A ratio", "Organic to aqueous volume ratio.", "ratio", _D),
    ),
    example={
        "feed_concentration": Quantity(5.0, "g/L"),
        "distribution_coefficient": Quantity(4.0, "ratio"),
        "oa_ratio": Quantity(1.0, "ratio"),
    },
    doc_page=_DOC,
)
register_class(
    StrippingStage,
    module_key="solvent_extraction",
    title="Single-stage stripping",
    description="One equilibrium stripping stage with a constant distribution coefficient.",
    parameters=(
        param(
            "loaded_organic_concentration",
            "Loaded organic concentration",
            "Metal in the loaded organic.",
            "g/L",
        ),
        param(
            "strip_distribution_coefficient",
            "Strip distribution coefficient",
            "C_org / C_aq under stripping conditions.",
            "ratio",
            _D,
        ),
        param("ao_ratio", "A/O ratio", "Aqueous (strip) to organic volume ratio.", "ratio", _D),
        param(
            "strip_aqueous_inlet_concentration",
            "Strip liquor inlet concentration",
            "Metal already in the strip liquor.",
            "g/L",
        ),
    ),
    example={
        "loaded_organic_concentration": Quantity(4.0, "g/L"),
        "strip_distribution_coefficient": Quantity(0.05, "ratio"),
        "ao_ratio": Quantity(0.25, "ratio"),
        "strip_aqueous_inlet_concentration": Quantity(30.0, "g/L"),
    },
    doc_page=_DOC,
)
register_class(
    CountercurrentExtraction,
    module_key="solvent_extraction",
    title="Counter-current extraction (Kremser)",
    description="Extraction over N theoretical counter-current stages, constant D.",
    parameters=(
        param(
            "feed_concentration", "Aqueous feed concentration", "Metal in the aqueous feed.", "g/L"
        ),
        param(
            "distribution_coefficient",
            "Distribution coefficient D",
            "C_org / C_aq (your system).",
            "ratio",
            _D,
        ),
        param("oa_ratio", "O/A ratio", "Organic to aqueous volume ratio.", "ratio", _D),
        param("stages", "Theoretical stages N", "Whole number of stages.", "ratio", _D),
    ),
    example={
        "feed_concentration": Quantity(5.0, "g/L"),
        "distribution_coefficient": Quantity(2.0, "ratio"),
        "oa_ratio": Quantity(1.0, "ratio"),
        "stages": Quantity(3.0, "ratio"),
    },
    doc_page=_DOC,
)
register_class(
    StagesRequired,
    module_key="solvent_extraction",
    title="Stages required",
    description="Theoretical counter-current stages for a target extraction, constant D.",
    parameters=(
        param(
            "distribution_coefficient",
            "Distribution coefficient D",
            "C_org / C_aq (your system).",
            "ratio",
            _D,
        ),
        param("oa_ratio", "O/A ratio", "Organic to aqueous volume ratio.", "ratio", _D),
        param(
            "target_extraction",
            "Target extraction",
            "Fraction of metal to extract (0 to 100 %, excluded).",
            "%",
            ("fraction", "%"),
        ),
    ),
    example={
        "distribution_coefficient": Quantity(2.0, "ratio"),
        "oa_ratio": Quantity(1.0, "ratio"),
        "target_extraction": Quantity(99.0, "%"),
    },
    doc_page=_DOC,
)
