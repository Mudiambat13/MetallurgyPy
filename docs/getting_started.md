# Quick start

!!! info "Indicative API"
    The snippets below show the target API from the specification. Names and signatures are confirmed in Phase 0 and may change before the first release.

## A first calculation

```python
from metallurgypy.mass_balance import MassBalance

balance = MassBalance(
    feed_mass=1000,    # basis and unit to be explicit in the final API
    feed_grade=0.025,  # mass fraction (2.5 %)
    recovery=0.92,     # fraction of contained metal recovered
)

result = balance.calculate()

print(result.metal_recovered)
print(result.metal_remaining)
print(result.recovery)
```

With these inputs the contained metal is \(1000 \times 0.025 = 25\) mass units, of which \(25 \times 0.92 = 23\) are recovered and \(2\) remain. The full derivation is on the [Mass balance](scientific_methods/mass_balance.md) page.

## What a result carries

A result is more than a number. Each important result exposes:

- the inputs and their units
- the formula or model used, and its version
- the numerical method and tolerances
- assumptions and warnings
- uncertainties, when supplied
- convergence status
- the date and the MetallurgyPy version

Full, unrounded values are kept in the result. Rounding happens only when displaying.

## Calculation modes

| Mode | Behaviour |
|---|---|
| `standard` | Usual scientific calculation in `float64` |
| `high_precision` | Reinforced precision where justified and available |
| `uncertainty_aware` | Propagates measurement uncertainties |

See [Numerical precision and uncertainty](scientific_methods/precision.md) for what each mode does and does not guarantee.

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
