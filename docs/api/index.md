# API reference

!!! info "Hand-written for now"
    This page is not generated from docstrings. Adding `mkdocstrings` is a planned improvement. Every public function has a docstring: use `help(...)`.

## Namespaces

| Import | Content |
|---|---|
| `metallurgypy.core` | `Quantity`, `convert`, `Tolerances`, `CalculationMode`, `Provenance`, result classes (`CalculationResult`, `GenericResult`, `OutputItem`, `ChartData`), exceptions |
| `metallurgypy.mass_balance` | `MassBalance`, `TwoProductBalance` |
| `metallurgypy.reagents` | Dilution, concentration conversion, consumption |
| `metallurgypy.electrowinning` | Faraday-law production, current density, energy |
| `metallurgypy.flotation` | Two-product balance, first-order kinetics |
| `metallurgypy.filtration` | Constant-pressure cake filtration, cake moisture |
| `metallurgypy.hydrometallurgy` | Leaching yield, first-order leach kinetics, neutralization, precipitation yield |
| `metallurgypy.solvent_extraction` | Single stage, stripping, Kremser, stages required, `McCabeThieleAnalysis` |
| `metallurgypy.thermodynamics` | Gibbs equilibrium, strong and weak acid pH |
| `metallurgypy.statistics` | `describe`, `linear_regression`, `correlation`, `detect_outliers`, `moving_average`, `variability` |
| `metallurgypy.precision` | `Measurement`, `propagate_model`, `monte_carlo`, `sensitivity_coefficients`, `one_at_a_time`, `format_with_uncertainty`, `round_sig`, `platform_precision` |
| `metallurgypy.registry` | `list_models`, `get_model`, `ModelSpec`, `ParameterSpec`, `MODULE_CATALOG` |
| `metallurgypy.records` | `save_record`, `load_record`, `verify`, `recompute`, `export_result_csv`, `export_result_json`, `csv_safe` |
| `metallurgypy.data_io` | `read_table`, `import_table`, `ColumnMapping`, `run_batch`, `write_rejected_csv` |
| `metallurgypy.comparison` | `compare`, `comparison_to_csv`, `export_comparison_csv` |
| `metallurgypy.reports` | `ReportEntry`, `build_report`, `render_html`, `write_html`, `write_pdf` |
| `metallurgypy.projects` | `Project`, `ProjectEntry`, `ProjectError` |
| `metallurgypy.visualization` | `build_figure`, `save_chart` (needs the `visualization` extra) |

All 21 models are registered under ids such as `mass_balance.recovery` or `solvent_extraction.countercurrent_kremser`; `list_models()` returns them with their parameters, units, equations source and illustrative examples.

## Conventions

- Bare numbers use a documented default unit; **grades, recoveries, efficiencies and purities are fractions** (use `Quantity(2.5, "%")` for percentages) and masses are in tonnes unless the parameter says otherwise.
- Results are unrounded; every result has `.provenance`.
- Files are never overwritten unless `overwrite=True`.

## Exceptions

`MetallurgyPyError` is the base class. Subclasses: `InvalidParameterError` (also a `ValueError`), `UnitConversionError`, `DimensionError`, `CalculationError`, `ConvergenceError` (a `CalculationError`), `ModelDomainError`, `RecordFormatError`. The import and project modules add `DataImportError` and `ProjectError`.
