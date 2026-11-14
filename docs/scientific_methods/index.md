# Scientific methods

Every model in MetallurgyPy has a page that states:

- the **equations** used
- the **assumptions** behind them
- the **domain of validity**
- the **inputs, units and conventions**
- known **limitations**
- the **source** of any constant or reference data, and the **version** of the model

If a page has no source for a value, MetallurgyPy does not ship that value: dosages, equilibrium data and similar parameters come from the user or from an explicitly documented source.

## Module status

| Module | Status | Page |
|---|---|---|
| Mass balance | Specified, first to be implemented (Phase 2) | [Mass balance](mass_balance.md) |
| Reagents | Specified (Phase 2) | [Reagents](reagents.md) |
| Electrowinning | Specified (Phase 5) | [Electrowinning](electrowinning.md) |
| Hydrometallurgy, solvent extraction, flotation, filtration, thermodynamics, statistics | Planned | [Other modules](other_modules.md) |
| Precision and uncertainty | Specified (Phase 3) | [Numerical precision and uncertainty](precision.md) |

!!! warning "Models, not validated simulators"
    A simplified model is not an industrial simulation validated against plant data. Use results as engineering estimates and validate them against measurements.
