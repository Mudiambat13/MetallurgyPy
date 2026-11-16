"""Propagation of input uncertainties through any registered model.

Two independent methods are provided, so that the first one can be checked:

``propagate_model``
    GUM first-order propagation (JCGM 100:2008, equation 13): the output
    variance is ``J S J^T`` with ``J`` the Jacobian (central finite
    differences) and ``S`` the input covariance matrix built from the standard
    uncertainties and the user-supplied correlation coefficients.
``monte_carlo``
    Sampling of the inputs from normal laws with the same covariance (inspired
    by JCGM 101:2008) and re-running the model. It captures non-linearity but
    assumes Gaussian inputs, and draws that leave the model domain are rejected
    and counted.

Neither method says anything about the *model* accuracy: only the effect of
input uncertainty on the outputs.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from metallurgypy.core.exceptions import (
    CalculationError,
    InvalidParameterError,
    MetallurgyPyError,
)
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity
from metallurgypy.precision._derivatives import Derivative, derivatives_wrt, outputs_of
from metallurgypy.precision.measurements import Measurement
from metallurgypy.registry import ModelSpec, get_model

Correlations = Mapping[tuple[str, str], float]

LINEARISATION_WARNING_LEVEL = 0.10  # relative standard uncertainty above which GUM-1 may be poor


def _covariance(
    names: list[str], std: dict[str, float], correlations: Correlations | None
) -> list[list[float]]:
    n = len(names)
    index = {name: i for i, name in enumerate(names)}
    corr = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for (a, b), r in (correlations or {}).items():
        if a not in index or b not in index:
            raise InvalidParameterError(f"Correlation refers to an unknown input: {(a, b)!r}.")
        if a == b:
            raise InvalidParameterError("A correlation needs two different inputs.")
        if isinstance(r, bool) or not isinstance(r, (int, float)) or not -1.0 <= r <= 1.0:
            raise InvalidParameterError(
                f"Correlation {(a, b)!r} must be between -1 and 1, got {r!r}."
            )
        i, j = index[a], index[b]
        if corr[i][j] not in (0.0, r) or corr[j][i] not in (0.0, r):
            raise InvalidParameterError(f"Conflicting correlation values for {(a, b)!r}.")
        corr[i][j] = corr[j][i] = float(r)
    _cholesky(corr)  # raises if the matrix is not a valid correlation matrix
    return [[corr[i][j] * std[names[i]] * std[names[j]] for j in range(n)] for i in range(n)]


def _cholesky(matrix: list[list[float]]) -> list[list[float]]:
    """Lower-triangular factor, or :class:`InvalidParameterError` if not positive semi-definite."""
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = matrix[i][j] - sum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                if s < -1e-12:
                    raise InvalidParameterError(
                        "The correlation coefficients are inconsistent: the matrix is not positive semi-definite."
                    )
                lower[i][j] = math.sqrt(max(s, 0.0))
            else:
                lower[i][j] = 0.0 if lower[j][j] == 0.0 else s / lower[j][j]
    return lower


def _align(spec: ModelSpec, measurements: Mapping[str, Measurement]) -> dict[str, Quantity]:
    expected = {p.name for p in spec.parameters}
    missing = sorted(expected - set(measurements))
    unknown = sorted(set(measurements) - expected)
    if missing:
        raise InvalidParameterError(f"Missing input(s): {', '.join(missing)}.")
    if unknown:
        raise InvalidParameterError(f"Unknown input(s) for {spec.model_id}: {', '.join(unknown)}.")
    return {name: m.quantity for name, m in measurements.items()}


@dataclass(frozen=True)
class OutputUncertainty:
    name: str
    label: str
    value: float
    unit: str
    standard_uncertainty: float
    sensitivities: Mapping[str, float]  # d(output)/d(input), output unit per input unit
    contributions: Mapping[str, float]  # share of the output variance due to each input (sums to 1)

    def expanded(self, k: float = 2.0) -> float:
        return k * self.standard_uncertainty

    @property
    def relative(self) -> float | None:
        return None if self.value == 0.0 else self.standard_uncertainty / abs(self.value)

    def as_measurement(self, method: str = "GUM first-order propagation") -> Measurement:
        return Measurement(
            self.value, self.unit, self.standard_uncertainty, "standard", method=method
        )


@dataclass(frozen=True)
class UncertainResult:
    """Nominal result plus the propagated uncertainty of every output."""

    nominal: CalculationResult
    outputs: Mapping[str, OutputUncertainty]
    inputs: Mapping[str, Measurement]
    correlations: Mapping[tuple[str, str], float]
    method: str
    warnings: tuple[str, ...] = field(default=())

    def __getitem__(self, name: str) -> OutputUncertainty:
        return self.outputs[name]

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "calculation_mode": "uncertainty_aware",
            "inputs": {k: m.to_dict() for k, m in self.inputs.items()},
            "correlations": [[a, b, r] for (a, b), r in self.correlations.items()],
            "outputs": {
                k: {
                    "value": o.value,
                    "unit": o.unit,
                    "standard_uncertainty": o.standard_uncertainty,
                    "sensitivities": dict(o.sensitivities),
                    "contributions": dict(o.contributions),
                }
                for k, o in self.outputs.items()
            },
            "warnings": list(self.warnings),
        }


def propagate_model(
    model: str | ModelSpec,
    measurements: Mapping[str, Measurement],
    correlations: Correlations | None = None,
) -> UncertainResult:
    """GUM first-order propagation of ``measurements`` through a registered model."""
    spec = get_model(model) if isinstance(model, str) else model
    nominal_inputs = _align(spec, measurements)
    names = [p.name for p in spec.parameters]
    std = {n: measurements[n].standard_uncertainty for n in names}
    cov = _covariance(names, std, correlations)
    nominal = spec.run(nominal_inputs)
    base = outputs_of(nominal)

    warnings: list[str] = []
    for n in names:
        rel = measurements[n].relative_standard_uncertainty
        if rel is not None and rel > LINEARISATION_WARNING_LEVEL:
            warnings.append(
                f"{n}: relative standard uncertainty {rel:.1%} is large; first-order propagation may be "
                "inaccurate. Compare with monte_carlo()."
            )
    jacobian: dict[str, dict[str, Derivative]] = {}
    for n in names:
        if std[n] == 0.0 and not any(cov[names.index(n)][j] for j in range(len(names))):
            continue  # exact input: no contribution, no derivative needed
        jacobian[n] = derivatives_wrt(spec, nominal_inputs, n, scale=std[n])
        if any(d.scheme != "central" for d in jacobian[n].values()):
            warnings.append(
                f"{n}: nominal value is at the edge of the model domain (one-sided derivative used)."
            )

    outputs: dict[str, OutputUncertainty] = {}
    labels = {o.name: o.label for o in nominal.outputs()}
    for out_name, q in base.items():
        grad = [
            jacobian[n][out_name].value if n in jacobian and out_name in jacobian[n] else 0.0
            for n in names
        ]
        var = sum(
            grad[i] * cov[i][j] * grad[j] for i in range(len(names)) for j in range(len(names))
        )
        var = max(var, 0.0)  # tiny negative values are rounding noise of a PSD form
        contributions: dict[str, float] = {}
        if var > 0.0:
            for i, n in enumerate(names):
                contributions[n] = (
                    grad[i] * sum(cov[i][j] * grad[j] for j in range(len(names))) / var
                )
        else:
            contributions = dict.fromkeys(names, 0.0)
        outputs[out_name] = OutputUncertainty(
            out_name,
            labels[out_name],
            q.value,
            q.unit,
            math.sqrt(var),
            {n: grad[i] for i, n in enumerate(names)},
            contributions,
        )
    corr_used = {k: float(v) for k, v in (correlations or {}).items()}
    return UncertainResult(
        nominal=nominal,
        outputs=outputs,
        inputs=dict(measurements),
        correlations=corr_used,
        method="GUM first-order propagation (central finite differences, JCGM 100:2008 eq. 13)",
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class MonteCarloOutput:
    name: str
    unit: str
    mean: float
    standard_deviation: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class MonteCarloResult:
    outputs: Mapping[str, MonteCarloOutput]
    samples: int
    rejected: int
    seed: int
    warnings: tuple[str, ...]


def monte_carlo(
    model: str | ModelSpec,
    measurements: Mapping[str, Measurement],
    correlations: Correlations | None = None,
    *,
    samples: int = 10_000,
    seed: int,
) -> MonteCarloResult:
    """Propagate by sampling normal inputs. ``seed`` is required so runs are reproducible."""
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 100:
        raise InvalidParameterError("samples must be an integer >= 100.")
    spec = get_model(model) if isinstance(model, str) else model
    nominal_inputs = _align(spec, measurements)
    names = [p.name for p in spec.parameters]
    std = {n: measurements[n].standard_uncertainty for n in names}
    lower = _cholesky(_covariance(names, std, correlations))
    rng = random.Random(seed)
    columns: dict[str, list[float]] = {}
    units: dict[str, str] = {}
    rejected = 0
    for _ in range(samples):
        z = [rng.gauss(0.0, 1.0) for _ in names]
        draw = {
            n: Quantity(
                nominal_inputs[n].value + sum(lower[i][k] * z[k] for k in range(i + 1)),
                nominal_inputs[n].unit,
            )
            for i, n in enumerate(names)
        }
        try:
            result = outputs_of(spec.run(draw))
        except (MetallurgyPyError, CalculationError):
            rejected += 1
            continue
        for key, q in result.items():
            columns.setdefault(key, []).append(q.value)
            units[key] = q.unit
    kept = samples - rejected
    if kept < 2:
        raise CalculationError(
            "Almost every Monte Carlo draw left the model domain: the inputs are too uncertain for this model."
        )
    outputs: dict[str, MonteCarloOutput] = {}
    for key, values in columns.items():
        mean = math.fsum(values) / len(values)
        sd = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1))
        outputs[key] = MonteCarloOutput(key, units[key], mean, sd, min(values), max(values))
    warnings = []
    if rejected:
        warnings.append(
            f"{rejected} of {samples} draws left the model domain and were rejected: the distribution is truncated, "
            "so the statistics are biased."
        )
    return MonteCarloResult(outputs, kept, rejected, seed, tuple(warnings))
