# Scientific methods

Every model in MetallurgyPy has a page that states:

- the **equations** used
- the **assumptions** behind them
- the **domain of validity**
- the **inputs, units and conventions**
- known **limitations**
- the **version** of the model

For the pages marked *generated*, the equations, assumptions and parameter tables are read from the code by `tools/gen_model_reference.py`, and a test fails if they drift. If a value has no documented source, MetallurgyPy does not ship it: dosages, equilibrium data, rate constants and similar parameters come from the user.

## Module status

| Module | Models | Page |
|---|---|---|
| Mass balance | 2 | [Mass balance](mass_balance.md) |
| Reagents | 3 | [Reagents](reagents.md) |
| Electrowinning | 1 | [Electrowinning](electrowinning.md) |
| Flotation | 2 | [Flotation](flotation.md) *(generated)* |
| Filtration | 2 | [Filtration](filtration.md) *(generated)* |
| Hydrometallurgy | 4 | [Hydrometallurgy](hydrometallurgy.md) *(generated)* |
| Solvent extraction | 4, plus McCabe–Thiele in the API | [Solvent extraction](solvent_extraction.md) *(generated)* |
| Thermodynamics | 3 | [Thermodynamics](thermodynamics.md) *(generated)* |
| Statistics | API only | [Statistics](statistics.md) |
| Precision and uncertainty | `Measurement`, GUM propagation, Monte Carlo, sensitivity | [Numerical precision and uncertainty](precision.md) |

All 21 registered models are available in Studio, which builds its forms from their metadata.

!!! warning "Models, not validated simulators"
    A simplified model is not an industrial simulation validated against plant data. The implementations are checked against hand calculations and analytic limits, **not** against experimental data. See the [scientific audit](../project/scientific_audit.md). Use results as engineering estimates and validate them against measurements.
