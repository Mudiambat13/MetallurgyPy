# Thermodynamics

Gibbs energy and equilibrium constant from \(\Delta H\) and \(\Delta S\), and pH of strong and weak monoprotic acids in the ideal-solution approximation.

!!! warning "Ideal solutions"
    Activity is taken equal to concentration. For concentrated acids and process liquors the activity coefficients are far from 1 and a measured pH can differ by more than one unit from these results. \(\Delta H\), \(\Delta S\), \(K_a\) and \(K_w\) come from the user's documented source; MetallurgyPy ships no thermodynamic database.

## Constants

\(R\) and \(F\) are derived from the exact 2019 SI values of \(N_A\), \(e\) and \(k_B\). The weak-acid model solves the charge balance numerically by bisection; the bracket, iteration count and residual are recorded in the result.

## Not implemented

Speciation, Pourbaix diagrams, activity-coefficient models, polyprotic acids, temperature-dependent \(\Delta H\) and \(\Delta S\) (heat capacity).

## Models

<!-- BEGIN GENERATED MODELS -->

### Gibbs energy and equilibrium constant

`thermodynamics.gibbs_equilibrium` · model version 1.0

dG and K at a temperature from dH and dS (constant with temperature).

| Parameter | Meaning | Default unit |
|---|---|---|
| `delta_h` | Reaction enthalpy dH. From your documented source. | kJ/mol |
| `delta_s` | Reaction entropy dS. From your documented source. | J/(mol.K) |
| `temperature` | Temperature. Must be close to the data reference temperature. | degC |

**Equations**

```text
dG = dH - T * dS
ln K = -dG / (R * T)
log10 K = ln K / ln 10
```

**Assumptions and limits**

- dH and dS are constant between their reference temperature and T (heat capacity change neglected): valid near the temperature where they were determined, increasingly wrong far from it.
- K is the thermodynamic equilibrium constant (activities, standard states of the data source); it is not a concentration quotient.
- dH, dS and their reference temperature come from the user's documented source.
- R = N_A * k_B, exact in the 2019 SI definition.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `delta_h` | -50 | kJ/mol |
| `delta_s` | -100 | J/(mol.K) |
| `temperature` | 25 | degC |

| Output | Value | Unit |
|---|---|---|
| Gibbs energy change | -20.185 | kJ/mol |
| ln K | 8.14254 | ratio |
| log10 K | 3.53626 | ratio |
| Equilibrium constant K | 3437.63 | ratio |

### Strong acid pH (ideal)

`thermodynamics.strong_acid_ph` · model version 1.0

pH of a fully dissociated acid, ideal-solution approximation.

| Parameter | Meaning | Default unit |
|---|---|---|
| `concentration` | Acid concentration. Formula-unit concentration. | mol/L |
| `protons` | Protons per formula unit. Fully dissociated protons. | ratio |

**Equations**

```text
[H+] = z * c
pH = -log10([H+])
```

**Assumptions and limits**

- Complete dissociation of z protons per formula unit (z supplied by the user).
- Activity equals concentration: valid only in dilute solution. Concentrated acids and process liquors have activity coefficients far from 1, and the measured pH can differ by more than one unit.
- Autoionization of water is neglected, so the model is refused below 1e-6 mol/L of H+.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `concentration` | 0.01 | mol/L |
| `protons` | 1 | ratio |

| Output | Value | Unit |
|---|---|---|
| [H+] | 0.01 | mol/L |
| pH (ideal) | 2 | ratio |

### Weak acid pH (ideal)

`thermodynamics.weak_acid_ph` · model version 1.0

pH of a monoprotic weak acid from the charge balance, solved numerically.

| Parameter | Meaning | Default unit |
|---|---|---|
| `analytical_concentration` | Total acid concentration. Analytical concentration. | mol/L |
| `pka` | pKa. Acid constant at the solution temperature. | ratio |
| `pkw` | pKw. Water constant at the solution temperature. | ratio |

**Equations**

```text
[A-] = C * Ka / (Ka + [H+])
[OH-] = Kw / [H+]
charge balance:  [H+] - [A-] - [OH-] = 0   (solved by bisection)
alpha = Ka / (Ka + [H+])
```

**Assumptions and limits**

- Single monoprotic acid, no other acid, base or complexing species in solution.
- Activity equals concentration (ideal solution); Ka and Kw apply at the solution temperature.
- pKa and pKw come from the user's documented source; pKw depends on temperature.
- Solved on [H+] with bisection; the bracket and convergence are recorded in the result.

**Numerical method:** Bisection on [H+] in [1e-30, C + 1] mol/L.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `analytical_concentration` | 0.1 | mol/L |
| `pka` | 4.76 | ratio |
| `pkw` | 14 | ratio |

| Output | Value | Unit |
|---|---|---|
| [H+] | 0.0013096 | mol/L |
| pH (ideal) | 2.88286 | ratio |
| Degree of dissociation alpha | 0.013096 | fraction |

<!-- END GENERATED MODELS -->

## Sources and validation

The equations are standard textbook relations. The implementation is checked against hand calculations and analytic limits in the test suite (`tests/process/`). It has **not** been validated against experimental or plant data; do that before relying on a result for a decision. Sources for each relation are listed in the [scientific audit](../project/scientific_audit.md).
