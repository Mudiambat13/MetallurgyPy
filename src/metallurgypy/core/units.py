"""Explicit, dependency-free unit handling.

Every unit belongs to one *dimension* (a name such as ``mass`` or ``time``) and
is defined by an exact ratio to the base unit of that dimension. Converting
between dimensions is an error (:class:`DimensionError`). Temperature has an
offset (degC) and is the only affine unit.

Dimensions and base units
-------------------------
=================  ==========================  =====================================
dimension          units                       base
=================  ==========================  =====================================
mass               g kg t kt Mt                kg
time               s min h d                   s
volume             mL L m3                     m3
area               cm2 m2                      m2
dimensionless      fraction % ppm g/t kg/t     fraction
                   ratio                       (``ratio`` = plain number, can exceed 1)
amount             mol kmol                    mol
molar_mass         g/mol kg/kmol               g/mol
mass_conc          mg/L g/m3 g/L kg/m3         kg/m3
molar_conc         mol/m3 mol/L                mol/m3
current            A kA                        A
current_density    A/m2 mA/cm2 A/cm2           A/m2
voltage            V                           V
energy             J kJ kWh                    J
power              W kW                        W
pressure           Pa kPa bar                  Pa
temperature        K degC                      K
mass_flow          kg/s kg/h t/h t/d           kg/s
volume_flow        m3/s m3/h L/min             m3/s
rate               1/s 1/min 1/h 1/d           1/s
viscosity          Pa.s mPa.s                  Pa.s
cake_resistance    m/kg                        m/kg   (specific cake resistance)
medium_resistance  1/m 1/cm                    1/m
molar_energy       J/mol kJ/mol                J/mol
molar_entropy      J/(mol.K) kJ/(mol.K)        J/(mol.K)
specific_energy    kWh/t kWh/kg                kWh/t
=================  ==========================  =====================================

``ppm`` and ``g/t`` are by mass (1e-6); ``kg/t`` is 1e-3. A reagent dosage in
kg/t is therefore a plain mass ratio. All factors are exact definitions.

A general engine such as Pint may replace this module later; the public
functions (:func:`convert`, :class:`Quantity`) are the stable surface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from numbers import Real

from metallurgypy.core.exceptions import (
    DimensionError,
    InvalidParameterError,
    UnitConversionError,
)

MASS = "mass"
DIMENSIONLESS = "dimensionless"
KELVIN_OFFSET = 273.15  # exact by definition of the Celsius scale


@dataclass(frozen=True)
class _UnitDef:
    dimension: str
    num: int  # base_value = value * num / den + offset
    den: int
    offset: float = 0.0


def _u(dim: str, **units: tuple[int, int]) -> dict[str, _UnitDef]:
    return {name: _UnitDef(dim, n, d) for name, (n, d) in units.items()}


_UNITS: dict[str, _UnitDef] = {}
for _group in (
    _u("mass", g=(1, 1000), kg=(1, 1), t=(1000, 1), kt=(10**6, 1), Mt=(10**9, 1)),
    _u("time", s=(1, 1), min=(60, 1), h=(3600, 1), d=(86400, 1)),
    _u("volume", mL=(1, 10**6), L=(1, 1000), m3=(1, 1)),
    _u("area", cm2=(1, 10**4), m2=(1, 1)),
    _u(
        "dimensionless",
        fraction=(1, 1),
        ratio=(1, 1),
    ),
    _u("amount", mol=(1, 1), kmol=(1000, 1)),
    _u("molar_mass", **{"g/mol": (1, 1), "kg/kmol": (1, 1)}),
    _u("mass_conc", **{"mg/L": (1, 1000), "g/m3": (1, 1000), "g/L": (1, 1), "kg/m3": (1, 1)}),
    _u("molar_conc", **{"mol/m3": (1, 1), "mol/L": (1000, 1)}),
    _u("current", A=(1, 1), kA=(1000, 1)),
    _u("current_density", **{"A/m2": (1, 1), "mA/cm2": (10, 1), "A/cm2": (10**4, 1)}),
    _u("voltage", V=(1, 1)),
    _u("energy", J=(1, 1), kJ=(1000, 1), kWh=(3_600_000, 1)),
    _u("power", W=(1, 1), kW=(1000, 1)),
    _u("pressure", Pa=(1, 1), kPa=(1000, 1), bar=(100_000, 1)),
    _u(
        "mass_flow",
        **{"kg/s": (1, 1), "kg/h": (1, 3600), "t/h": (1000, 3600), "t/d": (1000, 86400)},
    ),
    _u("volume_flow", **{"m3/s": (1, 1), "m3/h": (1, 3600), "L/min": (1, 60000)}),
    _u("rate", **{"1/s": (1, 1), "1/min": (1, 60), "1/h": (1, 3600), "1/d": (1, 86400)}),
    _u("viscosity", **{"Pa.s": (1, 1), "mPa.s": (1, 1000)}),
    _u("cake_resistance", **{"m/kg": (1, 1)}),
    _u("medium_resistance", **{"1/m": (1, 1), "1/cm": (100, 1)}),
    _u("molar_energy", **{"J/mol": (1, 1), "kJ/mol": (1000, 1)}),
    _u("molar_entropy", **{"J/(mol.K)": (1, 1), "kJ/(mol.K)": (1000, 1)}),
    _u("specific_energy", **{"kWh/t": (1, 1), "kWh/kg": (1000, 1)}),
):
    _UNITS.update(_group)
# dimensionless mass ratios (by mass, so only meaningful for mass-basis quantities)
_UNITS.update(
    {
        "%": _UnitDef("dimensionless", 1, 100),
        "ppm": _UnitDef("dimensionless", 1, 1_000_000),
        "g/t": _UnitDef("dimensionless", 1, 1_000_000),
        "kg/t": _UnitDef("dimensionless", 1, 1_000),
        "K": _UnitDef("temperature", 1, 1),
        "degC": _UnitDef("temperature", 1, 1, KELVIN_OFFSET),
    }
)

MASS_UNITS: tuple[str, ...] = ("g", "kg", "t", "kt", "Mt")
GRADE_UNITS: tuple[str, ...] = ("fraction", "%", "ppm", "g/t")
RATIO_UNITS: tuple[str, ...] = ("fraction", "%")


def units_of(dimension: str) -> tuple[str, ...]:
    """All unit symbols of ``dimension``, in definition order."""
    found = tuple(name for name, d in _UNITS.items() if d.dimension == dimension)
    if not found:
        raise UnitConversionError(f"Unknown dimension {dimension!r}.")
    return found


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
    if src.offset == 0.0 and dst.offset == 0.0:
        return float(value) * (src.num * dst.den) / (src.den * dst.num)
    base = float(value) * src.num / src.den + src.offset
    return (base - dst.offset) * dst.den / dst.num


def convert_exact(value: float, from_unit: str, to_unit: str) -> Fraction:
    """Exact rational conversion of the float ``value`` (no rounding at all).

    Used by the ``high_precision`` mode. Affine units (degC) are not supported.
    """
    src, dst = _UNITS.get(from_unit), _UNITS.get(to_unit)
    if src is None:
        dimension_of(from_unit)
    if dst is None:
        dimension_of(to_unit)
    assert src is not None and dst is not None
    if src.dimension != dst.dimension:
        raise DimensionError(
            f"Cannot convert {from_unit!r} ({src.dimension}) to {to_unit!r} ({dst.dimension})."
        )
    if src.offset or dst.offset:
        raise UnitConversionError(
            "Exact conversion is not available for temperature scales with an offset."
        )
    return Fraction(value) * Fraction(src.num * dst.den, src.den * dst.num)


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
