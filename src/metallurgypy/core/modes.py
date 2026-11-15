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

    A mode a model does not implement is refused explicitly instead of
    silently falling back to ``float64``. ``uncertainty_aware`` is provided by
    :func:`metallurgypy.precision.propagate_model`, not by the model itself.
    """
    try:
        resolved = CalculationMode(mode)
    except ValueError:
        valid = ", ".join(m.value for m in CalculationMode)
        raise InvalidParameterError(f"Unknown calculation mode {mode!r}. Valid: {valid}.") from None
    if resolved is CalculationMode.UNCERTAINTY_AWARE and resolved not in tuple(supported):
        raise InvalidParameterError(
            "Models run on nominal values. For uncertainty-aware results use "
            "metallurgypy.precision.propagate_model(model_id, measurements)."
        )
    if resolved not in tuple(supported):
        raise InvalidParameterError(
            f"Calculation mode {resolved.value!r} is not implemented for this model yet."
        )
    return resolved
