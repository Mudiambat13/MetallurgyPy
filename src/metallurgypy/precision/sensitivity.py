"""Sensitivity analysis: which input moves which output, and by how much."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from metallurgypy.core.exceptions import InvalidParameterError, MetallurgyPyError
from metallurgypy.core.units import Quantity
from metallurgypy.precision._derivatives import derivatives_wrt, outputs_of
from metallurgypy.registry import ModelSpec, get_model


@dataclass(frozen=True)
class SensitivityEntry:
    output: str
    input: str
    derivative: float  # d(output)/d(input)
    normalised: float | None  # (x / y) * dy/dx : % change of y per % change of x; None if y == 0


def sensitivity_coefficients(
    model: str | ModelSpec, inputs: Mapping[str, Quantity]
) -> list[SensitivityEntry]:
    """Local derivative and dimensionless (elasticity) sensitivity of every output to every input."""
    spec = get_model(model) if isinstance(model, str) else model
    base = outputs_of(spec.run(inputs))
    entries: list[SensitivityEntry] = []
    for p in spec.parameters:
        derivs = derivatives_wrt(spec, inputs, p.name, scale=inputs[p.name].value)
        for out_name, d in derivs.items():
            y = base[out_name].value
            x = inputs[p.name].value
            entries.append(
                SensitivityEntry(out_name, p.name, d.value, None if y == 0.0 else x / y * d.value)
            )
    return entries


@dataclass(frozen=True)
class OneAtATimeEntry:
    output: str
    input: str
    low: float | None  # output value with the input decreased; None if outside the model domain
    high: float | None
    unit: str


def one_at_a_time(
    model: str | ModelSpec, inputs: Mapping[str, Quantity], relative_variation: float = 0.1
) -> list[OneAtATimeEntry]:
    """Vary each input alone by +/- ``relative_variation`` (default 10 %) and record every output.

    Unlike the derivative this is not local: it shows non-linear effects. A
    variation that leaves the model domain is reported as ``None``, never hidden.
    """
    if not 0.0 < relative_variation < 1.0:
        raise InvalidParameterError("relative_variation must be between 0 and 1 (excluded).")
    spec = get_model(model) if isinstance(model, str) else model
    base = outputs_of(spec.run(inputs))
    entries: list[OneAtATimeEntry] = []
    for p in spec.parameters:
        x = inputs[p.name]
        sides: dict[str, dict[str, float] | None] = {}
        for label, factor in (
            ("low", 1.0 - relative_variation),
            ("high", 1.0 + relative_variation),
        ):
            changed = dict(inputs)
            changed[p.name] = Quantity(x.value * factor, x.unit)
            try:
                sides[label] = {k: q.value for k, q in outputs_of(spec.run(changed)).items()}
            except MetallurgyPyError:
                sides[label] = None
        for out_name, q in base.items():
            low, high = sides["low"], sides["high"]
            entries.append(
                OneAtATimeEntry(
                    out_name,
                    p.name,
                    None if low is None else low.get(out_name),
                    None if high is None else high.get(out_name),
                    q.unit,
                )
            )
    return entries
