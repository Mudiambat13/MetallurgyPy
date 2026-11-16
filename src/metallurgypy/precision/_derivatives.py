"""Finite-difference derivatives of model outputs with respect to model inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from metallurgypy.core.exceptions import (
    CalculationError,
    InvalidParameterError,
    MetallurgyPyError,
    ModelDomainError,
)
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity
from metallurgypy.registry import ModelSpec

# Relative step. Central differences have a truncation error of order h^2 and a rounding
# error of order eps/h; h = 1e-6 balances them for smooth analytic models (about 1e-10 relative).
REL_STEP = 1e-6


@dataclass(frozen=True)
class Derivative:
    value: float  # d(output) / d(input), in output unit per input unit
    scheme: str  # "central", "forward" or "backward"


def outputs_of(result: CalculationResult) -> dict[str, Quantity]:
    return {o.name: o.quantity for o in result.outputs()}


def _run(
    spec: ModelSpec, inputs: Mapping[str, Quantity], name: str, value: float
) -> dict[str, Quantity]:
    changed = dict(inputs)
    changed[name] = Quantity(value, inputs[name].unit)
    return outputs_of(spec.run(changed))


def derivatives_wrt(
    spec: ModelSpec, inputs: Mapping[str, Quantity], name: str, scale: float
) -> dict[str, Derivative]:
    """Derivatives of every output with respect to input ``name``.

    ``scale`` is a characteristic size of the input (its magnitude or its
    uncertainty); the step is ``REL_STEP * scale``. If a central step leaves the
    valid domain (for example a recovery at 100 %), a one-sided step is used. If
    no step is valid the model is not differentiable there and
    :class:`ModelDomainError` is raised.
    """
    x = inputs[name].value
    h = REL_STEP * max(abs(x), abs(scale), 1e-300)
    base = outputs_of(spec.run(inputs))
    results: dict[str, Derivative] = {}
    schemes = (("central", (-h, h)), ("forward", (0.0, h)), ("backward", (-h, 0.0)))
    for scheme, (lo, hi) in schemes:
        try:
            low = _run(spec, inputs, name, x + lo) if lo != 0.0 else base
            high = _run(spec, inputs, name, x + hi) if hi != 0.0 else base
        except (InvalidParameterError, ModelDomainError, CalculationError):
            continue
        except MetallurgyPyError:
            continue
        for key, base_q in base.items():
            if key in low and key in high and low[key].unit == base_q.unit == high[key].unit:
                results[key] = Derivative((high[key].value - low[key].value) / (hi - lo), scheme)
        return results
    raise ModelDomainError(
        f"Input {name!r} = {inputs[name]} sits where the model is not defined on either side: "
        "its uncertainty cannot be propagated by linearisation."
    )
