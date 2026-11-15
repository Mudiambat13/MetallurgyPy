"""Small numerical routines with documented stopping criteria."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from metallurgypy.core.exceptions import ConvergenceError, InvalidParameterError


@dataclass(frozen=True)
class RootResult:
    root: float
    iterations: int
    bracket_width: float
    residual: float

    def status(self) -> str:
        return (
            f"converged in {self.iterations} bisection iterations "
            f"(bracket width {self.bracket_width:.3g}, residual {self.residual:.3g})"
        )


def bisect(
    f: Callable[[float], float],
    low: float,
    high: float,
    *,
    rel_tol: float = 1e-14,
    max_iter: int = 200,
) -> RootResult:
    """Bisection on ``[low, high]`` for a function that changes sign.

    Stops when the bracket is narrower than ``rel_tol * max(|mid|, tiny)`` or
    when ``f(mid)`` is exactly zero. Raises :class:`InvalidParameterError` if the
    bracket does not enclose a sign change and :class:`ConvergenceError` if
    ``max_iter`` is exhausted. Bisection halves the bracket each step, so 200
    iterations are far more than float64 needs (about 60).
    """
    f_low, f_high = f(low), f(high)
    if not (math.isfinite(f_low) and math.isfinite(f_high)):
        raise InvalidParameterError("Function is not finite at the bracket ends.")
    if f_low == 0.0:
        return RootResult(low, 0, high - low, 0.0)
    if f_high == 0.0:
        return RootResult(high, 0, high - low, 0.0)
    if f_low * f_high > 0.0:
        raise InvalidParameterError("The bracket does not enclose a root (no sign change).")
    for i in range(1, max_iter + 1):
        mid = 0.5 * (low + high)
        f_mid = f(mid)
        if f_mid == 0.0 or (high - low) <= rel_tol * max(abs(mid), 1e-300):
            return RootResult(mid, i, high - low, f_mid)
        if f_low * f_mid < 0.0:
            high = mid
        else:
            low, f_low = mid, f_mid
    raise ConvergenceError(f"Bisection did not converge in {max_iter} iterations.")
