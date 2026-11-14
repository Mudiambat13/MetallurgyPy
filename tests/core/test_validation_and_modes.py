import math

import pytest

from metallurgypy.core import CalculationMode, InvalidParameterError, Tolerances
from metallurgypy.core.exceptions import MetallurgyPyError
from metallurgypy.core.modes import resolve_mode
from metallurgypy.core.validation import (
    require_between,
    require_non_negative,
    require_positive,
    require_real,
)


def test_require_real_accepts_numbers_and_returns_float():
    assert require_real("x", 3) == 3.0
    assert isinstance(require_real("x", 3), float)


@pytest.mark.parametrize("bad", [math.nan, math.inf, True, "1", None])
def test_require_real_rejects(bad):
    with pytest.raises(InvalidParameterError):
        require_real("x", bad)


def test_sign_and_range_checks():
    assert require_positive("x", 1e-300) > 0
    with pytest.raises(InvalidParameterError):
        require_positive("x", 0)
    assert require_non_negative("x", 0) == 0.0
    with pytest.raises(InvalidParameterError):
        require_non_negative("x", -1e-12)
    assert require_between("x", 1.0, 0.0, 1.0) == 1.0
    with pytest.raises(InvalidParameterError, match="between"):
        require_between("x", 1.0000001, 0.0, 1.0)


def test_error_messages_name_the_parameter():
    with pytest.raises(InvalidParameterError, match="feed_mass"):
        require_positive("feed_mass", -3)


def test_invalid_parameter_is_both_library_and_value_error():
    assert issubclass(InvalidParameterError, MetallurgyPyError)
    assert issubclass(InvalidParameterError, ValueError)


def test_tolerances_isclose():
    tol = Tolerances(rel=1e-9, abs=1e-12)
    assert tol.isclose(1.0, 1.0 + 5e-10)
    assert not tol.isclose(1.0, 1.0 + 5e-9)
    assert tol.isclose(0.0, 5e-13)
    assert not tol.isclose(0.0, 5e-12)
    with pytest.raises(InvalidParameterError):
        Tolerances(rel=-1.0)


def test_only_standard_mode_is_implemented_and_others_are_refused():
    assert resolve_mode("standard", (CalculationMode.STANDARD,)) is CalculationMode.STANDARD
    with pytest.raises(InvalidParameterError, match="not implemented"):
        resolve_mode("high_precision", (CalculationMode.STANDARD,))
    with pytest.raises(InvalidParameterError, match="Unknown calculation mode"):
        resolve_mode("turbo", (CalculationMode.STANDARD,))
