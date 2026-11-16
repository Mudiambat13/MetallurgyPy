# Numerical precision and uncertainty

Scientific rigor depends on keeping three notions apart.

| Notion | Question it answers | Where MetallurgyPy deals with it |
|---|---|---|
| **Numerical precision** | How accurately does the algorithm compute, given rounding errors? | Calculation modes, tolerances, exact-arithmetic mode for the mass balance |
| **Measurement uncertainty** | How uncertain are the input data? | `Measurement`, `propagate_model`, `monte_carlo` |
| **Model accuracy** | How well does the physical or chemical model represent the real process? | Not computable by the library. Stated in each model's assumptions and in the [scientific audit](../project/scientific_audit.md) |

A result printed with 12 decimals is not necessarily accurate: the inputs may be known to three significant figures, and the model may be a rough approximation. **Uncertainty propagation measures only the first of these two effects that it can see: the effect of input uncertainty through the model. It says nothing about model error.**

## Calculation modes

| Mode | Status | What it does |
|---|---|---|
| `standard` | All models | Closed-form evaluation in `float64`. Inputs are taken as exact. |
| `high_precision` | `MassBalance` only | Inputs are converted to exact rationals, the balance is computed in exact `Fraction` arithmetic and rounded once to `float`. Other models refuse the mode with a clear error. |
| `uncertainty_aware` | Through `propagate_model` | Not a model constructor option: a model computes a number, `propagate_model` computes the number *and* its uncertainty. Asking a model for this mode raises an error that points to `propagate_model`. |

`high_precision` removes rounding error of the arithmetic only. It does not make a grade of 2.5 % more accurate than the assay that produced it.

!!! note "No precision promises beyond what the platform gives"
    `platform_precision()` reports what the platform really provides (`float` epsilon, `numpy.longdouble` if NumPy is present). MetallurgyPy does not claim more than that, and never mixes numeric types silently.

## Measurements

```python
from metallurgypy.precision import Measurement

m1 = Measurement(2.5, "%", 0.05)  # standard uncertainty
m2 = Measurement(2.5, "%", 0.1, kind="expanded", coverage_factor=2.0)
m3 = Measurement(10.0, "g/L", 0.2, kind="rectangular")  # half-width of the interval
m4 = Measurement.from_replicates([2.48, 2.52, 2.51], "%")  # Type A: s / sqrt(n)
```

`kind` is one of `standard`, `expanded` (needs `coverage_factor`), `rectangular` (\(u = a/\sqrt{3}\)) and `triangular` (\(u = a/\sqrt{6}\)). Everything is converted to a standard uncertainty, in the unit of the value.

## First-order propagation (GUM)

`propagate_model(model_id, measurements, correlations=None)` applies the law of propagation of uncertainty (JCGM 100:2008, equation 13):

\[
u_c^2(y) = \sum_i \sum_j \frac{\partial f}{\partial x_i}\frac{\partial f}{\partial x_j}\,u(x_i)\,u(x_j)\,r_{ij}
\]

- The derivatives are **central finite differences** of the registered model, so every model is supported without separate formulas. A step that leaves the model's domain is reported, never hidden.
- `correlations` is a mapping `{("a", "b"): r}`. The correlation matrix must be positive semi-definite (checked by a Cholesky decomposition); otherwise the call fails.
- Each output reports its standard uncertainty, the sensitivity to every input and the **contribution of each input to the variance** (the shares sum to 1; with correlated inputs a share can be negative).
- Warnings are attached when an input's relative standard uncertainty exceeds 10 % (the first-order approximation is then doubtful) and when the nominal value sits at the edge of the model domain (a one-sided derivative is used).

**Limits of the method.** It is first-order: it is reliable for small relative uncertainties and smooth models, and it can be wrong near a singularity (for example a division by a quantity that can approach zero) or for large uncertainties. Cross-check with Monte Carlo.

## Monte Carlo cross-check

`monte_carlo(model_id, measurements, correlations=None, samples=10_000, seed=...)` samples **normal** inputs (with the requested correlations) and reruns the model. `seed` is mandatory so that results are reproducible. Samples that fall outside the model domain are counted in `rejected`, not discarded silently. The standard library generator is used; no extra dependency.

## Sensitivity

- `sensitivity_coefficients` returns the local derivative and the dimensionless elasticity \(\frac{x}{y}\frac{\partial y}{\partial x}\) of each output with respect to each input.
- `one_at_a_time` varies each input alone by ±10 % (configurable) and records every output. It shows non-linear effects the derivative hides.

## Presenting a result with its uncertainty

`format_with_uncertainty(value, u)` follows the GUM convention: the uncertainty is rounded to two significant digits and the value to the same decimal place, giving `23.00(54)`. `round_sig` and `format_sig` round to significant figures **for presentation only**; stored values are never rounded.

## Constants

Only constants whose value is **exact by definition** are built in: \(N_A\), \(e\) and \(k_B\) from the 2019 SI redefinition. The Faraday constant \(F = N_A e\) and the gas constant \(R = N_A k_B\) are derived from them. Measured constants with an uncertainty are not shipped.

## Numerical validation

- relative and absolute tolerances (defaults \(10^{-9}\) and \(10^{-12}\)), configurable
- division-by-zero and non-finite value checks
- documented stopping and convergence criteria for iterative solvers (the bracket, iteration count and residual are stored in the result)
- unrounded values kept in results; rounding is for presentation only

## Traceability

An important result exposes its inputs and units, formula or model and version, numerical method, assumptions, tolerances, convergence status, mode, warnings, and the date and version of MetallurgyPy. When uncertainties were propagated, the input measurements, correlations and output uncertainties are saved in the calculation file too.

In Studio, the display precision setting only changes what is shown. It never changes values held by the engine, saved files or exports.
