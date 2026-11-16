import math
from fractions import Fraction

import pytest

from metallurgypy.core import InvalidParameterError, ModelDomainError, Quantity
from metallurgypy.core.units import convert_exact
from metallurgypy.mass_balance import MassBalance
from metallurgypy.precision import (
    Measurement,
    format_sig,
    format_with_uncertainty,
    monte_carlo,
    one_at_a_time,
    platform_precision,
    propagate_model,
    round_sig,
    sensitivity_coefficients,
)

M = Measurement


# ------------------------------- Measurement ------------------------------- #


def test_standard_uncertainty_conversions():
    assert M(10.0, "t", 0.5).standard_uncertainty == 0.5
    assert M(10.0, "t", 1.0, "expanded", coverage_factor=2.0).standard_uncertainty == 0.5
    assert M(10.0, "t", math.sqrt(3.0), "rectangular").standard_uncertainty == pytest.approx(1.0)
    assert M(10.0, "t", math.sqrt(6.0), "triangular").standard_uncertainty == pytest.approx(1.0)
    assert M(10.0, "t", 1.0).expanded_uncertainty(2.0) == 2.0
    assert M(10.0, "t", 0.5).relative_standard_uncertainty == pytest.approx(0.05)
    assert M(0.0, "t", 0.5).relative_standard_uncertainty is None


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(value=1.0, unit="t", uncertainty=-1.0),
        dict(value=1.0, unit="t", uncertainty=math.nan),
        dict(value=1.0, unit="t", uncertainty=1.0, kind="expanded"),  # k missing
        dict(value=1.0, unit="t", uncertainty=1.0, kind="expanded", coverage_factor=0.0),
        dict(value=1.0, unit="t", uncertainty=1.0, coverage_factor=2.0),  # k without expanded
        dict(value=1.0, unit="t", uncertainty=1.0, kind="other"),  # meaning unknown: refused
        dict(value=math.inf, unit="t"),
        dict(value=1.0, unit="furlong"),
    ],
)
def test_measurement_rejects_invalid_definitions(kwargs):
    with pytest.raises(Exception) as info:
        Measurement(**kwargs)
    assert "Error" in type(info.value).__name__


def test_type_a_from_replicates():
    m = Measurement.from_replicates([10.0, 10.2, 9.8, 10.0], "%")
    assert m.value == pytest.approx(10.0)
    s = math.sqrt((0 + 0.04 + 0.04 + 0) / 3)
    assert m.uncertainty == pytest.approx(s / 2, rel=1e-13)  # s / sqrt(4)
    with pytest.raises(InvalidParameterError):
        Measurement.from_replicates([1.0], "%")


# -------------------------- GUM propagation, exact cases ------------------- #

ONE_PRODUCT = "mass_balance.recovery"


def _inputs(u_mass=0.0, u_grade=0.0, u_rec=0.0):
    return {
        "feed_mass": M(1000.0, "t", u_mass),
        "feed_grade": M(2.5, "%", u_grade),
        "recovery": M(92.0, "%", u_rec),
    }


def test_product_rule_matches_the_analytic_gum_result():
    # metal_recovered = F * g * R  (g and R as fractions). For independent inputs:
    # (u/y)^2 = (uF/F)^2 + (ug/g)^2 + (uR/R)^2
    res = propagate_model(ONE_PRODUCT, _inputs(10.0, 0.05, 1.0))
    out = res["metal_recovered"]
    assert out.value == pytest.approx(23.0, rel=1e-13)
    rel = math.sqrt((10 / 1000) ** 2 + (0.05 / 2.5) ** 2 + (1 / 92) ** 2)
    assert out.standard_uncertainty == pytest.approx(23.0 * rel, rel=1e-6)
    assert sum(out.contributions.values()) == pytest.approx(1.0, rel=1e-9)
    # largest contributor is the grade (2 % relative) , then the mass (1 %) : check ordering
    assert out.contributions["feed_grade"] > out.contributions["feed_mass"] > 0
    # sensitivity of metal_recovered to feed_mass is g*R = 0.025*0.92 (t per t)
    assert out.sensitivities["feed_mass"] == pytest.approx(0.025 * 0.92, rel=1e-7)


