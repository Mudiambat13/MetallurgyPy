# Quick start

## A first calculation

```python
from metallurgypy.core import Quantity
from metallurgypy.mass_balance import MassBalance

result = MassBalance(
    feed_mass=Quantity(1000, "t"),
    feed_grade=Quantity(2.5, "%"),
    recovery=Quantity(92, "%"),
).calculate()

print(result.metal_recovered)  # 23.0 t
print(result.metal_remaining)  # 2.0 t
```

Bare numbers also work and use documented default units (mass in tonnes, grades and recoveries as fractions between 0 and 1):

```python
MassBalance(feed_mass=1000, feed_grade=0.025, recovery=0.92).calculate()
```

This example is also provided as a script: `examples/mass_balance/basic_balance.py`. The inputs are illustrative, not plant data. The derivation is on the [Mass balance](scientific_methods/mass_balance.md) page.

## What a result carries

```python
result.provenance.model_version  # '1.0'
result.provenance.equations  # the formulas used
result.provenance.assumptions  # the assumptions, in plain language
result.provenance.inputs  # inputs as used, with units
result.warnings  # tuple of warnings (may be empty)
```

Each result exposes its inputs and units, the equations, assumptions, tolerances, calculation mode, the MetallurgyPy version and a UTC timestamp. Values are stored unrounded.

## Errors are explicit

```python
MassBalance(feed_mass=1000, feed_grade=0.025, recovery=1.2)
# InvalidParameterError: recovery = 1.2 fraction is outside the valid range of 0 to 1 (0 % to 100 %).
```

All library errors derive from `MetallurgyPyError`. Passing a mass where a grade is expected raises `DimensionError`, and a split that the grades cannot determine raises `ModelDomainError`.

## Save, reopen, export

```python
from metallurgypy.records import save_record, load_record, verify, export_result_csv

save_record("balance.mpy.json", result, name="Demo", notes="illustrative data")
record = load_record("balance.mpy.json")
print(verify(record))  # [] means a fresh calculation reproduces the saved result
export_result_csv("balance.csv", result)
```

Files are never overwritten unless you pass `overwrite=True`. A saved file is only data: reopening it looks the model up by name in a registry and never runs code from the file.

## Calculation modes

`standard` (float64) works for every model. `high_precision` (exact rational arithmetic) is available for `MassBalance`; other models refuse it with a clear error. Uncertainty-aware results come from `propagate_model` (see the [uncertainty tutorial](tutorials/uncertainty.md)). See [Numerical precision and uncertainty](scientific_methods/precision.md).

## Using Studio

```bash
pip install "metallurgypy[gui]"
metallurgypy-studio
```

Studio runs the same Core calculation as the snippet above. See the [Studio guide](gui/index.md).

## Next steps

- [Tutorial: your first mass balance](tutorials/first_mass_balance.md)
- [Architecture](architecture.md)
- [Scientific methods](scientific_methods/index.md)
