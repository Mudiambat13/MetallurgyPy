"""Reference cases for the process modules.

Every expected value is derived by hand or from an independent closed form in the
comment next to it. None is plant data.
"""

import math

import pytest

from metallurgypy.core import (
    ConvergenceError,
    DimensionError,
    InvalidParameterError,
    ModelDomainError,
    Quantity,
)
from metallurgypy.core.constants import (
    AVOGADRO,
    BOLTZMANN,
    ELEMENTARY_CHARGE,
    FARADAY,
    GAS_CONSTANT,
)
from metallurgypy.core.numerics import bisect
from metallurgypy.electrowinning import Electrowinning
from metallurgypy.filtration import CakeMoisture, ConstantPressureFiltration
from metallurgypy.flotation import FlotationBalance, FlotationKinetics
from metallurgypy.hydrometallurgy import (
    LeachingYield,
    LeachKinetics,
    Neutralization,
    PrecipitationYield,
)
from metallurgypy.reagents import ConcentrationConversion, Dilution, ReagentConsumption
from metallurgypy.registry import list_models
from metallurgypy.solvent_extraction import (
    CountercurrentExtraction,
    McCabeThieleAnalysis,
    SingleStageExtraction,
    StagesRequired,
    StrippingStage,
)
from metallurgypy.thermodynamics import GibbsReaction, StrongAcidPH, WeakAcidPH

Q = Quantity


def val(result, name):
    return result.get(name).value


# ------------------------------- constants --------------------------------- #


def test_constants_are_the_exact_si_values_and_derived_ones_match_codata_digits():
    assert (AVOGADRO, ELEMENTARY_CHARGE, BOLTZMANN) == (
        6.02214076e23,
        1.602176634e-19,
        1.380649e-23,
    )
    assert pytest.approx(96485.33212, rel=1e-10) == FARADAY
    assert pytest.approx(8.314462618, rel=1e-10) == GAS_CONSTANT


# ------------------------------- numerics ---------------------------------- #


def test_bisect_finds_sqrt2_and_reports_status():
    r = bisect(lambda x: x * x - 2.0, 0.0, 2.0)
    assert r.root == pytest.approx(math.sqrt(2.0), rel=1e-13)
    assert "converged" in r.status()


def test_bisect_errors():
    with pytest.raises(InvalidParameterError, match="sign change"):
        bisect(lambda x: x * x + 1.0, -1.0, 1.0)
    with pytest.raises(ConvergenceError):
        bisect(lambda x: x - 0.3, -1.0, 3.0, rel_tol=0.0, max_iter=5)  # root never hit exactly


# -------------------------------- reagents --------------------------------- #


def test_dilution_reference():
    # 100 g/L -> 10 g/L, 50 L : V1 = 50*10/100 = 5 L, diluent 45 L, factor 10, solute 0.5 kg
    r = Dilution(Q(100, "g/L"), Q(10, "g/L"), Q(50, "L")).calculate()
    assert val(r, "stock_volume") == pytest.approx(5.0, rel=1e-14)
    assert val(r, "diluent_volume") == pytest.approx(45.0, rel=1e-14)
    assert val(r, "dilution_factor") == pytest.approx(10.0, rel=1e-14)
    assert val(r, "solute_mass") == pytest.approx(0.5, rel=1e-14)
    assert r.get("stock_volume").unit == "L"


def test_dilution_units_equivalent_and_domain():
    a = Dilution(Q(100, "g/L"), Q(10, "g/L"), Q(50, "L")).calculate()
    b = Dilution(Q(100_000, "mg/L"), Q(10, "kg/m3"), Q(0.05, "m3")).calculate()
    assert val(b, "stock_volume") == pytest.approx(0.005, rel=1e-12)  # m3
    assert val(b, "solute_mass") == pytest.approx(val(a, "solute_mass"), rel=1e-12)
    with pytest.raises(ModelDomainError, match="higher than the stock"):
        Dilution(10, 20, 5).calculate()
    assert Dilution(10, 10, 5).calculate().warnings


def test_concentration_conversion():
    # 40 g/L of a 40 g/mol species = 1 mol/L ; 98 g/L at 98 g/mol = 1 mol/L
    assert val(ConcentrationConversion(40, 40).calculate(), "molar_concentration") == pytest.approx(
        1.0
    )
    r = ConcentrationConversion(Q(49_000, "mg/L"), Q(98, "g/mol")).calculate()
    assert val(r, "molar_concentration") == pytest.approx(0.5, rel=1e-14)


