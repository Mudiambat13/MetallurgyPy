# Flotation

Two simple tools for flotation data: the two-product (concentrate/tailings) balance computed from grades, and a first-order recovery-versus-time model.

!!! warning "What this is not"
    These are bookkeeping and empirical-fit tools. MetallurgyPy does not simulate a flotation circuit, does not predict floatability, and supplies no rate constants: `R_inf` and `k` must come from the user's own tests.

## Where the numbers come from

The balance uses the standard two-product formulae, the same as in [Mass balance](mass_balance.md). Grades carry assay and sampling error, and the formulae amplify it when the feed grade is close to the concentrate or tailings grade. The kinetic model has two empirical parameters that are valid only for the ore, reagents and cell conditions where they were fitted.

## Not implemented

Multi-class (fast/slow floating) kinetics, circuit simulation, bubble/particle models, scale-up factors.

## Models

<!-- BEGIN GENERATED MODELS -->

### Concentrate / tailings balance

`flotation.balance` · model version 1.0

Mass pull, metal recovery and enrichment from feed, concentrate and tailings grades.

| Parameter | Meaning | Default unit |
|---|---|---|
| `feed_mass` | Feed mass. Mass of the feed (> 0). | t |
| `feed_grade` | Feed grade. Mass fraction of the metal in the feed. | % |
| `concentrate_grade` | Concentrate grade. Mass fraction of the metal in the concentrate. | % |
| `tailings_grade` | Tailings grade. Mass fraction of the metal in the tailings. | % |

**Equations**

```text
C = F * (g - t) / (c - t)
T = F * (c - g) / (c - t)
mass_yield = C / F
recovery = C * c / (F * g)
enrichment_ratio = c / g
```

**Assumptions and limits**

- Two products only, single component, steady state, no accumulation.
- Grades are mass fractions of the metal on the same basis (dry or wet) as the masses.
- Grades are taken as exact: analytical uncertainty is not propagated in standard mode.
- Mass and metal balances are closed by construction; the residuals reported are numerical only.
- Real grades carry sampling and assay error, which can make a computed yield or recovery physically meaningless even when the arithmetic is valid.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `feed_mass` | 1000 | t |
| `feed_grade` | 1.5 | % |
| `concentrate_grade` | 25 | % |
| `tailings_grade` | 0.2 | % |

| Output | Value | Unit |
|---|---|---|
| Concentrate mass | 52.4194 | t |
| Tailings mass | 947.581 | t |
| Mass yield (concentrate / feed) | 0.0524194 | fraction |
| Metal recovery to concentrate | 0.873656 | fraction |
| Enrichment ratio (c / g) | 16.6667 | ratio |
| Metal in feed | 15 | t |
| Metal in concentrate | 13.1048 | t |
| Metal in tailings | 1.89516 | t |
| Closure residual (mass) | 0 | t |
| Closure residual (metal) | 0 | t |

### First-order kinetics

`flotation.kinetics_first_order` · model version 1.0

Recovery versus time from an ultimate recovery and a rate constant.

| Parameter | Meaning | Default unit |
|---|---|---|
| `ultimate_recovery` | Ultimate recovery. Plateau recovery reached for long times. | % |
| `rate_constant` | Rate constant k. First-order flotation rate constant. | 1/min |
| `time` | Flotation time. Time at which the recovery is wanted. | min |

**Equations**

```text
R(t) = R_inf * (1 - exp(-k * t))
t_95 = ln(20) / k   (time to reach 95 % of R_inf)
```

**Assumptions and limits**

- A single rate constant k describes the whole feed (one floatability class). Real ores usually need several.
- R_inf and k are empirical, valid for the ore, reagents and cell conditions where they were fitted; MetallurgyPy supplies none.
- Time is flotation (residence) time in the cell, with no scale-up factor applied.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `ultimate_recovery` | 90 | % |
| `rate_constant` | 0.5 | 1/min |
| `time` | 8 | min |

| Output | Value | Unit |
|---|---|---|
| Recovery at time t | 0.883516 | fraction |
| Recoverable fraction not yet recovered | 0.0164841 | fraction |
| Time to reach 95 % of ultimate recovery | 5.99146 | min |

<!-- END GENERATED MODELS -->

## Sources and validation

The equations are standard textbook relations. The implementation is checked against hand calculations and analytic limits in the test suite (`tests/process/`). It has **not** been validated against experimental or plant data; do that before relying on a result for a decision. Sources for each relation are listed in the [scientific audit](../project/scientific_audit.md).
