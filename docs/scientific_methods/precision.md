# Numerical precision and uncertainty

Scientific rigor depends on keeping three notions apart.

| Notion | Question it answers |
|---|---|
| **Numerical precision** | How accurately does the algorithm compute, given rounding errors? |
| **Measurement uncertainty** | How uncertain are the input data? |
| **Model accuracy** | How well does the physical or chemical model represent the real process? |

A result printed with 12 decimals is not necessarily accurate: the inputs may be known to three significant figures, and the model may be a rough approximation.

## Calculation modes

| Mode | Description |
|---|---|
| `standard` | Usual scientific computing in `float64` |
| `high_precision` | Reinforced precision where it is justified and available |
| `uncertainty_aware` | Propagation of input uncertainties |

!!! note "No precision promises beyond what the platform gives"
    MetallurgyPy does not claim higher precision when the algorithm, the platform or the data cannot guarantee it. For example `numpy.longdouble` depends on the platform, so its behaviour is detected and documented rather than assumed.

Numeric types are never mixed silently.

## Measurements

The `Measurement` object holds at least:

- value and unit
- uncertainty and its type (standard, expanded, other)
- coverage factor, when applicable
- origin or measurement method, if provided
- optional timestamp

Independent uncertainties are supported; correlations are supported when the data allow it.

## Numerical validation

- configurable absolute and relative tolerances
- approximate comparisons
- division-by-zero and non-finite value checks
- conditioning checks where relevant
- documented stopping and convergence criteria
- unrounded values kept in results
- rounding only for presentation, unless a scientific rule explicitly justifies it

## Traceability

An important result can expose its inputs and units, formula or model and version, numerical method, assumptions, uncertainties, warnings, tolerances, convergence status, and the date and version of MetallurgyPy.

In Studio, the display precision setting only changes what is shown. It never changes values held by the engine.
