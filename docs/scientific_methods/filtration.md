# Filtration

Constant-pressure cake filtration (the classical \(t/V\) versus \(V\) form) and cake moisture on wet and dry bases.

!!! warning "Scope"
    Incompressible cake only. Compressible cakes, constant-rate filtration, washing and deliquoring are not modelled. The specific cake resistance \(\alpha\) and medium resistance \(R_m\) must be measured for the slurry and filter in use; none is supplied.

## Reading the result

`K` and `B` are the slope and intercept of the \(\mathrm{d}t/\mathrm{d}V\) line. If your measured \(t/V\) points are not a straight line against \(V\), the constant-pressure incompressible model does not describe your filtration and the result should not be trusted.

## Not implemented

Compressible cakes, pressure/vacuum scale-up, centrifugal filtration, washing, deliquoring.

## Models

<!-- BEGIN GENERATED MODELS -->

### Constant-pressure cake filtration

`filtration.constant_pressure_cake` · model version 1.0

Time and rate to filter a volume through an incompressible cake at constant pressure.

| Parameter | Meaning | Default unit |
|---|---|---|
| `viscosity` | Filtrate viscosity. Dynamic viscosity of the filtrate. | mPa.s |
| `cake_resistance` | Specific cake resistance (alpha). Measured for this slurry. | m/kg |
| `solids_per_filtrate` | Solids per filtrate volume (c). Dry solids deposited per volume of filtrate. | kg/m3 |
| `medium_resistance` | Medium resistance (R_m). Resistance of the filter medium. | 1/m |
| `area` | Filter area. Filtration area. | m2 |
| `pressure_drop` | Pressure drop. Constant pressure difference across cake and medium. | kPa |
| `filtrate_volume` | Filtrate volume. Volume of filtrate to collect. | m3 |

**Equations**

```text
dt/dV = K * V + B
K = mu * alpha * c / (A^2 * dP)
B = mu * R_m / (A * dP)
t(V) = K * V^2 / 2 + B * V
rate(V) = 1 / (K * V + B)
m_cake,dry = c * V
```

**Assumptions and limits**

- Constant pressure drop, incompressible cake (alpha constant), constant medium resistance R_m.
- c is the dry-solids mass deposited per unit volume of filtrate (not the slurry solids concentration).
- Darcy flow through the cake and medium, no settling during filtration, no cake washing or deliquoring.
- alpha and R_m are measured for the slurry and filter used (user inputs).

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `viscosity` | 1 | mPa.s |
| `cake_resistance` | 1e+11 | m/kg |
| `solids_per_filtrate` | 50 | kg/m3 |
| `medium_resistance` | 1e+10 | 1/m |
| `area` | 10 | m2 |
| `pressure_drop` | 300 | kPa |
| `filtrate_volume` | 5 | m3 |

| Output | Value | Unit |
|---|---|---|
| Filtration time | 35 | min |
| Average filtrate rate | 8.57143 | m3/h |
| Filtrate rate at the end | 4.30279 | m3/h |
| Dry cake mass | 250 | kg |

### Cake moisture

`filtration.cake_moisture` · model version 1.0

Moisture of a filter cake (wet and dry basis) from wet and dry masses.

| Parameter | Meaning | Default unit |
|---|---|---|
| `wet_cake_mass` | Wet cake mass. Mass before drying. | kg |
| `dry_cake_mass` | Dry cake mass. Mass after drying to constant mass. | kg |

**Equations**

```text
m_water = m_wet - m_dry
moisture (wet basis) = m_water / m_wet
moisture (dry basis) = m_water / m_dry
```

**Assumptions and limits**

- Wet mass is weighed before drying and dry mass after drying to constant mass (user measurements).
- All mass lost on drying is counted as water; soluble salts and volatile species are not separated.
- Moisture is reported on both bases: they differ and must not be mixed up.

**Illustrative example** (fictional values, not plant data)

| Input | Value | Unit |
|---|---|---|
| `wet_cake_mass` | 100 | kg |
| `dry_cake_mass` | 80 | kg |

| Output | Value | Unit |
|---|---|---|
| Water mass | 20 | kg |
| Moisture, wet basis | 0.2 | fraction |
| Moisture, dry basis | 0.25 | fraction |

<!-- END GENERATED MODELS -->

## Sources and validation

The equations are standard textbook relations. The implementation is checked against hand calculations and analytic limits in the test suite (`tests/process/`). It has **not** been validated against experimental or plant data; do that before relying on a result for a decision. Sources for each relation are listed in the [scientific audit](../project/scientific_audit.md).