def test_sum_closure_remaining_is_exactly_one_minus_r_times_feed():
    # metal_remaining = F g (1 - R): its uncertainty from R alone is F g uR
    res = propagate_model(ONE_PRODUCT, _inputs(u_rec=1.0))
    assert res["metal_remaining"].standard_uncertainty == pytest.approx(
        1000 * 0.025 * 0.01, rel=1e-6
    )
    assert res["metal_feed"].standard_uncertainty == pytest.approx(
        0.0, abs=1e-9
    )  # does not depend on R


def test_exact_inputs_give_zero_uncertainty_and_expanded_uncertainty_scales():
    res = propagate_model(ONE_PRODUCT, _inputs())
    assert all(o.standard_uncertainty == 0.0 for o in res.outputs.values())
    r = propagate_model(ONE_PRODUCT, _inputs(10.0))
    o = r["metal_recovered"]
    assert o.expanded(2.0) == pytest.approx(2 * o.standard_uncertainty)
    assert o.as_measurement().standard_uncertainty == o.standard_uncertainty
    assert o.relative == pytest.approx(0.01, rel=1e-6)


def test_input_kinds_expanded_and_rectangular_are_converted_before_propagation():
    a = propagate_model(
        ONE_PRODUCT,
        {**_inputs(), "feed_mass": M(1000.0, "t", 20.0, "expanded", coverage_factor=2.0)},
    )
    b = propagate_model(ONE_PRODUCT, _inputs(10.0))
    assert a["metal_recovered"].standard_uncertainty == pytest.approx(
        b["metal_recovered"].standard_uncertainty, rel=1e-9
    )


def test_correlation_changes_the_result_as_the_covariance_formula_predicts():
    # y = F * g * R (fractions). With only F and R uncertain and correlation r:
    # u_y^2 = (gR)^2 uF^2 + (F g)^2 uR^2 + 2 r (gR)(F g) uF uR
    uF, uR = 10.0, 0.01
    g, R, F = 0.025, 0.92, 1000.0
    base = lambda r: math.sqrt(  # noqa: E731
        (g * R * uF) ** 2 + (F * g * uR) ** 2 + 2 * r * (g * R) * (F * g) * uF * uR
    )
    inputs = {"feed_mass": M(F, "t", uF), "feed_grade": M(2.5, "%"), "recovery": M(92.0, "%", 1.0)}
    for r in (-0.8, 0.0, 0.5, 1.0):
        res = propagate_model(ONE_PRODUCT, inputs, {("feed_mass", "recovery"): r})
        assert res["metal_recovered"].standard_uncertainty == pytest.approx(base(r), rel=1e-6)
        assert sum(res["metal_recovered"].contributions.values()) == pytest.approx(1.0, rel=1e-9)


def test_invalid_correlations_are_refused():
    inputs = _inputs(1.0, 0.1, 1.0)
    with pytest.raises(InvalidParameterError, match="between -1 and 1"):
        propagate_model(ONE_PRODUCT, inputs, {("feed_mass", "recovery"): 1.5})
    with pytest.raises(InvalidParameterError, match="unknown input"):
        propagate_model(ONE_PRODUCT, inputs, {("feed_mass", "nope"): 0.1})
    with pytest.raises(InvalidParameterError, match="different"):
        propagate_model(ONE_PRODUCT, inputs, {("feed_mass", "feed_mass"): 0.1})
    bad = {
        ("feed_mass", "feed_grade"): 0.9,
        ("feed_grade", "recovery"): 0.9,
        ("feed_mass", "recovery"): -0.9,
    }
    with pytest.raises(InvalidParameterError, match="semi-definite"):
        propagate_model(ONE_PRODUCT, inputs, bad)


def test_missing_and_unknown_inputs():
    with pytest.raises(InvalidParameterError, match="Missing"):
        propagate_model(ONE_PRODUCT, {"feed_mass": M(1.0, "t")})
    with pytest.raises(InvalidParameterError, match="Unknown input"):
        propagate_model(ONE_PRODUCT, {**_inputs(), "x": M(1.0, "t")})