def test_reagent_consumption_reference():
    # 100 t/h, 2 kg/t active, purity 95 %, 20 h/day, 30 days
    r = ReagentConsumption(
        Q(100, "t/h"), Q(2, "kg/t"), Q(95, "%"), Q(20, "h"), Q(30, "d")
    ).calculate()
    assert val(r, "active_per_hour") == pytest.approx(200.0)  # 2 kg/t * 100 t/h
    assert val(r, "product_per_hour") == pytest.approx(200.0 / 0.95)
    assert val(r, "product_per_day") == pytest.approx(200.0 / 0.95 * 20)
    assert val(r, "product_per_campaign") == pytest.approx(200.0 / 0.95 * 20 * 30 / 1000.0)  # t
    assert val(r, "ore_per_campaign") == pytest.approx(100 * 20 * 30)
    assert val(r, "specific_consumption") == pytest.approx(2.0 / 0.95)


def test_reagent_consumption_dosage_units_and_errors():
    g = ReagentConsumption(Q(50, "t/h"), Q(500, "g/t"), 1.0, 24, 1).calculate()
    kg = ReagentConsumption(Q(50, "t/h"), Q(0.5, "kg/t"), 1.0, 24, 1).calculate()
    assert val(g, "active_per_hour") == pytest.approx(val(kg, "active_per_hour"), rel=1e-14)
    with pytest.raises(InvalidParameterError, match="24"):
        ReagentConsumption(10, 1, 1, 25, 1)
    with pytest.raises(InvalidParameterError, match="purity"):
        ReagentConsumption(10, 1, 0.0, 10, 1)
    with pytest.raises(DimensionError):
        ReagentConsumption(Q(10, "kg"), 1, 1, 10, 1)


# ------------------------------ electrowinning ----------------------------- #


def test_electrowinning_faraday_reference():
    # m = I t M / (n F) with I=10 000 A, t=24 h, M=63.5 g/mol, n=2
    expected = 10_000 * 86_400 * 0.0635 / (2 * AVOGADRO * ELEMENTARY_CHARGE)
    r = Electrowinning(Q(10, "kA"), Q(24, "h"), 63.5, 2, Q(90, "%"), 2.0, 40.0).calculate()
    assert val(r, "theoretical_mass") == pytest.approx(expected, rel=1e-13)
    assert val(r, "actual_mass") == pytest.approx(0.9 * expected, rel=1e-13)
    assert val(r, "current_density") == pytest.approx(250.0)  # 10 000 A / 40 m2
    assert val(r, "energy") == pytest.approx(2.0 * 10_000 * 24 / 1000.0)  # 480 kWh
    assert val(r, "specific_energy") == pytest.approx(480.0 / (0.9 * expected / 1000.0), rel=1e-13)
    assert val(r, "production_rate") == pytest.approx(0.9 * expected / 24.0, rel=1e-13)
    assert r.chart_data().values[2] == pytest.approx(0.1 * expected, rel=1e-12)


def test_electrowinning_edges_and_errors():
    # mass is proportional to current and to duration
    one = val(Electrowinning(100, 1, 63.5, 2, 1.0, 2, 1).calculate(), "theoretical_mass")
    two = val(Electrowinning(200, 3, 63.5, 2, 1.0, 2, 1).calculate(), "theoretical_mass")
    assert two == pytest.approx(6 * one, rel=1e-13)
    assert Electrowinning(100, 1, 63.5, 2.5, 1.0, 2, 1).calculate().warnings
    with pytest.raises(InvalidParameterError, match="current_efficiency"):
        Electrowinning(100, 1, 63.5, 2, 1.2, 2, 1)
    with pytest.raises(InvalidParameterError, match="current_efficiency"):
        Electrowinning(100, 1, 63.5, 2, 0.0, 2, 1)
    with pytest.raises(InvalidParameterError, match="current"):
        Electrowinning(-1, 1, 63.5, 2, 0.9, 2, 1)


# --------------------------------- flotation ------------------------------- #


def test_flotation_balance_is_the_two_product_balance_with_its_own_id():
    r = FlotationBalance(100, 0.10, 0.50, 0.02).calculate()
    assert r.provenance.model_id == "flotation.balance"
    assert val(r, "recovery") == pytest.approx(5 / 6, rel=1e-14)


