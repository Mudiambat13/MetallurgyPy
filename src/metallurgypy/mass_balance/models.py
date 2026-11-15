"""Mass balance models. Equations and assumptions: docs/scientific_methods/mass_balance.md.

Conventions (identical for every model in this module)
------------------------------------------------------
* Bare numbers are interpreted in documented default units: masses in tonnes
  (``t``), grades and recoveries as fractions between 0 and 1. Pass a
  :class:`~metallurgypy.core.units.Quantity` to use another unit.
* A grade is the mass fraction of the metal in the stream, on the same (dry or
  wet) basis as the stream mass. The user is responsible for that consistency.
* Recovery is the share of the *contained metal* reporting to a product. It is
  not the mass yield, which is the share of the *total mass*.
* Values are computed in the unit of the mass input and are never rounded.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from metallurgypy.core.exceptions import CalculationError, InvalidParameterError, ModelDomainError
from metallurgypy.core.modes import CalculationMode, resolve_mode
from metallurgypy.core.provenance import Provenance
from metallurgypy.core.results import CalculationResult, ChartData, OutputItem
from metallurgypy.core.units import (
    GRADE_UNITS,
    MASS_UNITS,
    RATIO_UNITS,
    Quantity,
    as_quantity,
    convert_exact,
)
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

_SUPPORTED_MODES = (CalculationMode.STANDARD, CalculationMode.HIGH_PRECISION)
_EXACT_METHOD = (
    "Exact rational arithmetic (fractions.Fraction) on the float64 inputs; each output is rounded once to float64"
)


def _mass(name: str, raw: Quantity | float) -> Quantity:
    quantity = as_quantity(name, raw, default_unit="t", allowed_units=MASS_UNITS)
    if quantity.value <= 0.0:
        raise InvalidParameterError(f"{name} must be strictly positive, got {quantity}.")
    return quantity


def _fraction(name: str, raw: Quantity | float, *, allowed: tuple[str, ...]) -> Quantity:
    """Normalise a grade or recovery and check it lies between 0 and 1 (0 % to 100 %)."""
    quantity = as_quantity(name, raw, default_unit="fraction", allowed_units=allowed)
    as_fraction = quantity.to("fraction").value
    if not 0.0 <= as_fraction <= 1.0:
        raise InvalidParameterError(
            f"{name} = {quantity} is outside the valid range of 0 to 1 (0 % to 100 %)."
        )
    return quantity


def _fq(value: float) -> Quantity:
    return Quantity(value, "fraction")


# --------------------------------------------------------------------------- #
# Single-product balance from a known recovery
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, kw_only=True)
class MassBalanceResult(CalculationResult):
    feed_mass: Quantity
    feed_grade: Quantity
    recovery: Quantity
    loss: Quantity
    metal_feed: Quantity
    metal_recovered: Quantity
    metal_remaining: Quantity

    def outputs(self) -> tuple[OutputItem, ...]:
        return (
            OutputItem("metal_feed", "Metal in feed", self.metal_feed),
            OutputItem("metal_recovered", "Metal recovered", self.metal_recovered),
            OutputItem("metal_remaining", "Metal remaining (lost)", self.metal_remaining),
            OutputItem("recovery", "Recovery", self.recovery),
            OutputItem("loss", "Loss (1 - recovery)", self.loss),
        )

    def chart_data(self) -> ChartData:
        return ChartData(
            title="Metal balance",
            categories=("Metal in feed", "Metal recovered", "Metal remaining"),
            values=(
                self.metal_feed.value,
                self.metal_recovered.value,
                self.metal_remaining.value,
            ),
            unit=self.metal_feed.unit,
            source=f"MassBalance {MassBalance.MODEL_VERSION}, calculated",
        )


class MassBalance:
    """Metal balance of one feed given its grade and the recovery to one product.

    >>> result = MassBalance(feed_mass=1000, feed_grade=0.025, recovery=0.92).calculate()
    >>> result.metal_recovered.value
    23.0
    """

    MODEL_ID = "mass_balance.recovery"
    MODEL_VERSION = "1.0"
    EQUATIONS = (
        "m_feed = F * g",
        "m_recovered = R * m_feed",
        "m_remaining = (1 - R) * m_feed",
    )
    ASSUMPTIONS = (
        "Single component, single time point, steady state.",
        "Grade is a mass fraction of the metal, on the same basis (dry or wet) as the feed mass.",
        "Recovery is the share of contained metal reporting to the product; it is not the mass yield.",
        "Inputs are taken as exact: measurement uncertainty is not propagated in standard mode.",
        "The balance is arithmetic. It does not show that the recovery is achievable in a real circuit.",
    )

    def __init__(
        self,
        feed_mass: Quantity | float,
        feed_grade: Quantity | float,
        recovery: Quantity | float,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        self._mode = resolve_mode(mode, _SUPPORTED_MODES)
        self._tol = tolerances
        self.feed_mass = _mass("feed_mass", feed_mass)
        self.feed_grade = _fraction("feed_grade", feed_grade, allowed=GRADE_UNITS)
        self.recovery = _fraction("recovery", recovery, allowed=RATIO_UNITS)

    def calculate(self) -> MassBalanceResult:
        unit = self.feed_mass.unit
        mass = self.feed_mass.value
        grade = self.feed_grade.to("fraction").value
        rec = self.recovery.to("fraction").value

        exact = self._mode is CalculationMode.HIGH_PRECISION
        if exact:
            f_mass = Fraction(mass)
            f_grade = convert_exact(self.feed_grade.value, self.feed_grade.unit, "fraction")
            f_rec = convert_exact(self.recovery.value, self.recovery.unit, "fraction")
            f_feed = f_mass * f_grade
            metal_feed = float(f_feed)
            metal_recovered = float(f_rec * f_feed)
            metal_remaining = float(f_feed - f_rec * f_feed)
            loss = float(1 - f_rec)
        else:
            metal_feed = mass * grade
            metal_recovered = rec * metal_feed
            # Subtraction keeps the balance exact; (1 - R) * m_feed is the independent cross-check.
            metal_remaining = metal_feed - metal_recovered
            loss = 1.0 - rec
            cross_check = (1.0 - rec) * metal_feed
            if not self._tol.isclose(metal_remaining, cross_check):
                raise CalculationError(
                    f"Remaining metal {metal_remaining!r} {unit} disagrees with (1 - R) * m_feed "
                    f"= {cross_check!r} {unit}; this is a bug."
                )

        warnings: list[str] = []
        if grade == 0.0:
            warnings.append("Feed grade is zero: every metal quantity is zero.")
        if rec == 1.0:
            warnings.append("Recovery is exactly 100 %: no metal is lost. Check this input.")

        provenance = Provenance(
            model_id=self.MODEL_ID,
            model_version=self.MODEL_VERSION,
            method=_EXACT_METHOD if exact else "Closed-form evaluation in float64",
            equations=self.EQUATIONS,
            assumptions=self.ASSUMPTIONS,
            inputs={
                "feed_mass": self.feed_mass,
                "feed_grade": self.feed_grade,
                "recovery": self.recovery,
            },
            tolerances=self._tol,
            calculation_mode=self._mode.value,
        )
        return MassBalanceResult(
            provenance=provenance,
            warnings=tuple(warnings),
            feed_mass=self.feed_mass,
            feed_grade=_fq(grade),
            recovery=_fq(rec),
            loss=_fq(loss),
            metal_feed=Quantity(metal_feed, unit),
            metal_recovered=Quantity(metal_recovered, unit),
            metal_remaining=Quantity(metal_remaining, unit),
        )


# --------------------------------------------------------------------------- #
# Two-product balance from the three grades
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, kw_only=True)
class TwoProductResult(CalculationResult):
    feed_mass: Quantity
    concentrate_mass: Quantity
    tailings_mass: Quantity
    mass_yield: Quantity
    recovery: Quantity
    enrichment_ratio: Quantity
    metal_feed: Quantity
    metal_concentrate: Quantity
    metal_tailings: Quantity
    mass_closure_residual: Quantity
    metal_closure_residual: Quantity

    def outputs(self) -> tuple[OutputItem, ...]:
        return (
            OutputItem("concentrate_mass", "Concentrate mass", self.concentrate_mass),
            OutputItem("tailings_mass", "Tailings mass", self.tailings_mass),
            OutputItem("mass_yield", "Mass yield (concentrate / feed)", self.mass_yield),
            OutputItem("recovery", "Metal recovery to concentrate", self.recovery),
            OutputItem("enrichment_ratio", "Enrichment ratio (c / g)", self.enrichment_ratio),
            OutputItem("metal_feed", "Metal in feed", self.metal_feed),
            OutputItem("metal_concentrate", "Metal in concentrate", self.metal_concentrate),
            OutputItem("metal_tailings", "Metal in tailings", self.metal_tailings),
            OutputItem("mass_closure_residual", "Closure residual (mass)", self.mass_closure_residual),
            OutputItem(
                "metal_closure_residual", "Closure residual (metal)", self.metal_closure_residual
            ),
        )

    def chart_data(self) -> ChartData:
        return ChartData(
            title="Metal distribution",
            categories=("Metal in feed", "In concentrate", "In tailings"),
            values=(
                self.metal_feed.value,
                self.metal_concentrate.value,
                self.metal_tailings.value,
            ),
            unit=self.metal_feed.unit,
            source=f"TwoProductBalance {TwoProductBalance.MODEL_VERSION}, calculated",
        )


class TwoProductBalance:
    """Split of a feed into concentrate and tailings from the three measured grades.

    With feed ``F``, grades ``g`` (feed), ``c`` (concentrate), ``t`` (tailings)::

        C = F (g - t) / (c - t)      T = F (c - g) / (c - t)
        mass yield = C / F           recovery = C c / (F g)
    """

    MODEL_ID = "mass_balance.two_product"
    MODEL_VERSION = "1.0"
    EQUATIONS = (
        "C = F * (g - t) / (c - t)",
        "T = F * (c - g) / (c - t)",
        "mass_yield = C / F",
        "recovery = C * c / (F * g)",
        "enrichment_ratio = c / g",
    )
    ASSUMPTIONS = (
        "Two products only, single component, steady state, no accumulation.",
        "Grades are mass fractions of the metal on the same basis (dry or wet) as the masses.",
        "Grades are taken as exact: analytical uncertainty is not propagated in standard mode.",
        "Mass and metal balances are closed by construction; the residuals reported are numerical only.",
        "Real grades carry sampling and assay error, which can make a computed yield "
        "or recovery physically meaningless even when the arithmetic is valid.",
    )

    def __init__(
        self,
        feed_mass: Quantity | float,
        feed_grade: Quantity | float,
        concentrate_grade: Quantity | float,
        tailings_grade: Quantity | float,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        self._mode = resolve_mode(mode, (CalculationMode.STANDARD,))  # high_precision: MassBalance only
        self._tol = tolerances
        self.feed_mass = _mass("feed_mass", feed_mass)
        self.feed_grade = _fraction("feed_grade", feed_grade, allowed=GRADE_UNITS)
        self.concentrate_grade = _fraction("concentrate_grade", concentrate_grade, allowed=GRADE_UNITS)
        self.tailings_grade = _fraction("tailings_grade", tailings_grade, allowed=GRADE_UNITS)

    def calculate(self) -> TwoProductResult:
        unit = self.feed_mass.unit
        f_mass = self.feed_mass.value
        g = self.feed_grade.to("fraction").value
        c = self.concentrate_grade.to("fraction").value
        t = self.tailings_grade.to("fraction").value

        if c == t:
            raise ModelDomainError(
                "Concentrate and tailings grades are equal: the split between the two products "
                "cannot be determined from the grades."
            )
        if not min(c, t) <= g <= max(c, t):
            raise ModelDomainError(
                "The feed grade must lie between the tailings and concentrate grades "
                f"(got feed {g!r}, concentrate {c!r}, tailings {t!r}); otherwise a product "
                "would need a negative mass."
            )
        if g == 0.0:
            raise ModelDomainError(
                "Feed grade is zero: recovery and enrichment ratio are undefined."
            )

        c_mass = f_mass * (g - t) / (c - t)
        t_mass = f_mass * (c - g) / (c - t)
        mass_residual = f_mass - (c_mass + t_mass)
        metal_feed = f_mass * g
        metal_c = c_mass * c
        metal_t = t_mass * t
        metal_residual = metal_feed - (metal_c + metal_t)

        if not self._tol.isclose(f_mass, c_mass + t_mass) or not self._tol.isclose(
            metal_feed, metal_c + metal_t
        ):
            raise CalculationError(
                "Mass or metal balance does not close within tolerance; this is a bug."
            )

        warnings: list[str] = []
        if c < t:
            warnings.append(
                "Concentrate grade is lower than tailings grade: check which stream is which."
            )
        if c_mass == 0.0 or t_mass == 0.0:
            warnings.append("One product has zero mass: the feed grade equals a product grade.")

        provenance = Provenance(
            model_id=self.MODEL_ID,
            model_version=self.MODEL_VERSION,
            method="Closed-form evaluation in float64",
            equations=self.EQUATIONS,
            assumptions=self.ASSUMPTIONS,
            inputs={
                "feed_mass": self.feed_mass,
                "feed_grade": self.feed_grade,
                "concentrate_grade": self.concentrate_grade,
                "tailings_grade": self.tailings_grade,
            },
            tolerances=self._tol,
            calculation_mode=self._mode.value,
        )
        return TwoProductResult(
            provenance=provenance,
            warnings=tuple(warnings),
            feed_mass=self.feed_mass,
            concentrate_mass=Quantity(c_mass, unit),
            tailings_mass=Quantity(t_mass, unit),
            mass_yield=_fq(c_mass / f_mass),
            recovery=_fq(metal_c / metal_feed),
            enrichment_ratio=Quantity(c / g, "ratio"),
            metal_feed=Quantity(metal_feed, unit),
            metal_concentrate=Quantity(metal_c, unit),
            metal_tailings=Quantity(metal_t, unit),
            mass_closure_residual=Quantity(mass_residual, unit),
            metal_closure_residual=Quantity(metal_residual, unit),
        )
