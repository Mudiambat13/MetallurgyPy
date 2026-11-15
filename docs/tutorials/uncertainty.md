# Propagating measurement uncertainty

This tutorial uses **fictitious** numbers. It shows how the uncertainty of a feed mass, a grade and a recovery propagates to the recovered metal.

```python
from metallurgypy.precision import (
    Measurement, propagate_model, monte_carlo, one_at_a_time, format_with_uncertainty,
)

inputs = {
    "feed_mass": Measurement(1000, "t", 5),      # standard uncertainty 5 t
    "feed_grade": Measurement(2.5, "%", 0.05),   # +/- 0.05 percentage points
    "recovery": Measurement(92, "%", 1.0),
}

u = propagate_model("mass_balance.recovery", inputs)
metal = u["metal_recovered"]
print(format_with_uncertainty(metal.value, metal.standard_uncertainty), metal.unit)
```

The value is written `23.00(54)`: 23.00 t with a standard uncertainty of 0.54 t (coverage factor k = 1).

## Which input matters most?

```python
for name, share in metal.contributions.items():
    print(f"{name}: {share:.0%} of the variance")
```

Here the grade contributes about 74 % of the variance and the recovery about 22 %: a better assay of the grade would reduce the uncertainty more than a more precise weighing.

## Cross-check with Monte Carlo

The first-order method is an approximation. Check it by sampling:

```python
mc = monte_carlo("mass_balance.recovery", inputs, samples=20_000, seed=42)
sampled = mc.outputs["metal_recovered"]
print(sampled.standard_deviation, metal.standard_uncertainty)
assert abs(sampled.standard_deviation - metal.standard_uncertainty) < 0.05
```

For this nearly linear model the two agree. If they differ noticeably, the uncertainties are too large for the first-order method or the model is strongly non-linear near the nominal point; trust the Monte Carlo figure and look at the sensitivity below.

## Non-linear effects

```python
from metallurgypy.core import Quantity
from metallurgypy.registry import get_model

nominal = {
    "feed_mass": Quantity(1000, "t"),
    "feed_grade": Quantity(2.5, "%"),
    "recovery": Quantity(92, "%"),
}
for row in one_at_a_time("mass_balance.recovery", nominal, 0.1):
    if row.output == "metal_recovered":
        print(row.input, row.low, row.high, row.unit)
```

## Studio

In the Calculation workspace, type the standard uncertainty next to a value (same unit). Studio shows a "Std. uncertainty" column and an uncertainty budget in the details, and saves the uncertainties in the calculation file.

## What this does not tell you

The propagated uncertainty covers the effect of your input uncertainties **through the model**. It does not include model error: a recovery model that does not describe the circuit has an error that no input uncertainty reveals. See [Numerical precision and uncertainty](../scientific_methods/precision.md).