def test_flotation_kinetics_reference():
    # R = 0.9 * (1 - exp(-0.5*8)) ; t95 = ln(20)/0.5
    r = FlotationKinetics(Q(90, "%"), Q(0.5, "1/min"), Q(8, "min")).calculate()
    assert val(r, "recovery") == pytest.approx(0.9 * (1 - math.exp(-4.0)), rel=1e-14)
    assert val(r, "time_95") == pytest.approx(math.log(20) / 0.5, rel=1e-14)
    chart = r.chart_data()
    assert chart.kind == "line" and chart.x[0] == 0.0 and chart.values[0] == 0.0
    assert chart.values[-1] == pytest.approx(val(r, "recovery"), rel=1e-14)
    assert all(b >= a for a, b in zip(chart.values, chart.values[1:], strict=False))  # monotonic
    # at t95 the recovery is exactly 95 % of the plateau
    t95 = val(r, "time_95")
    at95 = FlotationKinetics(0.9, 0.5, t95).calculate()
    assert val(at95, "recovery") == pytest.approx(0.95 * 0.9, rel=1e-13)


def test_flotation_kinetics_k_in_other_units_and_errors():
    a = FlotationKinetics(0.9, Q(30, "1/h"), Q(8, "min")).calculate()  # 30 /h = 0.5 /min
    assert val(a, "recovery") == pytest.approx(0.9 * (1 - math.exp(-4.0)), rel=1e-13)
    with pytest.raises(InvalidParameterError):
        FlotationKinetics(1.5, 0.5, 8)
    with pytest.raises(InvalidParameterError):
        FlotationKinetics(0.0, 0.5, 8)


# --------------------------------- filtration ------------------------------ #


def test_constant_pressure_filtration_reference():
    # K = mu*alpha*c/(A^2 dP) = 1e-3*1e11*50/(100*3e5) = 500/3 ; B = mu*Rm/(A dP) = 10/3
    # t = K V^2/2 + B V with V=5 m3 -> 2100 s = 35 min ; rate_end = 1/(K V + B)
    r = ConstantPressureFiltration(
        Q(1, "mPa.s"), 1e11, 50, 1e10, 10, Q(300, "kPa"), Q(5, "m3")
    ).calculate()
    k, b = 500.0 / 3.0, 10.0 / 3.0
    assert val(r, "filtration_time") == pytest.approx((k * 25 / 2 + b * 5) / 60.0, rel=1e-13)
    assert val(r, "filtration_time") == pytest.approx(35.0, rel=1e-13)
    assert val(r, "final_rate") == pytest.approx(3600.0 / (k * 5 + b), rel=1e-13)
    assert val(r, "dry_cake_mass") == pytest.approx(250.0)
    assert val(r, "average_rate") == pytest.approx(5.0 / 2100.0 * 3600.0, rel=1e-13)
    assert r.chart_data().kind == "line"


def test_filtration_scaling_laws():
    base = ConstantPressureFiltration(1e-3, 1e11, 50, 0.0, 10, 3e5, 5)
    # with no medium resistance, t ~ V^2 : doubling V multiplies t by 4
    t1 = val(base.calculate(), "filtration_time")
    t2 = val(
        ConstantPressureFiltration(1e-3, 1e11, 50, 0.0, 10, 3e5, 10).calculate(), "filtration_time"
    )
    assert t2 == pytest.approx(4 * t1, rel=1e-12)
    # t ~ 1/dP and ~ 1/A^2 for the cake term
    t_dp = val(
        ConstantPressureFiltration(1e-3, 1e11, 50, 0.0, 10, 6e5, 5).calculate(), "filtration_time"
    )
    assert t_dp == pytest.approx(t1 / 2, rel=1e-12)
    t_a = val(
        ConstantPressureFiltration(1e-3, 1e11, 50, 0.0, 20, 3e5, 5).calculate(), "filtration_time"
    )
    assert t_a == pytest.approx(t1 / 4, rel=1e-12)


def test_cake_moisture():
    r = CakeMoisture(100, 80).calculate()
    assert val(r, "moisture_wet_basis") == pytest.approx(0.2)
    assert val(r, "moisture_dry_basis") == pytest.approx(0.25)
    assert val(r, "water_mass") == pytest.approx(20.0)
    assert CakeMoisture(100, 100).calculate().warnings
    with pytest.raises(ModelDomainError, match="exceeds"):
        CakeMoisture(80, 100).calculate()


# ------------------------------ hydrometallurgy ---------------------------- #