def test_edge_of_domain_uses_a_one_sided_derivative_and_says_so():
    inputs = {
        "feed_mass": M(1000.0, "t"),
        "feed_grade": M(2.5, "%"),
        "recovery": M(100.0, "%", 1.0),
    }
    res = propagate_model(ONE_PRODUCT, inputs)
    assert any("edge of the model domain" in w for w in res.warnings)
    assert res["metal_recovered"].standard_uncertainty == pytest.approx(25.0 * 0.01, rel=1e-5)


def test_large_relative_uncertainty_warns():
    res = propagate_model(ONE_PRODUCT, {**_inputs(), "feed_mass": M(1000.0, "t", 300.0)})
    assert any("may be inaccurate" in w for w in res.warnings)


def test_works_for_every_registered_model_with_nominal_example():
    from metallurgypy.registry import list_models

    for spec in list_models():
        meas = {k: M(q.value, q.unit, abs(q.value) * 1e-3) for k, q in spec.example.items()}
        try:
            res = propagate_model(spec, meas)
        except ModelDomainError:
            continue  # model not differentiable there: refusing is the documented behaviour
        for o in res.outputs.values():
            assert math.isfinite(o.standard_uncertainty) and o.standard_uncertainty >= 0.0, (
                spec.model_id
            )
            assert (
                sum(o.contributions.values()) == pytest.approx(1.0, abs=1e-6)
                or o.standard_uncertainty == 0.0
            )


# ------------------------------- Monte Carlo ------------------------------- #


def test_monte_carlo_agrees_with_gum_for_a_nearly_linear_model():
    meas = _inputs(10.0, 0.05, 1.0)
    gum = propagate_model(ONE_PRODUCT, meas)["metal_recovered"]
    mc = monte_carlo(ONE_PRODUCT, meas, samples=20000, seed=12345)
    out = mc.outputs["metal_recovered"]
    assert out.mean == pytest.approx(gum.value, rel=5e-3)
    assert out.standard_deviation == pytest.approx(gum.standard_uncertainty, rel=0.03)
    assert mc.rejected == 0 and mc.samples == 20000


def test_monte_carlo_is_reproducible_and_respects_correlation():
    meas = {
        "feed_mass": M(1000.0, "t", 10.0),
        "feed_grade": M(2.5, "%"),
        "recovery": M(92.0, "%", 1.0),
    }
    a = monte_carlo(ONE_PRODUCT, meas, samples=2000, seed=1)
    b = monte_carlo(ONE_PRODUCT, meas, samples=2000, seed=1)
    assert a.outputs["metal_recovered"].mean == b.outputs["metal_recovered"].mean
    pos = monte_carlo(ONE_PRODUCT, meas, {("feed_mass", "recovery"): 0.9}, samples=5000, seed=2)
    neg = monte_carlo(ONE_PRODUCT, meas, {("feed_mass", "recovery"): -0.9}, samples=5000, seed=2)
    assert (
        pos.outputs["metal_recovered"].standard_deviation
        > neg.outputs["metal_recovered"].standard_deviation
    )


def test_monte_carlo_reports_rejected_draws_and_validates_arguments():
    meas = {
        "feed_mass": M(1000.0, "t", 10.0),
        "feed_grade": M(2.5, "%"),
        "recovery": M(99.5, "%", 1.0),
    }
    mc = monte_carlo(ONE_PRODUCT, meas, samples=1000, seed=3)
    assert mc.rejected > 0 and any(
        "rejected" in w for w in mc.warnings
    )  # recovery > 100 % is invalid
    with pytest.raises(InvalidParameterError, match="samples"):
        monte_carlo(ONE_PRODUCT, meas, samples=10, seed=1)


# ---------------------------------- sensitivity ---------------------------- #


def test_sensitivity_coefficients_elasticities():
    inputs = {
        "feed_mass": Quantity(1000, "t"),
        "feed_grade": Quantity(2.5, "%"),
        "recovery": Quantity(92, "%"),
    }
    entries = {(e.output, e.input): e for e in sensitivity_coefficients(ONE_PRODUCT, inputs)}
    # metal_recovered is proportional to each input: elasticity 1
    for name in ("feed_mass", "feed_grade", "recovery"):
        assert entries[("metal_recovered", name)].normalised == pytest.approx(1.0, rel=1e-6)
    # metal_remaining ~ (1 - R): elasticity to R is -R/(1-R) = -11.5
    assert entries[("metal_remaining", "recovery")].normalised == pytest.approx(
        -0.92 / 0.08, rel=1e-5
    )
    assert entries[("metal_feed", "recovery")].derivative == pytest.approx(0.0, abs=1e-9)


