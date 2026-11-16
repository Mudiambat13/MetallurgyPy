"""Rounding for PRESENTATION only. Nothing here changes a value held by the engine."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

from metallurgypy.core.exceptions import InvalidParameterError


def _check(value: float) -> None:
    if not math.isfinite(value):
        raise InvalidParameterError(f"Cannot round a non-finite value: {value!r}.")


def round_sig(value: float, digits: int) -> float:
    """Round to ``digits`` significant figures (half away from zero, on the exact decimal expansion)."""
    _check(value)
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 1:
        raise InvalidParameterError("digits must be an integer >= 1.")
    if value == 0.0:
        return 0.0
    exponent = math.floor(math.log10(abs(value)))
    quantum = Decimal(1).scaleb(exponent - digits + 1)
    return float(Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP))


def format_sig(value: float, digits: int) -> str:
    """Text with exactly ``digits`` significant figures, trailing zeros kept (``0.0250``)."""
    _check(value)
    if value == 0.0:
        return "0"
    rounded = Decimal(repr(round_sig(value, digits)))
    exponent = math.floor(math.log10(abs(float(rounded))))
    decimals = max(digits - exponent - 1, 0)
    if exponent >= digits:  # integer part longer than the requested digits: keep it whole
        return f"{rounded:.0f}"
    return f"{rounded:.{decimals}f}"


def format_with_uncertainty(
    value: float, standard_uncertainty: float, uncertainty_digits: int = 2
) -> str:
    """GUM-style concise notation, e.g. ``23.00(12)`` for 23.0012 with u = 0.1234.

    The uncertainty is rounded to ``uncertainty_digits`` (1 or 2) significant figures and the
    value is rounded to the same decimal place. If the uncertainty is zero, the value is shown as is.
    """
    _check(value)
    _check(standard_uncertainty)
    if standard_uncertainty < 0.0:
        raise InvalidParameterError("The uncertainty must be >= 0.")
    if uncertainty_digits not in (1, 2):
        raise InvalidParameterError("uncertainty_digits must be 1 or 2.")
    if standard_uncertainty == 0.0:
        return repr(value)
    u_rounded = round_sig(standard_uncertainty, uncertainty_digits)
    u_exp = math.floor(math.log10(u_rounded))
    place = u_exp - uncertainty_digits + 1  # power of ten of the last kept digit
    value_text = f"{Decimal(value).quantize(Decimal(1).scaleb(place), rounding=ROUND_HALF_UP):f}"
    if place < 0:
        digits_u = round(u_rounded / 10.0**place)
        return f"{value_text}({digits_u})"
    return f"{value_text} +/- {u_rounded:.0f}"