def test_leaching_yield_reference():
    # feed 100 t @ 2 % = 2000 kg ; residue 92 t @ 0.5 % = 460 kg ; dissolved 1540 kg -> 77 %
    # solution 300 m3 * 5 kg/m3 = 1500 kg ; gap 40 kg
    r = LeachingYield(100, Q(2, "%"), 92, Q(0.5, "%"), 300, Q(5, "g/L")).calculate()
    assert val(r, "extraction_solids") == pytest.approx(0.77, rel=1e-13)
    assert val(r, "metal_solution") == pytest.approx(1500.0)
    assert val(r, "reconciliation_gap") == pytest.approx(40.0, rel=1e-12)
    assert r.warnings == ()


def test_leaching_yield_warnings_and_domain():
    assert LeachingYield(100, 0.02, 92, 0.03, 1, 1).calculate().warnings  # negative extraction
    assert any(
        "solution exceeds" in w
        for w in LeachingYield(100, 0.02, 92, 0.005, 1000, 50).calculate().warnings
    )
    with pytest.raises(ModelDomainError):
        LeachingYield(100, 0.0, 92, 0.0, 1, 1).calculate()


def test_leach_kinetics_reference():
    r = LeachKinetics(Q(95, "%"), Q(0.3, "1/h"), Q(12, "h")).calculate()
    assert val(r, "extraction") == pytest.approx(0.95 * (1 - math.exp(-3.6)), rel=1e-14)
    assert val(r, "time_90") == pytest.approx(math.log(10) / 0.3, rel=1e-14)


def test_neutralization_reference():
    # 100 m3 * 0.1 mol/L = 10 000 mol H+ ; z=2 -> 5 000 mol ; M=56 g/mol -> 280 kg pure ; /0.9 -> 311.11 kg
    r = Neutralization(100, Q(0.1, "mol/L"), 56, 2, Q(90, "%")).calculate()
    assert val(r, "acid_amount") == pytest.approx(10_000.0)
    assert val(r, "base_amount") == pytest.approx(5_000.0)
    assert val(r, "base_mass_pure") == pytest.approx(280.0)
    assert val(r, "base_mass_commercial") == pytest.approx(280.0 / 0.9, rel=1e-14)
    assert r.warnings  # stoichiometric-minimum warning is always present


def test_precipitation_yield():
    r = PrecipitationYield(50, Q(4, "g/L"), Q(0.2, "g/L")).calculate()
    assert val(r, "precipitated_mass") == pytest.approx(190.0)
    assert val(r, "yield") == pytest.approx(0.95)
    assert val(r, "residual_mass") == pytest.approx(10.0)
    with pytest.raises(ModelDomainError, match="re-dissolution"):
        PrecipitationYield(50, 1, 2).calculate()


# --------------------------- solvent extraction ---------------------------- #


def test_single_stage_extraction_reference_and_balance():
    # D=4, r=1, C0=5 -> Caq = 1, Corg = 4, extraction 0.8
    r = SingleStageExtraction(5, 4, 1).calculate()
    assert val(r, "raffinate_concentration") == pytest.approx(1.0)
    assert val(r, "loaded_organic_concentration") == pytest.approx(4.0)
    assert val(r, "extraction") == pytest.approx(0.8)
    assert abs(val(r, "balance_residual")) < 1e-12
    # with r = 2 the organic is more dilute: Caq = 5/9, Corg = 20/9, extraction 8/9
    r2 = SingleStageExtraction(5, 4, 2).calculate()
    assert val(r2, "extraction") == pytest.approx(8 / 9, rel=1e-14)
    assert val(r2, "ao_ratio") == pytest.approx(0.5)


def test_stripping_reference():
    # y0=4, D=0.05, A/O=0.25, x_in=30: x=(4+7.5)/0.3=38.333.., y=1.91666.., stripped=(4-y)/4
    r = StrippingStage(4, 0.05, 0.25, 30).calculate()
    assert val(r, "strip_liquor_concentration") == pytest.approx(115 / 3, rel=1e-13)
    assert val(r, "stripped_organic_concentration") == pytest.approx(0.05 * 115 / 3, rel=1e-13)
    assert abs(val(r, "balance_residual")) < 1e-12


