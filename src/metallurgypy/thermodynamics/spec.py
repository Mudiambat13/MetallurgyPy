"""Registry metadata for the thermodynamics models."""

from metallurgypy.core.units import Quantity
from metallurgypy.registry import param, register_class
from metallurgypy.thermodynamics.models import GibbsReaction, StrongAcidPH, WeakAcidPH

_DOC = "scientific_methods/thermodynamics/"

register_class(
    GibbsReaction,
    module_key="thermodynamics",
    title="Gibbs energy and equilibrium constant",
    description="dG and K at a temperature from dH and dS (constant with temperature).",
    parameters=(
        param("delta_h", "Reaction enthalpy dH", "From your documented source.", "kJ/mol"),
        param("delta_s", "Reaction entropy dS", "From your documented source.", "J/(mol.K)"),
        param("temperature", "Temperature", "Must be close to the data reference temperature.", "degC", ("K", "degC")),
    ),
    example={
        "delta_h": Quantity(-50.0, "kJ/mol"),
        "delta_s": Quantity(-100.0, "J/(mol.K)"),
        "temperature": Quantity(25.0, "degC"),
    },
    doc_page=_DOC,
)
register_class(
    StrongAcidPH,
    module_key="thermodynamics",
    title="Strong acid pH (ideal)",
    description="pH of a fully dissociated acid, ideal-solution approximation.",
    parameters=(
        param("concentration", "Acid concentration", "Formula-unit concentration.", "mol/L"),
        param("protons", "Protons per formula unit", "Fully dissociated protons.", "ratio", ("ratio",)),
    ),
    example={"concentration": Quantity(0.01, "mol/L"), "protons": Quantity(1.0, "ratio")},
    doc_page=_DOC,
)
register_class(
    WeakAcidPH,
    module_key="thermodynamics",
    title="Weak acid pH (ideal)",
    description="pH of a monoprotic weak acid from the charge balance, solved numerically.",
    parameters=(
        param("analytical_concentration", "Total acid concentration", "Analytical concentration.", "mol/L"),
        param("pka", "pKa", "Acid constant at the solution temperature.", "ratio", ("ratio",)),
        param("pkw", "pKw", "Water constant at the solution temperature.", "ratio", ("ratio",)),
    ),
    example={
        "analytical_concentration": Quantity(0.1, "mol/L"),
        "pka": Quantity(4.76, "ratio"),
        "pkw": Quantity(14.0, "ratio"),
    },
    doc_page=_DOC,
)
