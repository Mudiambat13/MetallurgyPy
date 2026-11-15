# Hydrometallurgy

Leaching yield from solid assays (cross-checked against the solution assay), an empirical first-order leach-kinetics curve, stoichiometric neutralization, and precipitation yield.

!!! warning "Stoichiometry is not equilibrium"
    The neutralization model gives the *stoichiometric minimum*. It does not model buffering, metal hydrolysis, precipitation or gypsum formation, so real reagent consumption is usually higher. Kinetic curves are empirical fits, not mechanisms (no shrinking-core, diffusion or passivation model).

## Reconciliation, not verdict

The leaching model reports the gap between the amount dissolved according to the solid assays and the amount found in solution. A gap is information about assay error, entrained solution or precipitation. MetallurgyPy sets no acceptance threshold.

## Not implemented

Speciation, equilibrium diagrams, mechanistic kinetics, heap or tank-leach simulation, solubility-product models.

## Models

<!-- BEGIN GENERATED MODELS -->

### Leaching extraction yield

`hydrometallurgy.leaching_yield` · model version 1.0

Extraction from solid assays, cross-checked with the solution assay.

| Parameter | Meaning | Default unit |
|---|---|---|
| `feed_mass` | Feed mass. Dry mass of solids fed. | t |
| `feed_grade` | Feed grade. Metal mass fraction in the feed. | % |
| `residue_mass` | Residue mass. Dry mass of leach residue. | t |
| `residue_grade` | Residue grade. Metal mass fraction in the residue. | % |
| `solution_volume` | Pregnant solution volume. Volume of leach solution. | m3 |
| `solution_concentration` | Solution concentration. Metal concentration in the solution. | g/L |

**Equations**

```text
m_feed = F * g_feed
m_residue = R * g_res
extraction (solids) = 1 - m_residue / m_feed
m_dissolved (solids) = m_feed - m_residue
m_solution = V * C
gap = m_dissolved (solids) - m_solution
```

**Assumptions and limits**

- Single metal, same dry basis for solid masses and grades.
- The solid-based extraction is the reference; the solution-based amount is a cross-check.
- The gap is a reconciliation difference, not a verdict: assay error, entrained or wash solution, precipitation and sampling all contribute. MetallurgyPy sets no acceptance threshold.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `feed_mass` | 100 | t |
| `feed_grade` | 2 | % |
| `residue_mass` | 92 | t |
| `residue_grade` | 0.5 | % |
| `solution_volume` | 300 | m3 |
| `solution_concentration` | 5 | g/L |

| Output | Value | Unit |
|---|---|---|
| Metal in feed | 2000 | kg |
| Metal in residue | 460 | kg |
| Extraction (solid basis) | 0.77 | fraction |
| Metal dissolved (solid basis) | 1540 | kg |
| Metal in solution (solution basis) | 1500 | kg |
| Reconciliation gap (solids - solution) | 40 | kg |

### First-order leach kinetics

`hydrometallurgy.leach_kinetics_first_order` · model version 1.0

Empirical extraction versus time from a maximum extraction and a rate constant.

| Parameter | Meaning | Default unit |
|---|---|---|
| `maximum_extraction` | Maximum extraction. Plateau extraction for long times. | % |
| `rate_constant` | Rate constant k. First-order rate constant. | 1/h |
| `time` | Leaching time. Time at which the extraction is wanted. | h |

**Equations**

```text
X(t) = X_max * (1 - exp(-k * t))
t_90 = ln(10) / k   (time to reach 90 % of X_max)
```

**Assumptions and limits**

- Empirical single-rate model: it does not represent a mechanism (shrinking core, diffusion, passivation) and does not describe every ore or set of conditions.
- X_max and k are fitted by the user for a given ore, temperature, acidity and particle size; none is supplied.
- Valid only inside the time range of the data the parameters were fitted on.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `maximum_extraction` | 95 | % |
| `rate_constant` | 0.3 | 1/h |
| `time` | 12 | h |

| Output | Value | Unit |
|---|---|---|
| Extraction at time t | 0.924042 | fraction |
| Time to reach 90 % of maximum extraction | 7.67528 | h |

### Neutralization (stoichiometric)

`hydrometallurgy.neutralization` · model version 1.0

Stoichiometric base needed to neutralize free acidity.

| Parameter | Meaning | Default unit |
|---|---|---|
| `solution_volume` | Solution volume. Volume to neutralize. | m3 |
| `free_acidity` | Free acidity. Mol of H+ per litre. | mol/L |
| `base_molar_mass` | Base molar mass. Molar mass of the base formula unit. | g/mol |
| `base_equivalents` | OH- per formula unit. Hydroxide delivered per formula unit. | ratio |
| `base_purity` | Base purity. Active share of the commercial base. | % |

**Equations**

```text
n_H = V * c_H
n_base = n_H / z
m_base = n_base * M / p
```

**Assumptions and limits**

- Stoichiometric only: c_H is the free acidity in mol of H+ per litre; z is the number of OH- delivered per formula unit of base.
- No buffering, hydrolysis of dissolved metals, precipitation or gypsum formation is modelled, so the real consumption is usually higher.
- Base molar mass, purity and equivalents are supplied by the user.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `solution_volume` | 100 | m3 |
| `free_acidity` | 0.1 | mol/L |
| `base_molar_mass` | 56 | g/mol |
| `base_equivalents` | 2 | ratio |
| `base_purity` | 90 | % |

| Output | Value | Unit |
|---|---|---|
| Free acid (H+) to neutralize | 10000 | mol |
| Base needed (formula units) | 5000 | mol |
| Base mass (pure) | 280 | kg |
| Base mass (commercial, at given purity) | 311.111 | kg |

!!! warning
    Stoichiometric minimum only: actual consumption is higher when metals hydrolyse or precipitate.

### Precipitation yield

`hydrometallurgy.precipitation_yield` · model version 1.0

Metal precipitated and yield from concentrations before and after.

| Parameter | Meaning | Default unit |
|---|---|---|
| `solution_volume` | Solution volume. Volume treated (assumed unchanged). | m3 |
| `initial_concentration` | Initial concentration. Dissolved metal before precipitation. | g/L |
| `final_concentration` | Final concentration. Dissolved metal after precipitation. | g/L |

**Equations**

```text
m_precipitated = (C0 - Cf) * V
yield = (C0 - Cf) / C0
```

**Assumptions and limits**

- The solution volume is unchanged by the precipitation reagent (no dilution); use the final volume otherwise.
- The metal removed from solution reports entirely to the solid (no adsorption on other solids, no volatilisation).
- No equilibrium or solubility-product model: concentrations are measured values.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `solution_volume` | 50 | m3 |
| `initial_concentration` | 4 | g/L |
| `final_concentration` | 0.2 | g/L |

| Output | Value | Unit |
|---|---|---|
| Metal precipitated | 190 | kg |
| Precipitation yield | 0.95 | fraction |
| Metal left in solution | 10 | kg |

<!-- END GENERATED MODELS -->

## Sources and validation

The equations are standard textbook relations. The implementation is checked against hand calculations and analytic limits in the test suite (`tests/process/`). It has **not** been validated against experimental or plant data; do that before relying on a result for a decision. Sources for each relation are listed in the [scientific audit](../project/scientific_audit.md).
