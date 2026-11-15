# Scientific audit

An honest statement of what has and has not been verified. Read it before relying on a result.

## What "verified" means here

For each model, the tests compare the implementation with:

1. **hand calculations** done separately from the code;
2. **analytic limits** (for example, one Kremser stage equals the single-stage formula; \(\phi = 1/(N+1)\) when \(E = 1\); extraction is capped at \(1-E\) for \(E<1\); a very weak, very dilute acid gives pH 7; a very strong acid behaves as completely dissociated);
3. **closure and consistency** (mass and metal balances close; round trips such as stages-required then Kremser recover the target);
4. **invalid input and domain edges** (negative, zero, non-finite, out-of-range, wrong units).

This shows that the code implements the stated equations correctly. It does **not** show that the equations describe a given plant, ore or chemical system.

## What has *not* been verified

- **No comparison with experimental or plant data.** No validation result against measurements is claimed anywhere.
- **No independent scientific review.** The equations are standard textbook relations written from the author's knowledge. A domain expert should check each page. Bibliographic references have **not** been added or checked; none are invented here.
- **No comparison with another software package** (for example a process simulator or a thermodynamic database).
- **Studio has not been run** on a real display by the author of this code. Its logic is tested without Qt (view models, services); the widgets are exercised only by the CI job.
- **CI has not been run.** The workflows exist but were not executed against GitHub.
- **Linting.** `ruff` was not available where this was written; `mypy --strict` passes on the sources.

## Model-by-model status

| Module | Equation family | Verified against | Main scientific limit |
|---|---|---|---|
| Mass balance | Metal and two-product balance | Hand calculation, closure, exact-arithmetic cross-check | Grades are taken as exact in standard mode; real assays make yield and recovery uncertain |
| Reagents | Dilution, mass/molar conversion, dosage × throughput | Hand calculation | Volumes assumed additive; dosages, purity, throughput are user inputs |
| Electrowinning | Faraday's law, current efficiency, energy | Reference formula with the exact SI constants, hand-calculated energy and current density | Constant current, efficiency and voltage supplied by the user |
| Flotation | Two-product balance, first-order kinetics | Hand calculation, limits (\(t\to\infty\)) | Single rate constant; parameters empirical and ore-specific |
| Filtration | Constant-pressure incompressible cake | Hand calculation | Incompressible cake only; \(\alpha\), \(R_m\) from the user |
| Hydrometallurgy | Yield, first-order kinetics, stoichiometric neutralization, precipitation yield | Hand calculation, closure | Stoichiometric/empirical; no speciation or mechanism |
| Solvent extraction | Single stage, Kremser, stages required, McCabe–Thiele stepping | Hand calculation, analytic limits, round trip (stages required then Kremser). McCabe–Thiele stepping is checked against Kremser for a linear isotherm within about 8 %, because the last stage is prorated linearly | Constant \(D\) (linear isotherm); equilibrium stages, no efficiency |
| Thermodynamics | \(\Delta G\), \(K\); ideal pH | Hand calculation (weak acid pH 2.883), limits, residual of the charge balance, bisection convergence | Ideal solutions; constant \(\Delta H\), \(\Delta S\) |
| Uncertainty | GUM first order, Monte Carlo | Analytic cases (products, sums), Monte Carlo agreement, correlation handling | First order; normal inputs in Monte Carlo; excludes model error |
| Statistics | Standard descriptive tools | Hand-calculated values and error cases | Descriptive only |

## Constants and data

Only constants exact by definition are included (\(N_A\), \(e\), \(k_B\) from the 2019 SI; \(F\) and \(R\) derived). No thermodynamic tables, extractant data, rate constants or reagent dosages are shipped. Example values in the interface and docs are labelled fictitious.

## Test inventory

About 280 automated tests (Core, process models, precision, records, data import, comparison, reports, projects, Studio logic and documentation examples). The GUI test module is skipped when PySide6 is absent.

## Before using a result for a decision

1. Read the model's assumptions on its page.
2. Check that your conditions are inside its domain of validity.
3. Compare with at least one measurement or an independent calculation.
4. Propagate the uncertainty of your inputs and look at which one dominates.
