# Solvent extraction

Single-stage extraction and stripping with a constant distribution coefficient, counter-current extraction by the Kremser equation, and the number of theoretical stages for a target extraction.

!!! warning "Linear isotherm only"
    Every model here assumes a constant distribution coefficient \(D\). Real extractants saturate, so \(D\) falls as the organic loads. Use these models for dilute systems or as a first estimate; the user supplies \(D\) for the stated chemical system, pH and temperature. No extractant data is built in.

## Theoretical stages are not mixer-settlers

Stages are equilibrium stages. Real stage efficiency is below 100 % and is not applied; the number of stages required is reported as a continuous value and the practical count is its ceiling before efficiency.

The Core also provides McCabe–Thiele stepping against a tabulated isotherm supplied by the user (`metallurgypy.solvent_extraction`); it interpolates the user's data and invents none.

## Not implemented

Mixer-settler efficiency, multi-component systems, pH-dependent isotherms, circuit simulation.

## Models

<!-- BEGIN GENERATED MODELS -->

### Single-stage extraction

`solvent_extraction.single_stage` · model version 1.0

One equilibrium stage with a constant distribution coefficient.

| Parameter | Meaning | Default unit |
|---|---|---|
| `feed_concentration` | Aqueous feed concentration. Metal concentration in the aqueous feed. | g/L |
| `distribution_coefficient` | Distribution coefficient D. C_org / C_aq at equilibrium (your system). | ratio |
| `oa_ratio` | O/A ratio. Organic to aqueous volume ratio. | ratio |

**Equations**

```text
D = C_org / C_aq   (at equilibrium)
C_aq = C_feed / (1 + D * r)      r = O/A (volume ratio)
C_org = D * C_aq
extraction = D * r / (1 + D * r)
```

**Assumptions and limits**

- Constant distribution coefficient D over the whole concentration range (linear isotherm); real extractants saturate, so check D at the loaded-organic concentration.
- Organic enters free of the metal; the stage reaches equilibrium; phases are immiscible and volumes unchanged.
- D is for the stated chemical system, pH, temperature and extractant, and comes from the user.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `feed_concentration` | 5 | g/L |
| `distribution_coefficient` | 4 | ratio |
| `oa_ratio` | 1 | ratio |

| Output | Value | Unit |
|---|---|---|
| Raffinate (aqueous) concentration | 1 | g/L |
| Loaded organic concentration | 4 | g/L |
| Extraction (fraction of metal transferred) | 0.8 | fraction |
| A/O ratio | 1 | ratio |
| Metal balance residual | 0 | g/L |

### Single-stage stripping

`solvent_extraction.stripping_single_stage` · model version 1.0

One equilibrium stripping stage with a constant distribution coefficient.

| Parameter | Meaning | Default unit |
|---|---|---|
| `loaded_organic_concentration` | Loaded organic concentration. Metal in the loaded organic. | g/L |
| `strip_distribution_coefficient` | Strip distribution coefficient. C_org / C_aq under stripping conditions. | ratio |
| `ao_ratio` | A/O ratio. Aqueous (strip) to organic volume ratio. | ratio |
| `strip_aqueous_inlet_concentration` | Strip liquor inlet concentration. Metal already in the strip liquor. | g/L |

**Equations**

```text
y0 * O + x_in * A = y * O + x * A
y = D_s * x
x = (y0 + (A/O) * x_in) / (D_s + A/O)
stripping = (y0 - y) / y0
```

**Assumptions and limits**

- Constant distribution coefficient D over the whole concentration range (linear isotherm); real extractants saturate, so check D at the loaded-organic concentration.
- D_s = C_org / C_aq measured under STRIPPING conditions (typically much lower than in extraction).
- Phases immiscible, volumes unchanged, equilibrium reached.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `loaded_organic_concentration` | 4 | g/L |
| `strip_distribution_coefficient` | 0.05 | ratio |
| `ao_ratio` | 0.25 | ratio |
| `strip_aqueous_inlet_concentration` | 30 | g/L |

| Output | Value | Unit |
|---|---|---|
| Strip liquor concentration | 38.3333 | g/L |
| Stripped organic concentration | 1.91667 | g/L |
| Stripping (fraction removed from organic) | 0.520833 | fraction |
| Metal balance residual | -1.77636e-15 | g/L |

### Counter-current extraction (Kremser)

`solvent_extraction.countercurrent_kremser` · model version 1.0

Extraction over N theoretical counter-current stages, constant D.

| Parameter | Meaning | Default unit |
|---|---|---|
| `feed_concentration` | Aqueous feed concentration. Metal in the aqueous feed. | g/L |
| `distribution_coefficient` | Distribution coefficient D. C_org / C_aq (your system). | ratio |
| `oa_ratio` | O/A ratio. Organic to aqueous volume ratio. | ratio |
| `stages` | Theoretical stages N. Whole number of stages. | ratio |

**Equations**

```text
E = D * r      (extraction factor, r = O/A)
phi = (E - 1) / (E^(N+1) - 1)     (fraction left in raffinate; phi = 1/(N+1) if E = 1)
C_raffinate = phi * C_feed
C_loaded = (C_feed - C_raffinate) / r
```

**Assumptions and limits**

- Constant distribution coefficient D over the whole concentration range (linear isotherm); real extractants saturate, so check D at the loaded-organic concentration.
- N equilibrium (theoretical) stages in counter-current; the organic enters free of the metal.
- Mixer-settler efficiency is not applied: real stage efficiency is below 100 % and must be handled by the user.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `feed_concentration` | 5 | g/L |
| `distribution_coefficient` | 2 | ratio |
| `oa_ratio` | 1 | ratio |
| `stages` | 3 | ratio |

| Output | Value | Unit |
|---|---|---|
| Extraction factor E = D * O/A | 2 | ratio |
| Raffinate concentration | 0.333333 | g/L |
| Loaded organic concentration | 4.66667 | g/L |
| Extraction (fraction) | 0.933333 | fraction |

### Stages required

`solvent_extraction.stages_required` · model version 1.0

Theoretical counter-current stages for a target extraction, constant D.

| Parameter | Meaning | Default unit |
|---|---|---|
| `distribution_coefficient` | Distribution coefficient D. C_org / C_aq (your system). | ratio |
| `oa_ratio` | O/A ratio. Organic to aqueous volume ratio. | ratio |
| `target_extraction` | Target extraction. Fraction of metal to extract (0 to 100 %, excluded). | % |

**Equations**

```text
E = D * r
phi = 1 - extraction
N = ln(1 + (E - 1) / phi) / ln(E) - 1      (N = 1/phi - 1 if E = 1)
```

**Assumptions and limits**

- Constant distribution coefficient D over the whole concentration range (linear isotherm); real extractants saturate, so check D at the loaded-organic concentration.
- N is the continuous number of theoretical stages; the practical (integer) count is its ceiling, before stage efficiency.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `distribution_coefficient` | 2 | ratio |
| `oa_ratio` | 1 | ratio |
| `target_extraction` | 99 | % |

| Output | Value | Unit |
|---|---|---|
| Theoretical stages (continuous) | 5.65821 | ratio |
| Theoretical stages (rounded up) | 6 | ratio |
| Extraction factor E = D * O/A | 2 | ratio |

<!-- END GENERATED MODELS -->

## Sources and validation

The equations are standard textbook relations. The implementation is checked against hand calculations and analytic limits in the test suite (`tests/process/`). It has **not** been validated against experimental or plant data; do that before relying on a result for a decision. Sources for each relation are listed in the [scientific audit](../project/scientific_audit.md).
