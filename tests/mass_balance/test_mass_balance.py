import math
import random

import pytest

from metallurgypy.core import (
    DimensionError,
    InvalidParameterError,
    ModelDomainError,
    Quantity,
    Tolerances,
)
from metallurgypy.mass_balance import MassBalance, TwoProductBalance

# --------------------------------------------------------------------------- #
# MassBalance: reference cases worked out by hand
# --------------------------------------------------------------------------- #


def test_reference_case_specification_example():
    # 1000 * 0.025 = 25 ; 0.92 * 25 = 23 ; 25 - 23 = 2
    r = MassBalance(feed_mass=1000, feed_grade=0.025, recovery=0.92).calculate()
    assert r.metal_feed == Quantity(25.0, "t")
    assert r.metal_recovered == Quantity(23.0, "t")
    assert r.metal_remaining == Quantity(2.0, "t")
    assert r.recovery == Quantity(0.92, "fraction")
    assert r.loss.value == pytest.approx(0.08, abs=1e-15)
    assert r.warnings == ()


def test_reference_case_half_recovery():
    r = MassBalance(100, 0.10, 0.5).calculate()
    assert (r.metal_feed.value, r.metal_recovered.value, r.metal_remaining.value) == (10.0, 5.0, 5.0)


def test_units_are_honoured_and_equivalent():
    base = MassBalance(1000, 0.025, 0.92).calculate()
    other = MassBalance(
        Quantity(1_000_000, "kg"), Quantity(2.5, "%"), Quantity(92, "%")
    ).calculate()
    assert other.metal_recovered.unit == "kg"
    assert other.metal_recovered.to("t").value == pytest.approx(base.metal_recovered.value, rel=1e-12)
    ppm = MassBalance(1, Quantity(25_000, "g/t"), 1).calculate()
    assert ppm.metal_feed.value == pytest.approx(0.025, rel=1e-12)


def test_edge_cases():
    zero_grade = MassBalance(10, 0.0, 0.5).calculate()
    assert zero_grade.metal_recovered.value == 0.0 and zero_grade.warnings
    full = MassBalance(10, 0.5, 1.0).calculate()
    assert full.metal_remaining.value == 0.0 and full.warnings
    none = MassBalance(10, 0.5, 0.0).calculate()
    assert none.metal_recovered.value == 0.0 and none.metal_remaining.value == 5.0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (dict(feed_mass=0, feed_grade=0.1, recovery=0.5), "feed_mass"),
        (dict(feed_mass=-5, feed_grade=0.1, recovery=0.5), "feed_mass"),
        (dict(feed_mass=10, feed_grade=1.5, recovery=0.5), "feed_grade"),
        (dict(feed_mass=10, feed_grade=-0.1, recovery=0.5), "feed_grade"),
        (dict(feed_mass=10, feed_grade=0.1, recovery=1.2), "recovery"),
        (dict(feed_mass=10, feed_grade=0.1, recovery=Quantity(120, "%")), "recovery"),
        (dict(feed_mass=math.nan, feed_grade=0.1, recovery=0.5), "feed_mass"),
        (dict(feed_mass=10, feed_grade=math.inf, recovery=0.5), "feed_grade"),
    ],
)
def test_invalid_inputs_name_the_offending_parameter(kwargs, message):
    with pytest.raises(InvalidParameterError, match=message):
        MassBalance(**kwargs)


def test_wrong_dimension_is_rejected():
    with pytest.raises(DimensionError):
        MassBalance(Quantity(10, "%"), 0.1, 0.5)
    with pytest.raises(DimensionError):
        MassBalance(10, Quantity(5, "t"), 0.5)
    with pytest.raises(DimensionError, match="recovery"):
        MassBalance(10, 0.1, Quantity(500, "g/t"))  # g/t is a grade unit, not a recovery unit


def test_unsupported_mode_is_refused_not_silently_ignored():
    with pytest.raises(InvalidParameterError, match="not implemented"):
        MassBalance(10, 0.1, 0.5, mode="high_precision")


def test_result_traceability_and_unrounded_values():
    r = MassBalance(1000, 0.025, 0.92, tolerances=Tolerances(rel=1e-10, abs=1e-13)).calculate()
    p = r.provenance
    assert p.model_id == "mass_balance.recovery" and p.model_version == "1.0"
    assert p.equations and p.assumptions
    assert p.tolerances == Tolerances(rel=1e-10, abs=1e-13)
    assert p.calculation_mode == "standard"
    assert p.inputs["feed_grade"] == Quantity(0.025, "fraction")  # bare number: documented default unit
    assert p.software_version and p.timestamp.endswith("+00:00")
    third = MassBalance(1, 1 / 3, 1 / 7).calculate()
    assert third.metal_feed.value == 1 / 3  # no rounding anywhere
    assert r.get("metal_recovered") == r.metal_recovered
    with pytest.raises(KeyError):
        r.get("nope")


