"""Descriptive statistics, regression, correlation, outliers and time-series helpers.

Pure standard-library implementation (no NumPy needed). Functions return plain
dataclasses and raise :class:`InvalidParameterError` on unusable data; they never
silently drop values. Sample (n - 1) estimators are used for dispersion.
"""

from __future__ import annotations

import math
import statistics as _st
from collections.abc import Sequence
from dataclasses import dataclass

from metallurgypy.core.exceptions import CalculationError, InvalidParameterError


def _clean(name: str, values: Sequence[float], minimum: int) -> list[float]:
    data = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise InvalidParameterError(f"{name} contains a non-numeric or non-finite value: {v!r}.")
        data.append(float(v))
    if len(data) < minimum:
        raise InvalidParameterError(f"{name} needs at least {minimum} values, got {len(data)}.")
    return data


@dataclass(frozen=True)
class Description:
    n: int
    mean: float
    median: float
    std: float  # sample standard deviation (n - 1); 0.0 when n == 1
    minimum: float
    maximum: float
    q1: float
    q3: float
    cv: float | None  # coefficient of variation std / |mean|; None if mean == 0


def describe(values: Sequence[float]) -> Description:
    data = _clean("values", values, 1)
    mean = _st.fmean(data)
    std = _st.stdev(data) if len(data) > 1 else 0.0
    if len(data) >= 2:
        q1, _, q3 = _st.quantiles(data, n=4, method="inclusive")
    else:
        q1 = q3 = data[0]
    return Description(
        n=len(data),
        mean=mean,
        median=_st.median(data),
        std=std,
        minimum=min(data),
        maximum=max(data),
        q1=q1,
        q3=q3,
        cv=None if mean == 0.0 else std / abs(mean),
    )


@dataclass(frozen=True)
class Regression:
    slope: float
    intercept: float
    r_squared: float
    slope_stderr: float | None  # None when n == 2 (no residual degrees of freedom)
    intercept_stderr: float | None
    n: int

    def predict(self, x: float) -> float:
        return self.intercept + self.slope * x


def linear_regression(x: Sequence[float], y: Sequence[float]) -> Regression:
    """Ordinary least squares ``y = intercept + slope * x``."""
    xs, ys = _clean("x", x, 2), _clean("y", y, 2)
    if len(xs) != len(ys):
        raise InvalidParameterError("x and y must have the same length.")
    n = len(xs)
    mx, my = _st.fmean(xs), _st.fmean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    if sxx == 0.0:
        raise CalculationError("All x values are equal: the regression slope is undefined.")
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys, strict=True))
    syy = sum((b - my) ** 2 for b in ys)
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_res = sum((b - (intercept + slope * a)) ** 2 for a, b in zip(xs, ys, strict=True))
    r2 = 1.0 if syy == 0.0 else 1.0 - ss_res / syy
    slope_se: float | None = None
    intercept_se: float | None = None
    if n > 2:
        s2 = ss_res / (n - 2)
        slope_se = math.sqrt(s2 / sxx)
        intercept_se = math.sqrt(s2 * (1.0 / n + mx * mx / sxx))
    return Regression(slope, intercept, r2, slope_se, intercept_se, n)


def correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson correlation coefficient."""
    xs, ys = _clean("x", x, 2), _clean("y", y, 2)
    if len(xs) != len(ys):
        raise InvalidParameterError("x and y must have the same length.")
    if len(set(xs)) == 1 or len(set(ys)) == 1:
        raise CalculationError("A constant series has no defined correlation.")
    return _st.correlation(xs, ys)


@dataclass(frozen=True)
class Outliers:
    indices: tuple[int, ...]
    scores: tuple[float, ...]  # modified z-score of every value
    threshold: float
    median: float
    mad: float


def detect_outliers(values: Sequence[float], threshold: float = 3.5) -> Outliers:
    """Flag values with a modified z-score (median/MAD based) above ``threshold``.

    ``score = 0.6745 * (x - median) / MAD`` (Iglewicz and Hoaglin). The default
    3.5 is their recommended cut-off, a screening rule and not a proof that a
    value is wrong. Raises if MAD is zero (more than half the values identical).
    """
    data = _clean("values", values, 3)
    if threshold <= 0:
        raise InvalidParameterError("threshold must be positive.")
    med = _st.median(data)
    mad = _st.median([abs(v - med) for v in data])
    if mad == 0.0:
        raise CalculationError("MAD is zero (at least half the values are identical): the modified z-score is undefined.")
    scores = tuple(0.6745 * (v - med) / mad for v in data)
    flagged = tuple(i for i, s in enumerate(scores) if abs(s) > threshold)
    return Outliers(flagged, scores, threshold, med, mad)


def moving_average(values: Sequence[float], window: int) -> list[float]:
    """Trailing simple moving average; the first ``window - 1`` points are not produced."""
    data = _clean("values", values, 1)
    if isinstance(window, bool) or not isinstance(window, int) or window < 1 or window > len(data):
        raise InvalidParameterError(f"window must be an integer between 1 and {len(data)}.")
    return [_st.fmean(data[i - window + 1 : i + 1]) for i in range(window - 1, len(data))]


@dataclass(frozen=True)
class Variability:
    within_std: float  # pooled within-group sample standard deviation
    between_std_of_means: float
    groups: int
    total_n: int


def variability(groups: Sequence[Sequence[float]]) -> Variability:
    """Within-group (repeatability) and between-group dispersion of replicate groups."""
    if len(groups) < 2:
        raise InvalidParameterError("Need at least two groups.")
    cleaned = [_clean(f"group {i}", g, 2) for i, g in enumerate(groups)]
    dof = sum(len(g) - 1 for g in cleaned)
    pooled = math.sqrt(sum(sum((v - _st.fmean(g)) ** 2 for v in g) for g in cleaned) / dof)
    means = [_st.fmean(g) for g in cleaned]
    return Variability(pooled, _st.stdev(means), len(cleaned), sum(len(g) for g in cleaned))


__all__ = [
    "Description",
    "Outliers",
    "Regression",
    "Variability",
    "correlation",
    "describe",
    "detect_outliers",
    "linear_regression",
    "moving_average",
    "variability",
]
