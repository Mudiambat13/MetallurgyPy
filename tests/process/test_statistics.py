import math

import pytest

from metallurgypy.core import CalculationError, InvalidParameterError
from metallurgypy.statistics import (
    correlation,
    describe,
    detect_outliers,
    linear_regression,
    moving_average,
    variability,
)


def test_describe_reference():
    d = describe([2, 4, 4, 4, 5, 5, 7, 9])
    assert d.n == 8 and d.mean == 5.0 and d.median == 4.5
    assert d.std == pytest.approx(math.sqrt(32 / 7), rel=1e-14)  # sample std, sum sq dev = 32
    assert (d.minimum, d.maximum) == (2.0, 9.0)
    assert d.cv == pytest.approx(d.std / 5.0)
    assert d.q1 <= d.median <= d.q3


def test_describe_edges_and_errors():
    one = describe([3.0])
    assert one.std == 0.0 and one.q1 == one.q3 == 3.0
    assert describe([-1.0, 1.0]).cv is None  # zero mean
    for bad in ([], [1.0, math.nan], [1.0, math.inf], [1.0, "a"], [True, 2]):
        with pytest.raises(InvalidParameterError):
            describe(bad)


def test_regression_exact_line_and_noisy_reference():
    r = linear_regression([0, 1, 2, 3], [1, 3, 5, 7])  # y = 1 + 2x
    assert r.slope == pytest.approx(2.0) and r.intercept == pytest.approx(1.0)
    assert r.r_squared == pytest.approx(1.0) and r.slope_stderr == pytest.approx(0.0, abs=1e-12)
    assert r.predict(10) == pytest.approx(21.0)
    # classic textbook set: x=1..5, y=2,4,5,4,5 -> slope 0.6, intercept 2.2, r2 0.6
    t = linear_regression([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
    assert t.slope == pytest.approx(0.6) and t.intercept == pytest.approx(2.2)
    assert t.r_squared == pytest.approx(0.6)
    # slope standard error = sqrt(s2 / Sxx) with s2 = SSres/(n-2) = 2.4/3 ; Sxx = 10
    assert t.slope_stderr == pytest.approx(math.sqrt(0.8 / 10), rel=1e-12)
    assert linear_regression([0, 1], [0, 1]).slope_stderr is None


def test_regression_errors():
    with pytest.raises(CalculationError, match="slope is undefined"):
        linear_regression([1, 1, 1], [1, 2, 3])
    with pytest.raises(InvalidParameterError, match="same length"):
        linear_regression([1, 2, 3], [1, 2])


def test_correlation():
    assert correlation([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert correlation([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)
    with pytest.raises(CalculationError):
        correlation([1, 1, 1], [1, 2, 3])


def test_outliers_modified_z_score():
    data = [10.0, 10.2, 9.9, 10.1, 10.0, 25.0]
    result = detect_outliers(data)
    assert result.indices == (5,)
    assert result.median == 10.05
    with pytest.raises(CalculationError, match="MAD is zero"):
        detect_outliers([1, 1, 1, 1, 9])
    assert detect_outliers([1, 2, 3, 4, 5]).indices == ()


def test_moving_average_and_variability():
    assert moving_average([1, 2, 3, 4, 5], 3) == [2.0, 3.0, 4.0]
    assert moving_average([1, 2, 3], 1) == [1.0, 2.0, 3.0]
    with pytest.raises(InvalidParameterError):
        moving_average([1, 2], 3)
    v = variability([[10.0, 10.2, 9.8], [11.0, 11.2, 10.8]])
    assert v.within_std == pytest.approx(0.2, rel=1e-12)  # each group has s = 0.2
    assert v.groups == 2 and v.total_n == 6
