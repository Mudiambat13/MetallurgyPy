# API reference

!!! info "Hand-written for now"
    Code exists, but this page is not generated from docstrings yet. Adding `mkdocstrings` is a planned improvement.

## Implemented today

| Import | Content |
|---|---|
| `metallurgypy.core` | `Quantity`, `Tolerances`, `CalculationMode`, `Provenance`, result base classes, exceptions |
| `metallurgypy.mass_balance` | `MassBalance`, `TwoProductBalance` and their result classes |
| `metallurgypy.records` | `save_record`, `load_record`, `verify`, `recompute`, `export_result_csv`, `export_result_json` |
| `metallurgypy.registry` | `list_models`, `get_model`, `ModelSpec`, `ParameterSpec` |
| `metallurgypy.visualization` | `build_figure`, `save_chart` (needs the `visualization` extra) |

## Planned

| Namespace | Content |
|---|---|
| `metallurgypy.precision` | `Measurement`, uncertainty propagation, significant figures, sensitivity |
| `metallurgypy.reagents` | dosing, dilution, consumption |
| `metallurgypy.hydrometallurgy` | leaching, precipitation, neutralization, dissolution |
| `metallurgypy.solvent_extraction` | stages, circuits, McCabe-Thiele |
| `metallurgypy.electrowinning` | electrolysis, current efficiency, production, energy |
| `metallurgypy.flotation`, `filtration`, `thermodynamics`, `statistics` | as described in [Other modules](../scientific_methods/other_modules.md) |

## Exceptions

`MetallurgyPyError` is the base class. Subclasses: `InvalidParameterError` (also a `ValueError`), `UnitConversionError`, `DimensionError`, `CalculationError`, `ConvergenceError` (a `CalculationError`), `ModelDomainError`, `RecordFormatError`.
