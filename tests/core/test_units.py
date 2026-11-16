import math

import pytest

from metallurgypy.core import (
    DimensionError,
    InvalidParameterError,
    Quantity,
    UnitConversionError,
)
from metallurgypy.core.units import GRADE_UNITS, MASS_UNITS, as_quantity, convert


@pytest.mark.parametrize(
    ("value", "src", "dst", "expected"),
    [
        (1.0, "t", "kg", 1000.0),
        (1000.0, "g", "kg", 1.0),
        (2.5, "kt", "t", 2500.0),
        (1.0, "Mt", "kt", 1000.0),
        (2.5, "%", "fraction", 0.025),
        (1.0, "g/t", "ppm", 1.0),
        (1.0, "ppm", "fraction", 1e-6),
        (0.5, "fraction", "%", 50.0),
        (7.0, "ratio", "fraction", 7.0),
    ],
)
def test_reference_conversions(value, src, dst, expected):
    assert convert(value, src, dst) == pytest.approx(expected, rel=1e-15, abs=0)


def test_same_unit_is_identity_without_rounding():
    x = 0.1 + 0.2
    assert convert(x, "kg", "kg") == x


@pytest.mark.parametrize("unit", MASS_UNITS)
def test_mass_round_trip(unit):
    value = 123.456789
    assert convert(convert(value, unit, "kg"), "kg", unit) == pytest.approx(value, rel=1e-15)


@pytest.mark.parametrize("unit", GRADE_UNITS)
def test_grade_round_trip(unit):
    value = 0.0123456
    back = convert(convert(value, unit, "fraction"), "fraction", unit)
    assert back == pytest.approx(value, rel=1e-15)


def test_dimension_mismatch_is_an_error():
    with pytest.raises(DimensionError):
        convert(1.0, "t", "%")


def test_unknown_unit_lists_known_units():
    with pytest.raises(UnitConversionError, match="Known units"):
        convert(1.0, "furlong", "kg")
    with pytest.raises(UnitConversionError):
        Quantity(1.0, "furlong")


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True, "5", None])
def test_quantity_rejects_non_finite_or_non_numeric(bad):
    with pytest.raises(InvalidParameterError):
        Quantity(bad, "t")


def test_quantity_keeps_unrounded_value_and_converts_int():
    q = Quantity(1, "t")
    assert q.value == 1.0 and isinstance(q.value, float)
    assert Quantity(0.1 + 0.2, "t").value == 0.1 + 0.2
    assert q.dimension == "mass"
    assert q.to("kg") == Quantity(1000.0, "kg")


def test_as_quantity_default_unit_and_allowed_units():
    assert as_quantity("m", 5, default_unit="t", allowed_units=MASS_UNITS) == Quantity(5.0, "t")
    with pytest.raises(DimensionError, match="not accepted"):
        as_quantity("m", Quantity(5, "%"), default_unit="t", allowed_units=MASS_UNITS)
    with pytest.raises(InvalidParameterError, match=r"^m:"):
        as_quantity("m", math.nan, default_unit="t", allowed_units=MASS_UNITS)