def test_chart_data_matches_result():
    r = MassBalance(1000, 0.025, 0.92).calculate()
    chart = r.chart_data()
    assert chart.values == (25.0, 23.0, 2.0)
    assert chart.unit == "t" and "calculated" in chart.source


def test_property_closure_and_bounds_on_random_inputs():
    rng = random.Random(20260101)
    for _ in range(2000):
        mass = 10 ** rng.uniform(-3, 9)
        grade = rng.random()
        rec = rng.random()
        r = MassBalance(mass, grade, rec).calculate()
        assert r.metal_recovered.value + r.metal_remaining.value == pytest.approx(
            r.metal_feed.value, rel=1e-12, abs=0
        )
        assert 0.0 <= r.metal_recovered.value <= r.metal_feed.value <= mass


# --------------------------------------------------------------------------- #
# TwoProductBalance
# --------------------------------------------------------------------------- #


def test_two_product_reference_case():
    # F=100, g=0.10, c=0.50, t=0.02 -> C = 100*0.08/0.48 = 100/6 ; yield 1/6 ; recovery 5/6
    r = TwoProductBalance(100, 0.10, 0.50, 0.02).calculate()
    assert r.concentrate_mass.value == pytest.approx(100 / 6, rel=1e-14)
    assert r.tailings_mass.value == pytest.approx(500 / 6, rel=1e-14)
    assert r.mass_yield.value == pytest.approx(1 / 6, rel=1e-14)
    assert r.recovery.value == pytest.approx(5 / 6, rel=1e-14)
    assert r.enrichment_ratio.unit == "ratio"
    assert r.enrichment_ratio.value == pytest.approx(5.0, rel=1e-14)
    assert r.metal_feed.value == pytest.approx(10.0, rel=1e-14)
    assert r.metal_concentrate.value + r.metal_tailings.value == pytest.approx(10.0, rel=1e-14)
    assert abs(r.mass_closure_residual.value) < 1e-12 and abs(r.metal_closure_residual.value) < 1e-12


def test_recovery_is_not_mass_yield():
    r = TwoProductBalance(100, 0.10, 0.50, 0.02).calculate()
    assert r.recovery.value != pytest.approx(r.mass_yield.value)


def test_two_product_percent_inputs_match_fractions():
    a = TwoProductBalance(100, 0.10, 0.50, 0.02).calculate()
    b = TwoProductBalance(100, Quantity(10, "%"), Quantity(50, "%"), Quantity(2, "%")).calculate()
    assert b.recovery.value == pytest.approx(a.recovery.value, rel=1e-13)


def test_two_product_domain_errors():
    with pytest.raises(ModelDomainError, match="equal"):
        TwoProductBalance(100, 0.1, 0.3, 0.3).calculate()
    with pytest.raises(ModelDomainError, match="between"):
        TwoProductBalance(100, 0.6, 0.5, 0.02).calculate()  # feed richer than concentrate
    with pytest.raises(ModelDomainError, match="between"):
        TwoProductBalance(100, 0.01, 0.5, 0.02).calculate()  # feed poorer than tailings
    with pytest.raises(ModelDomainError, match="zero"):
        TwoProductBalance(100, 0.0, 0.5, 0.0).calculate()


def test_two_product_boundaries_and_warnings():
    all_to_tailings = TwoProductBalance(100, 0.02, 0.5, 0.02).calculate()
    assert all_to_tailings.concentrate_mass.value == 0.0
    assert all_to_tailings.recovery.value == 0.0 and all_to_tailings.warnings
    swapped = TwoProductBalance(100, 0.10, 0.02, 0.50).calculate()
    assert any("which stream" in w for w in swapped.warnings)


def test_two_product_property_on_random_valid_grades():
    rng = random.Random(7)
    for _ in range(2000):
        t = rng.uniform(0.0, 0.2)
        c = rng.uniform(t + 0.01, 1.0)
        g = rng.uniform(t, c)
        if g == 0.0 or c == t:
            continue
        mass = 10 ** rng.uniform(-2, 8)
        r = TwoProductBalance(mass, g, c, t).calculate()
        assert 0.0 <= r.mass_yield.value <= 1.0
        assert -1e-12 <= r.recovery.value <= 1.0 + 1e-12
        assert r.concentrate_mass.value + r.tailings_mass.value == pytest.approx(mass, rel=1e-12)
        assert r.metal_concentrate.value + r.metal_tailings.value == pytest.approx(
            r.metal_feed.value, rel=1e-9, abs=1e-12
        )
