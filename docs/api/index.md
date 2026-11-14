# API reference

!!! info "Not generated yet"
    There is no importable code yet, so there is nothing to document automatically. Once Phase 1 lands, this section will be generated from docstrings with `mkdocstrings` (added to `docs/requirements.txt` at that point).

## Planned public namespaces

| Namespace | Content |
|---|---|
| `metallurgypy.core` | units, constants, exceptions, validation, results, provenance |
| `metallurgypy.precision` | numerical modes, uncertainty, `Measurement`, tolerances, significant figures, sensitivity |
| `metallurgypy.mass_balance` | `MassBalance` |
| `metallurgypy.reagents` | dosing, dilution, consumption |
| `metallurgypy.hydrometallurgy` | leaching, precipitation, neutralization, dissolution |
| `metallurgypy.solvent_extraction` | stages, circuits, McCabe-Thiele |
| `metallurgypy.electrowinning` | electrolysis, current efficiency, production, energy |
| `metallurgypy.flotation`, `filtration`, `thermodynamics`, `statistics`, `visualization` | as described in [Other modules](../scientific_methods/other_modules.md) |

## Planned exceptions

`MetallurgyPyError`, `InvalidParameterError`, `UnitConversionError`, `DimensionError`, `CalculationError`, `ConvergenceError`, `ModelDomainError`.
