"""Minimal, explicit unit handling for the quantities used by the first models.

Scope
-----
Two dimensions only, because those are the only ones the current models need:

``mass``
    ``g``, ``kg``, ``t`` (metric tonne), ``kt``, ``Mt``.
``dimensionless``
    ``fraction``, ``%``, ``ppm``, ``g/t``. ``ppm`` and ``g/t`` are by *mass*
    (1 g/t = 1 ppm = 1e-6), so they are only meaningful for mass-basis grades.

All factors are exact definitions, stored as integer ratios so that a
conversion adds at most the rounding of one multiplication and one division.

A general unit engine (Pint) will be adopted when modules need more dimensions
(volume, concentration, current, energy...). Until then this module keeps the
Core free of dependencies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from metallurgypy.core.exceptions import (
    DimensionError,
    InvalidParameterError,
    UnitConversionError,
)

MASS = "mass"
DIMENSIONLESS = "dimensionless"


@dataclass(frozen=True)
class _UnitDef:
    dimension: str
    num: int  # value_in_base = value * num / den
    den: int


_UNITS: dict[str, _UnitDef] = {
    # mass, base unit: kg
    "g": _UnitDef(MASS, 1, 1_000),
    "kg": _UnitDef(MASS, 1, 1),
    "t": _UnitDef(MASS, 1_000, 1),
    "kt": _UnitDef(MASS, 1_000_000, 1),
    "Mt": _UnitDef(MASS, 1_000_000_000, 1),
    # dimensionless, base unit: fraction
    "fraction": _UnitDef(DIMENSIONLESS, 1, 1),
    "%": _UnitDef(DIMENSIONLESS, 1, 100),
    "ppm": _UnitDef(DIMENSIONLESS, 1, 1_000_000),
    "g/t": _UnitDef(DIMENSIONLESS, 1, 1_000_000),
    # plain ratio (for outputs such as an enrichment ratio, which can exceed 1)
    "ratio": _UnitDef(DIMENSIONLESS, 1, 1),
}

MASS_UNITS: tuple[str, ...] = ("g", "kg", "t", "kt", "Mt")
GRADE_UNITS: tuple[str, ...] = ("fraction", "%", "ppm", "g/t")
RATIO_UNITS: tuple[str, ...] = ("fraction", "%")


def dimension_of(unit: str) -> str:
    """Return the dimension name of ``unit`` or raise :class:`UnitConversionError`."""
    try:
        return _UNITS[unit].dimension
    except KeyError:
        known = ", ".join(sorted(_UNITS))
        raise UnitConversionError(f"Unknown unit {unit!r}. Known units: {known}.") from None


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert ``value`` between two units of the same dimension."""
    src = _UNITS.get(from_unit)
    dst = _UNITS.get(to_unit)
    if src is None:
        dimension_of(from_unit)  # raises with the list of known units
    if dst is None:
        dimension_of(to_unit)
    assert src is not None and dst is not None
    if src.dimension != dst.dimension:
        raise DimensionError(
            f"Cannot convert {from_unit!r} ({src.dimension}) to {to_unit!r} ({dst.dimension})."
        )
    if from_unit == to_unit:
        return float(value)
    return float(value) * (src.num * dst.den) / (src.den * dst.num)


@dataclass(frozen=True)
class Quantity:
    """A finite number with an explicit unit. The stored value is never rounded."""

    value: float
    unit: str

    def __post_init__(self) -> None:
        dimension_of(self.unit)
        if isinstance(self.value, bool) or not isinstance(self.value, Real):
            raise InvalidParameterError(
                f"Quantity value must be a real number, got {type(self.value).__name__}."
            )
        number = float(self.value)
        if not math.isfinite(number):
            raise InvalidParameterError(f"Quantity value must be finite, got {self.value!r}.")
        object.__setattr__(self, "value", number)

    @property
    def dimension(self) -> str:
        return dimension_of(self.unit)

    def to(self, unit: str) -> Quantity:
        """Return the same quantity expressed in ``unit``."""
        return Quantity(convert(self.value, self.unit, unit), unit)

    def __str__(self) -> str:
        return f"{self.value!r} {self.unit}"


def as_quantity(
    name: str,
    raw: Quantity | float | int,
    *,
    default_unit: str,
    allowed_units: tuple[str, ...],
) -> Quantity:
    """Normalise a user input to a :class:`Quantity`.

    A bare number is interpreted in ``default_unit`` (documented per model).
    A :class:`Quantity` must use one of ``allowed_units``.
    """
    if isinstance(raw, Quantity):
        quantity = raw
    else:
        try:
            quantity = Quantity(raw, default_unit)
        except InvalidParameterError as exc:
            raise InvalidParameterError(f"{name}: {exc}") from None
    if quantity.unit not in allowed_units:
        raise DimensionError(
            f"{name}: unit {quantity.unit!r} is not accepted here. "
            f"Use one of: {', '.join(allowed_units)}."
        )
    return quantity
