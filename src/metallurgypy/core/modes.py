"""Calculation modes (see the *Numerical precision and uncertainty* page)."""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum

from metallurgypy.core.exceptions import InvalidParameterError


class CalculationMode(str, Enum):
    STANDARD = "standard"
    HIGH_PRECISION = "high_precision"
    UNCERTAINTY_AWARE = "uncertainty_aware"


def resolve_mode(
    mode: CalculationMode | str, supported: Iterable[CalculationMode]
) -> CalculationMode:
    """Validate ``mode`` and make sure the calling model implements it.

    Only ``standard`` exists today. The other modes are refused explicitly
    instead of silently falling back to ``float64``.
    """
    try:
        resolved = CalculationMode(mode)
    except ValueError:
        valid = ", ".join(m.value for m in CalculationMode)
        raise InvalidParameterError(f"Unknown calculation mode {mode!r}. Valid: {valid}.") from None
    if resolved not in tuple(supported):
        raise InvalidParameterError(
            f"Calculation mode {resolved.value!r} is not implemented for this model yet."
        )
    return resolved