def test_kremser_reference_and_limits():
    # E=2, N=3 : phi = 1/(2^4-1) = 1/15
    r = CountercurrentExtraction(5, 2, 1, 3).calculate()
    assert val(r, "raffinate_concentration") == pytest.approx(5 / 15, rel=1e-14)
    assert val(r, "extraction") == pytest.approx(14 / 15, rel=1e-14)
    assert val(r, "loaded_organic_concentration") == pytest.approx(5 * 14 / 15, rel=1e-14)
    # E = 1: phi = 1/(N+1)
    assert val(CountercurrentExtraction(5, 1, 1, 4).calculate(), "extraction") == pytest.approx(
        1 - 1 / 5
    )
    # one stage must equal the single-stage result
    one = CountercurrentExtraction(5, 4, 1, 1).calculate()
    single = SingleStageExtraction(5, 4, 1).calculate()
    assert val(one, "extraction") == pytest.approx(val(single, "extraction"), rel=1e-13)
    # E < 1 is limited to 1 - E even with many stages
    many = CountercurrentExtraction(5, 0.5, 1, 1000).calculate()
    assert val(many, "extraction") == pytest.approx(0.5, rel=1e-9) and many.warnings
    # a huge extraction factor must not overflow
    assert val(
        CountercurrentExtraction(5, 1e6, 1, 1000).calculate(), "extraction"
    ) == pytest.approx(1.0)
    with pytest.raises(InvalidParameterError, match="whole number"):
        CountercurrentExtraction(5, 2, 1, 2.5)


def test_stages_required_is_the_inverse_of_kremser():
    r = StagesRequired(2, 1, Q(99, "%")).calculate()
    n = val(r, "theoretical_stages")
    assert n == pytest.approx(math.log(101) / math.log(2) - 1, rel=1e-13)
    assert val(r, "stages_ceiling") == 6.0
    from metallurgypy.solvent_extraction.models import _unextracted_fraction

    assert _unextracted_fraction(2.0, n) == pytest.approx(0.01, rel=1e-12)
    assert val(StagesRequired(1, 1, Q(80, "%")).calculate(), "theoretical_stages") == pytest.approx(
        4.0
    )  # 1/0.2-1
    with pytest.raises(ModelDomainError, match="Unreachable"):
        StagesRequired(0.5, 1, Q(60, "%")).calculate()  # max extraction is 50 %


def test_mccabe_thiele_matches_kremser_for_a_linear_isotherm():
    d, feed, raff, ao = 2.0, 5.0, 0.05, 1.0  # E = D*O/A = 2
    xs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    ys = [d * x for x in xs]
    result = McCabeThieleAnalysis(xs, ys, feed=feed, raffinate=raff, ao_ratio=ao).run()
    phi = raff / feed  # 0.01 -> 99 % extraction
    expected = math.log(1 + (2 - 1) / phi) / math.log(2) - 1  # Kremser, 5.658
    assert result.stages == pytest.approx(
        expected, rel=0.08
    )  # stepping prorates the last stage linearly
    assert 5.0 < result.stages < 6.0
    assert result.loaded_organic == pytest.approx(d * (feed - 0) * 0 + result.stage_points[0][1])


def test_mccabe_thiele_errors():
    xs, ys = (
        [0.0, 1.0, 2.0, 4.0],
        [0.0, 0.5, 1.0, 2.0],
    )  # D = 0.5 : extraction factor < 1 at A/O = 1
    with pytest.raises(ConvergenceError, match="pinch"):
        McCabeThieleAnalysis(xs, ys, feed=2.0, raffinate=0.05, ao_ratio=1.0).run()
    with pytest.raises(ModelDomainError, match="extrapolation"):
        McCabeThieleAnalysis([0, 1, 2], [0, 1, 2], feed=5.0, raffinate=0.1, ao_ratio=1.0).run()
    with pytest.raises(InvalidParameterError, match="increasing"):
        McCabeThieleAnalysis([0, 1, 1], [0, 1, 2], feed=1.0, raffinate=0.1, ao_ratio=1.0)
    with pytest.raises(InvalidParameterError):
        McCabeThieleAnalysis([0, 1], [0, 1], feed=1.0, raffinate=1.0, ao_ratio=1.0)


# ------------------------------ thermodynamics ----------------------------- #


def test_gibbs_reference():
    # dG = -50000 - 298.15*(-100) = -20185 J/mol ; ln K = 20185/(R*298.15)
    r = GibbsReaction(Q(-50, "kJ/mol"), Q(-100, "J/(mol.K)"), Q(25, "degC")).calculate()
    assert val(r, "delta_g") == pytest.approx(-20.185, rel=1e-13)
    assert val(r, "ln_k") == pytest.approx(20185.0 / (GAS_CONSTANT * 298.15), rel=1e-13)
    assert val(r, "k") == pytest.approx(math.exp(val(r, "ln_k")), rel=1e-13)
    assert val(r, "log10_k") == pytest.approx(val(r, "ln_k") / math.log(10), rel=1e-13)
    same = GibbsReaction(Q(-50, "kJ/mol"), Q(-100, "J/(mol.K)"), Q(298.15, "K")).calculate()
    assert val(same, "delta_g") == pytest.approx(val(r, "delta_g"), rel=1e-13)


