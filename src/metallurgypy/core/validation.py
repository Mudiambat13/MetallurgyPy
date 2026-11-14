"""Input validation helpers and numerical tolerances."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from metallurgypy.core.exceptions import InvalidParameterError


def require_real(name: str, value: object) -> float:
    """Return ``value`` as a ``float`` after checking it is a finite real number."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidParameterError(f"{name} must be a real number, got {type(value).__name__}.")
    number = float(value)
    if not math.isfinite(number):
        raise InvalidParameterError(f"{name} must be finite, got {value!r}.")
    return number


def require_positive(name: str, value: object) -> float:
    number = require_real(name, value)
    if number <= 0.0:
        raise InvalidParameterError(f"{name} must be strictly positive, got {number!r}.")
    return number


def require_non_negative(name: str, value: object) -> float:
    number = require_real(name, value)
    if number < 0.0:
        raise InvalidParameterError(f"{name} must be >= 0, got {number!r}.")
    return number


def require_between(name: str, value: object, low: float, high: float, *, what: str = "") -> float:
    """Require ``low <= value <= high`` (both bounds included)."""
    number = require_real(name, value)
    if not low <= number <= high:
        suffix = f" ({what})" if what else ""
        raise InvalidParameterError(
            f"{name} must be between {low!r} and {high!r}{suffix}, got {number!r}."
        )
    return number


@dataclass(frozen=True)
class Tolerances:
    """Relative and absolute tolerances for approximate comparisons.

    The defaults are numerical choices, not physical constants. They sit far
    above the rounding error accumulated by the handful of float64 operations
    used in the current models (machine epsilon is about 2.2e-16) and far
    below any realistic measurement precision. They are recorded in the
    provenance of each result and can be overridden by the caller.
    """

    rel: float = 1e-9
    abs: float = 1e-12

    def __post_init__(self) -> None:
        require_non_negative("Tolerances.rel", self.rel)
        require_non_negative("Tolerances.abs", self.abs)

    def isclose(self, a: float, b: float) -> bool:
        """True if ``a`` and ``b`` agree within the relative or absolute tolerance."""
        return abs(a - b) <= max(self.rel * max(abs(a), abs(b)), self.abs)


DEFAULT_TOLERANCES = Tolerances()