def test_one_at_a_time_reports_domain_exits_instead_of_hiding_them():
    inputs = {
        "feed_mass": Quantity(1000, "t"),
        "feed_grade": Quantity(2.5, "%"),
        "recovery": Quantity(95, "%"),
    }
    rows = [
        e
        for e in one_at_a_time(ONE_PRODUCT, inputs, 0.1)
        if e.input == "recovery" and e.output == "metal_recovered"
    ]
    assert rows[0].low == pytest.approx(25 * 0.855, rel=1e-12)
    assert rows[0].high is None  # 95 % * 1.1 = 104.5 % is outside the model
    with pytest.raises(InvalidParameterError):
        one_at_a_time(ONE_PRODUCT, inputs, 1.5)


# ------------------------ significant figures and precision ---------------- #


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [
        (123456.0, 3, 123000.0),
        (0.0123456, 2, 0.012),
        (2.5, 1, 3.0),
        (-2.5, 1, -3.0),
        (0.0, 3, 0.0),
        (9.999, 2, 10.0),
    ],
)
def test_round_sig(value, digits, expected):
    assert round_sig(value, digits) == expected


@pytest.mark.parametrize(
    ("value", "digits", "text"),
    [(0.025, 3, "0.0250"), (23.0, 4, "23.00"), (123456.0, 3, "123000"), (1 / 3, 6, "0.333333")],
)
def test_format_sig(value, digits, text):
    assert format_sig(value, digits) == text


def test_format_with_uncertainty_gum_style():
    assert format_with_uncertainty(23.0012, 0.1234) == "23.00(12)"
    assert format_with_uncertainty(23.0012, 0.1234, 1) == "23.0(1)"
    assert format_with_uncertainty(1234.5, 0.0, 2) == "1234.5"
    assert format_with_uncertainty(1234.0, 56.0, 2) == "1234 +/- 56"
    for bad in (math.nan, math.inf):
        with pytest.raises(InvalidParameterError):
            round_sig(bad, 3)


def test_rounding_is_presentation_only():
    r = MassBalance(1, 1 / 3, 1 / 7).calculate()
    format_sig(r.metal_feed.value, 3)
    assert r.metal_feed.value == 1 / 3  # untouched


def test_platform_precision_reports_facts():
    p = platform_precision()
    assert p.float64_mantissa_bits == 53 and p.float64_epsilon == 2.0**-52
    assert isinstance(p.note, str) and p.note


# --------------------------------- high precision -------------------------- #


def test_high_precision_is_exact_then_rounded_once():
    mass, grade, rec = 1000.0, 0.025, 0.92
    exact_feed = Fraction(mass) * Fraction(grade)
    r = MassBalance(mass, grade, rec, mode="high_precision").calculate()
    assert r.metal_feed.value == float(exact_feed)
    assert r.metal_recovered.value == float(Fraction(rec) * exact_feed)
    assert r.metal_remaining.value == float(exact_feed - Fraction(rec) * exact_feed)
    assert r.provenance.calculation_mode == "high_precision" and "Fraction" in r.provenance.method
    std = MassBalance(mass, grade, rec).calculate()
    ulp = math.ulp(std.metal_recovered.value)
    assert abs(std.metal_recovered.value - r.metal_recovered.value) <= 2 * ulp


def test_high_precision_unit_conversion_is_exact():
    assert convert_exact(2.5, "%", "fraction") == Fraction(2.5) / 100
    assert convert_exact(1.0, "t", "kg") == 1000
    with pytest.raises(Exception, match="offset"):
        convert_exact(25.0, "degC", "K")
    r = MassBalance(
        Quantity(1000, "t"), Quantity(2.5, "%"), Quantity(92, "%"), mode="high_precision"
    ).calculate()
    assert r.metal_recovered.value == pytest.approx(23.0, rel=1e-15)