def test_gibbs_edges():
    at_equilibrium = GibbsReaction(10, 0.0, 300).calculate()  # unit defaults: kJ/mol, J/(mol K), K
    assert val(at_equilibrium, "delta_g") == pytest.approx(10.0)
    zero = GibbsReaction(Q(30, "kJ/mol"), Q(100, "J/(mol.K)"), Q(300, "K")).calculate()
    assert val(zero, "delta_g") == pytest.approx(0.0, abs=1e-12) and val(
        zero, "k"
    ) == pytest.approx(1.0)
    huge = GibbsReaction(Q(-2000, "kJ/mol"), 0.0, 300).calculate()
    assert "k" not in {o.name for o in huge.outputs()} and huge.warnings
    with pytest.raises(InvalidParameterError, match="absolute zero"):
        GibbsReaction(1, 1, Q(-300, "degC"))


def test_strong_acid_ph():
    assert val(StrongAcidPH(0.01, 1).calculate(), "ph") == pytest.approx(2.0, abs=1e-14)
    assert val(StrongAcidPH(0.005, 2).calculate(), "ph") == pytest.approx(2.0, abs=1e-14)
    with pytest.raises(ModelDomainError, match="too dilute"):
        StrongAcidPH(1e-8, 1).calculate()
    assert StrongAcidPH(1.0, 1).calculate().warnings


def test_weak_acid_ph_solves_the_charge_balance():
    r = WeakAcidPH(Q(0.1, "mol/L"), 4.76, 14.0).calculate()
    h = val(r, "hydrogen_concentration")
    ka, kw, c = 10**-4.76, 1e-14, 0.1
    assert h - c * ka / (ka + h) - kw / h == pytest.approx(
        0.0, abs=1e-15
    )  # residual of the equation
    assert val(r, "ph") == pytest.approx(-math.log10(h), rel=1e-14)
    assert val(r, "ph") == pytest.approx(2.8829, abs=1e-3)  # approx. sqrt(Ka C) solution
    assert val(r, "dissociation_fraction") == pytest.approx(ka / (ka + h), rel=1e-13)
    assert "converged" in r.provenance.convergence


def test_weak_acid_limits():
    # very weak and dilute: pH tends to 7 (water autoionization dominates)
    r = WeakAcidPH(1e-9, 9.0, 14.0).calculate()
    assert val(r, "ph") == pytest.approx(7.0, abs=0.01)
    # strong-acid limit: pKa very negative behaves like complete dissociation
    r = WeakAcidPH(0.01, -6.0, 14.0).calculate()
    assert val(r, "ph") == pytest.approx(2.0, abs=1e-4)


# --------------------------------- registry -------------------------------- #


def test_every_registered_model_example_runs_and_is_traceable():
    specs = list_models()
    assert len(specs) == 21
    assert {s.module_key for s in specs} == {
        "mass_balance",
        "reagents",
        "electrowinning",
        "flotation",
        "filtration",
        "hydrometallurgy",
        "solvent_extraction",
        "thermodynamics",
    }
    for spec in specs:
        result = spec.run(spec.example)
        p = result.provenance
        assert p.model_id == spec.model_id and p.model_version == spec.model_version
        assert p.equations and p.assumptions, spec.model_id
        assert all(math.isfinite(o.quantity.value) for o in result.outputs()), spec.model_id
        assert {q for q in p.inputs} == {x.name for x in spec.parameters}


@pytest.mark.parametrize("spec", list_models(), ids=lambda s: s.model_id)
def test_missing_or_bad_inputs_are_rejected_by_every_model(spec):
    from metallurgypy.core.units import dimension_of

    inputs = dict(spec.example)
    first = spec.parameters[0].name
    own = dimension_of(spec.example[first].unit)
    bad_unit = next(u for u in ("kg", "s", "A", "V") if dimension_of(u) != own)
    with pytest.raises((DimensionError, InvalidParameterError)):
        spec.run({**inputs, first: Quantity(1.0, bad_unit)})
    del inputs[first]
    with pytest.raises(InvalidParameterError, match="Missing"):
        spec.run(inputs)
