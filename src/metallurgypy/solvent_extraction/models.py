"""Solvent extraction and stripping. Equations: docs/scientific_methods/solvent_extraction.md.

The distribution coefficient D = [M]org / [M]aq is always a user input for a
stated chemical system. No behaviour of any extractant is built in.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from metallurgypy.core.exceptions import (
    ConvergenceError,
    InvalidParameterError,
    ModelDomainError,
)
from metallurgypy.core.inputs import qty
from metallurgypy.core.model_base import BaseModel, out
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.results import GenericResult
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

_Q = Quantity | float
_LINEAR_ASSUMPTION = (
    "Constant distribution coefficient D over the whole concentration range (linear isotherm); "
    "real extractants saturate, so check D at the loaded-organic concentration."
)


def _ratio(name: str, raw: _Q) -> Quantity:
    return qty(name, raw, unit="ratio", allowed=("ratio",), positive=True)


class SingleStageExtraction(BaseModel):
    """One equilibrium extraction stage with a constant distribution coefficient."""

    MODEL_ID = "solvent_extraction.single_stage"
    EQUATIONS = (
        "D = C_org / C_aq   (at equilibrium)",
        "C_aq = C_feed / (1 + D * r)      r = O/A (volume ratio)",
        "C_org = D * C_aq",
        "extraction = D * r / (1 + D * r)",
    )
    ASSUMPTIONS = (
        _LINEAR_ASSUMPTION,
        "Organic enters free of the metal; the stage reaches equilibrium; phases are immiscible and volumes unchanged.",
        "D is for the stated chemical system, pH, temperature and extractant, and comes from the user.",
    )

    def __init__(
        self,
        feed_concentration: _Q,
        distribution_coefficient: _Q,
        oa_ratio: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "feed_concentration": qty("feed_concentration", feed_concentration, unit="g/L", non_negative=True),
            "distribution_coefficient": _ratio("distribution_coefficient", distribution_coefficient),
            "oa_ratio": _ratio("oa_ratio", oa_ratio),
        }

    def calculate(self) -> GenericResult:
        feed = self._inputs["feed_concentration"]
        d = self._inputs["distribution_coefficient"].value
        r = self._inputs["oa_ratio"].value
        c_aq = feed.value / (1.0 + d * r)
        c_org = d * c_aq
        residual = feed.value - (c_aq + r * c_org)
        unit = feed.unit
        return self._result(
            [
                out("raffinate_concentration", "Raffinate (aqueous) concentration", c_aq, unit),
                out("loaded_organic_concentration", "Loaded organic concentration", c_org, unit),
                out("extraction", "Extraction (fraction of metal transferred)", d * r / (1.0 + d * r), "fraction"),
                out("ao_ratio", "A/O ratio", 1.0 / r, "ratio"),
                out("balance_residual", "Metal balance residual", residual, unit),
            ]
        )


class StrippingStage(BaseModel):
    """One equilibrium stripping stage with a constant (organic/aqueous) distribution coefficient."""

    MODEL_ID = "solvent_extraction.stripping_single_stage"
    EQUATIONS = (
        "y0 * O + x_in * A = y * O + x * A",
        "y = D_s * x",
        "x = (y0 + (A/O) * x_in) / (D_s + A/O)",
        "stripping = (y0 - y) / y0",
    )
    ASSUMPTIONS = (
        _LINEAR_ASSUMPTION.replace("extraction", "stripping"),
        "D_s = C_org / C_aq measured under STRIPPING conditions (typically much lower than in extraction).",
        "Phases immiscible, volumes unchanged, equilibrium reached.",
    )

    def __init__(
        self,
        loaded_organic_concentration: _Q,
        strip_distribution_coefficient: _Q,
        ao_ratio: _Q,
        strip_aqueous_inlet_concentration: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "loaded_organic_concentration": qty("loaded_organic_concentration", loaded_organic_concentration, unit="g/L", positive=True),
            "strip_distribution_coefficient": _ratio("strip_distribution_coefficient", strip_distribution_coefficient),
            "ao_ratio": _ratio("ao_ratio", ao_ratio),
            "strip_aqueous_inlet_concentration": qty("strip_aqueous_inlet_concentration", strip_aqueous_inlet_concentration, unit="g/L", non_negative=True),
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        unit = i["loaded_organic_concentration"].unit
        y0 = i["loaded_organic_concentration"].value
        d = i["strip_distribution_coefficient"].value
        ao = i["ao_ratio"].value
        x_in = i["strip_aqueous_inlet_concentration"].to(unit).value
        x = (y0 + ao * x_in) / (d + ao)
        y = d * x
        return self._result(
            [
                out("strip_liquor_concentration", "Strip liquor concentration", x, unit),
                out("stripped_organic_concentration", "Stripped organic concentration", y, unit),
                out("stripping", "Stripping (fraction removed from organic)", (y0 - y) / y0, "fraction"),
                out("balance_residual", "Metal balance residual", y0 + ao * x_in - y - ao * x, unit),
            ]
        )


def _unextracted_fraction(extraction_factor: float, stages: float) -> float:
    """Kremser fraction of metal left in the raffinate after ``stages`` counter-current stages."""
    e, n = extraction_factor, stages
    if abs(e - 1.0) < 1e-12:
        return 1.0 / (n + 1.0)
    if e > 1.0:
        w = float(e ** (-(n + 1.0)))
        return float((e - 1.0) * w / (1.0 - w))
    return float((e - 1.0) / (e ** (n + 1.0) - 1.0))


class CountercurrentExtraction(BaseModel):
    """Counter-current cascade with a constant D (Kremser equation), fresh organic."""

    MODEL_ID = "solvent_extraction.countercurrent_kremser"
    EQUATIONS = (
        "E = D * r      (extraction factor, r = O/A)",
        "phi = (E - 1) / (E^(N+1) - 1)     (fraction left in raffinate; phi = 1/(N+1) if E = 1)",
        "C_raffinate = phi * C_feed",
        "C_loaded = (C_feed - C_raffinate) / r",
    )
    ASSUMPTIONS = (
        _LINEAR_ASSUMPTION,
        "N equilibrium (theoretical) stages in counter-current; the organic enters free of the metal.",
        "Mixer-settler efficiency is not applied: real stage efficiency is below 100 % and must be handled by the user.",
    )

    def __init__(
        self,
        feed_concentration: _Q,
        distribution_coefficient: _Q,
        oa_ratio: _Q,
        stages: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        n = _ratio("stages", stages)
        if n.value != int(n.value) or n.value > 1000:
            raise InvalidParameterError(f"stages must be a whole number between 1 and 1000, got {n.value!r}.")
        self._inputs = {
            "feed_concentration": qty("feed_concentration", feed_concentration, unit="g/L", non_negative=True),
            "distribution_coefficient": _ratio("distribution_coefficient", distribution_coefficient),
            "oa_ratio": _ratio("oa_ratio", oa_ratio),
            "stages": n,
        }

    def calculate(self) -> GenericResult:
        i = self._inputs
        feed = i["feed_concentration"]
        e = i["distribution_coefficient"].value * i["oa_ratio"].value
        n = i["stages"].value
        phi = _unextracted_fraction(e, n)
        raffinate = phi * feed.value
        loaded = (feed.value - raffinate) / i["oa_ratio"].value
        warnings = []
        if e < 1.0:
            warnings.append(
                f"Extraction factor {e!r} < 1: even with infinite stages at most {1.0 - e:.6g} of the metal can be extracted."
            )
        return self._result(
            [
                out("extraction_factor", "Extraction factor E = D * O/A", e, "ratio"),
                out("raffinate_concentration", "Raffinate concentration", raffinate, feed.unit),
                out("loaded_organic_concentration", "Loaded organic concentration", loaded, feed.unit),
                out("extraction", "Extraction (fraction)", 1.0 - phi, "fraction"),
            ],
            warnings=warnings,
        )


class StagesRequired(BaseModel):
    """Theoretical counter-current stages needed for a target extraction (constant D)."""

    MODEL_ID = "solvent_extraction.stages_required"
    EQUATIONS = (
        "E = D * r",
        "phi = 1 - extraction",
        "N = ln(1 + (E - 1) / phi) / ln(E) - 1      (N = 1/phi - 1 if E = 1)",
    )
    ASSUMPTIONS = (
        _LINEAR_ASSUMPTION,
        "N is the continuous number of theoretical stages; the practical (integer) count is its ceiling, before stage efficiency.",
    )

    def __init__(
        self,
        distribution_coefficient: _Q,
        oa_ratio: _Q,
        target_extraction: _Q,
        *,
        mode: CalculationMode | str = CalculationMode.STANDARD,
        tolerances: Tolerances = DEFAULT_TOLERANCES,
    ) -> None:
        super().__init__(mode=mode, tolerances=tolerances)
        self._inputs = {
            "distribution_coefficient": _ratio("distribution_coefficient", distribution_coefficient),
            "oa_ratio": _ratio("oa_ratio", oa_ratio),
            "target_extraction": qty("target_extraction", target_extraction, unit="fraction", allowed=("fraction", "%"), open_fraction=True),
        }

    def calculate(self) -> GenericResult:
        e = self._inputs["distribution_coefficient"].value * self._inputs["oa_ratio"].value
        phi = 1.0 - self._inputs["target_extraction"].to("fraction").value
        if abs(e - 1.0) < 1e-12:
            n = 1.0 / phi - 1.0
        else:
            if e < 1.0 and phi <= 1.0 - e:
                raise ModelDomainError(
                    f"Unreachable target: with E = {e!r} < 1 the extraction cannot exceed {1.0 - e:.6g} "
                    "whatever the number of stages. Raise D or the O/A ratio."
                )
            n = math.log(1.0 + (e - 1.0) / phi) / math.log(e) - 1.0
        n = max(n, 0.0)
        return self._result(
            [
                out("theoretical_stages", "Theoretical stages (continuous)", n, "ratio"),
                out("stages_ceiling", "Theoretical stages (rounded up)", float(math.ceil(n - 1e-12)), "ratio"),
                out("extraction_factor", "Extraction factor E = D * O/A", e, "ratio"),
            ]
        )


@dataclass(frozen=True)
class McCabeThieleResult:
    stages: float
    stage_points: tuple[tuple[float, float], ...]  # (aqueous, organic) at each equilibrium stage
    loaded_organic: float
    raffinate: float
    warnings: tuple[str, ...]


class McCabeThieleAnalysis:
    """Stage-by-stage construction of a counter-current extraction with a tabulated isotherm.

    The isotherm is user data: ``aqueous[i]`` and ``organic[i]`` in the same
    concentration unit, both strictly increasing, starting at or above zero.
    Interpolation is linear; extrapolation beyond the data is refused.

    Operating line (organic fresh with concentration ``organic_in``)::

        y = organic_in + (A/O) * (x - raffinate)

    Stages are stepped from the feed end. The count is fractional: the last
    stage is prorated by the aqueous concentration reached versus the target.
    """

    MAX_STAGES = 100

    def __init__(
        self,
        aqueous: Sequence[float],
        organic: Sequence[float],
        *,
        feed: float,
        raffinate: float,
        ao_ratio: float,
        organic_in: float = 0.0,
    ) -> None:
        if len(aqueous) != len(organic) or len(aqueous) < 2:
            raise InvalidParameterError("The isotherm needs at least two points with equal-length columns.")
        for name, values in (("aqueous", aqueous), ("organic", organic)):
            if any(not math.isfinite(v) or v < 0 for v in values):
                raise InvalidParameterError(f"Isotherm {name} values must be finite and >= 0.")
            if any(b <= a for a, b in zip(values, values[1:], strict=False)):
                raise InvalidParameterError(f"Isotherm {name} values must be strictly increasing.")
        if not 0.0 <= raffinate < feed:
            raise InvalidParameterError("Need 0 <= raffinate < feed.")
        if ao_ratio <= 0.0 or organic_in < 0.0:
            raise InvalidParameterError("ao_ratio must be > 0 and organic_in >= 0.")
        self._x, self._y = list(aqueous), list(organic)
        self.feed, self.raffinate, self.ao, self.organic_in = feed, raffinate, ao_ratio, organic_in

    def _x_at_equilibrium(self, y: float) -> float:
        ys, xs = self._y, self._x
        if y < ys[0] or y > ys[-1]:
            raise ModelDomainError(
                f"Organic concentration {y!r} is outside the isotherm data [{ys[0]!r}, {ys[-1]!r}]: "
                "extrapolation is refused. Extend the isotherm data."
            )
        for j in range(1, len(ys)):
            if y <= ys[j]:
                frac = (y - ys[j - 1]) / (ys[j] - ys[j - 1])
                return xs[j - 1] + frac * (xs[j] - xs[j - 1])
        return xs[-1]  # unreachable: y <= ys[-1] was checked

    def run(self) -> McCabeThieleResult:
        x_in = self.feed
        points: list[tuple[float, float]] = []
        for n in range(1, self.MAX_STAGES + 1):
            y = self.organic_in + self.ao * (x_in - self.raffinate)  # organic leaving this stage
            x_out = self._x_at_equilibrium(y)
            if x_out >= x_in - 1e-15:
                raise ConvergenceError(
                    f"Stage {n} does not lower the aqueous concentration (pinch): the target raffinate "
                    "is unreachable at this A/O ratio. Increase O (lower A/O)."
                )
            points.append((x_out, y))
            if x_out <= self.raffinate + 1e-15:
                previous = self.feed if n == 1 else points[-2][0]
                fraction = (previous - self.raffinate) / (previous - x_out)
                loaded = points[0][1]
                return McCabeThieleResult(
                    stages=(n - 1) + fraction,
                    stage_points=tuple(points),
                    loaded_organic=loaded,
                    raffinate=self.raffinate,
                    warnings=("Fractional stage count: round up and apply the stage efficiency.",),
                )
            x_in = x_out
        raise ConvergenceError(f"More than {self.MAX_STAGES} stages needed: the target is not practically reachable.")
