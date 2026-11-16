"""Thermodynamics. Equations: docs/scientific_methods/thermodynamics.md.

No thermodynamic dataset is bundled: enthalpies, entropies and acidity
constants are user inputs, and the model documents the temperature at which
they must be valid.
"""

from __future__ import annotations

import math

from metallurgypy.core.constants import GAS_CONSTANT
from metallurgypy.core.exceptions import InvalidParameterError, ModelDomainError
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.numerics import bisect
from metallurgypy.core.results import GenericResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances, require_real

_Q = Quantity | float
_LN_MAX = 700.0  # exp(700) ~ 1e304, close to the float64 limit


class GibbsReaction(BaseModel):
    """Gibbs energy change and equilibrium constant of a reaction at one temperature."""

    MODEL_ID = "thermodynamics.gibbs_equilibrium"
    EQUATIONS = (
        "dG = dH - T * dS",
        "ln K = -dG / (R * T)",
        "log10 K = ln K / ln 10",
    )
    ASSUMPTIONS = (
        "dH and dS are constant between their reference temperature and T (heat capacity change neglected): "
        "valid near the temperature where they were determined, increasingly wrong far from it.",
        "K is the thermodynamic equilibrium constant (activities, standard states of the data source); "
        "it is not a concentration quotient.",
        "dH, dS and their reference temperature come from the user's documented source.",
        "R = N_A * k_B, exact in the 2019 SI definition.",
    )

    def __init__(
        self,
        delta_h: _Q,
        delta_s: _Q,
        temperature: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        temp = qty("temperature", temperature, unit="K", allowed=("K", "degC"))
        if temp.to("K").value <= 0.0:
            raise InvalidParameterError(f"temperature = {temp} is at or below absolute zero.")
        self._inputs = {
            "delta_h": qty("delta_h", delta_h, unit="kJ/mol"),
            "delta_s": qty("delta_s", delta_s, unit="J/(mol.K)"),
            "temperature": temp,
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        t = i["temperature"].to("K").value
        dh = i["delta_h"].to("J/mol").value
        ds = i["delta_s"].to("J/(mol.K)").value
        dg = dh - t * ds
        ln_k = -dg / (GAS_CONSTANT * t)
        items = [
            out("delta_g", "Gibbs energy change", dg / 1000.0, "kJ/mol"),
            out("ln_k", "ln K", ln_k, "ratio"),
            out("log10_k", "log10 K", ln_k / math.log(10.0), "ratio"),
        ]
        warnings = []
        if abs(ln_k) <= _LN_MAX:
            items.append(out("k", "Equilibrium constant K", math.exp(ln_k), "ratio"))
        else:
            warnings.append("K is outside the float64 range: use ln K or log10 K.")
        return self._result(items, warnings=warnings)


class StrongAcidPH(BaseModel):
    """pH of a fully dissociated acid, ideal-solution approximation."""

    MODEL_ID = "thermodynamics.strong_acid_ph"
    EQUATIONS = ("[H+] = z * c", "pH = -log10([H+])")
    ASSUMPTIONS = (
        "Complete dissociation of z protons per formula unit (z supplied by the user).",
        "Activity equals concentration: valid only in dilute solution. Concentrated acids and process liquors "
        "have activity coefficients far from 1, and the measured pH can differ by more than one unit.",
        "Autoionization of water is neglected, so the model is refused below 1e-6 mol/L of H+.",
    )

    def __init__(
        self,
        concentration: _Q,
        protons: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "concentration": qty("concentration", concentration, unit="mol/L", positive=True),
            "protons": qty("protons", protons, unit="ratio", allowed=("ratio",), positive=True),
        }

    def calculate(self) -> GenericResult:
        h = self._inputs["concentration"].to("mol/L").value * self._inputs["protons"].value
        if h < 1e-6:
            raise ModelDomainError(
                f"[H+] = {h:.3g} mol/L is too dilute for the strong-acid model (water autoionization matters)."
            )
        warnings = []
        if h > 0.1:
            warnings.append(
                "[H+] above 0.1 mol/L: activity coefficients are no longer close to 1; the pH is indicative only."
            )
        return self._result(
            [
                out("hydrogen_concentration", "[H+]", h, "mol/L"),
                out("ph", "pH (ideal)", -math.log10(h), "ratio"),
            ],
            warnings=warnings,
        )


class WeakAcidPH(BaseModel):
    """pH of a monoprotic weak acid from the charge balance (water autoionization included)."""

    MODEL_ID = "thermodynamics.weak_acid_ph"
    EQUATIONS = (
        "[A-] = C * Ka / (Ka + [H+])",
        "[OH-] = Kw / [H+]",
        "charge balance:  [H+] - [A-] - [OH-] = 0   (solved by bisection)",
        "alpha = Ka / (Ka + [H+])",
    )
    ASSUMPTIONS = (
        "Single monoprotic acid, no other acid, base or complexing species in solution.",
        "Activity equals concentration (ideal solution); Ka and Kw apply at the solution temperature.",
        "pKa and pKw come from the user's documented source; pKw depends on temperature.",
        "Solved on [H+] with bisection; the bracket and convergence are recorded in the result.",
    )

    def __init__(
        self,
        analytical_concentration: _Q,
        pka: _Q,
        pkw: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "analytical_concentration": qty(
                "analytical_concentration", analytical_concentration, unit="mol/L", positive=True
            ),
            "pka": qty("pka", pka, unit="ratio", allowed=("ratio",)),
            "pkw": qty("pkw", pkw, unit="ratio", allowed=("ratio",), positive=True),
        }
        require_real("pka", self._inputs["pka"].value)

    def calculate(self) -> GenericResult:
        c = self._inputs["analytical_concentration"].to("mol/L").value
        ka = float(10.0 ** (-self._inputs["pka"].value))
        kw = 10.0 ** (-self._inputs["pkw"].value)

        def charge_balance(h: float) -> float:
            return float(h - c * ka / (ka + h) - kw / h)

        root = bisect(charge_balance, 1e-30, c + 1.0, rel_tol=1e-14)
        h = root.root
        return self._result(
            [
                out("hydrogen_concentration", "[H+]", h, "mol/L"),
                out("ph", "pH (ideal)", -math.log10(h), "ratio"),
                out(
                    "dissociation_fraction",
                    "Degree of dissociation alpha",
                    ka / (ka + h),
                    "fraction",
                ),
            ],
            convergence=root.status(),
            method="Bisection on [H+] in [1e-30, C + 1] mol/L",
        )
