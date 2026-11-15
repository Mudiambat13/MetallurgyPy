"""One-line input normalisation shared by all models."""

from __future__ import annotations

from metallurgypy.core.exceptions import InvalidParameterError
from metallurgypy.core.units import Quantity, as_quantity, dimension_of, units_of


def qty(
    name: str,
    raw: Quantity | float | int,
    *,
    unit: str,
    allowed: tuple[str, ...] | None = None,
    positive: bool = False,
    non_negative: bool = False,
    fraction: bool = False,
    open_fraction: bool = False,
) -> Quantity:
    """Normalise one input.

    ``unit`` is the documented default for bare numbers; ``allowed`` defaults to
    every unit of the same dimension. ``positive`` means strictly > 0,
    ``non_negative`` means >= 0, ``fraction`` requires 0 <= value <= 1 once
    expressed as a fraction, ``open_fraction`` requires 0 < value < 1.
    """
    quantity = as_quantity(
        name,
        raw,
        default_unit=unit,
        allowed_units=allowed or units_of(dimension_of(unit)),
    )
    if positive and quantity.value <= 0.0:
        raise InvalidParameterError(f"{name} must be strictly positive, got {quantity}.")
    if non_negative and quantity.value < 0.0:
        raise InvalidParameterError(f"{name} must be >= 0, got {quantity}.")
    if fraction or open_fraction:
        as_fraction = quantity.to("fraction").value
        low_ok = as_fraction > 0.0 if open_fraction else as_fraction >= 0.0
        high_ok = as_fraction < 1.0 if open_fraction else as_fraction <= 1.0
        if not (low_ok and high_ok):
            bounds = "0 to 1, both excluded" if open_fraction else "0 to 1 (0 % to 100 %)"
            raise InvalidParameterError(
                f"{name} = {quantity} is outside the valid range of {bounds}."
            )
    return quantity
