# Reagents

**Package:** `metallurgypy.reagents` · **Status:** implemented (3 models)

## Scope

- dosage and specific consumption
- solution preparation and dilution
- mass and molar concentrations
- consumption per tonne of ore
- hourly, daily and per-campaign consumption

Reagent examples include sulfuric acid, lime, caustic soda, flocculants, extractants, oxidants and reducers.

!!! warning "Dosages are never built in"
    Dosages always come from the user or from an explicitly documented source. MetallurgyPy does not suggest operating dosages.

## Equations

Mass concentration and molar concentration, for solute mass \(m\), molar mass \(M\) and solution volume \(V\):

\[
\rho = \frac{m}{V} \qquad c = \frac{m}{M\,V}
\]

Dilution, conserving the amount of solute:

\[
c_1 V_1 = c_2 V_2
\]

Reagent consumption for a specific dosage \(d\) (reagent mass per tonne of ore) and ore throughput \(\dot{m}_{\text{ore}}\):

\[
\dot{m}_{\text{reagent}} = d \, \dot{m}_{\text{ore}}
\]

Daily and campaign consumption follow by multiplying by operating time, which the user supplies.

## Assumptions and limits

- ideal mixing: volumes are treated as additive only where stated; real solutions may show volume contraction
- purity and commercial strength of the reagent must be given by the user
- molar masses and densities used by examples carry a documented source
