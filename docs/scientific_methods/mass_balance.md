# Mass balance

**Package:** `metallurgypy.mass_balance` · **Status:** specified, implementation in Phase 2

## Scope

- global and per-component mass balances
- solid/liquid balances
- grades and contained metal mass
- recovery and losses
- mass yield
- multi-stream balances
- balance closure and reconciliation gaps

## Definitions

Let \(F\) be the feed mass, \(g\) the feed grade expressed as a **mass fraction** of the metal (for example 0.025 for 2.5 %), and \(R\) the recovery as a fraction between 0 and 1.

Contained metal in the feed:

\[
m_{\text{feed}} = F \, g
\]

Metal recovered and metal remaining:

\[
m_{\text{rec}} = R \, F \, g \qquad
m_{\text{rem}} = (1 - R)\, F \, g
\]

Closure for a single component:

\[
m_{\text{feed}} = m_{\text{rec}} + m_{\text{rem}}
\]

For a split into concentrate (mass \(C\), grade \(c\)) and tailings (mass \(T\), grade \(t\)), with \(F = C + T\):

\[
R = \frac{C\,c}{F\,g} \qquad
\text{mass yield} = \frac{C}{F}
\]

## Recovery is not mass yield

Recovery is the share of the **contained metal** that reports to a product. Mass yield is the share of the **total mass** that reports to it. They are different quantities, and the library keeps them in separate, explicitly named fields.

## Worked example

Inputs: \(F = 1000\) (mass unit), \(g = 0.025\), \(R = 0.92\).

\[
m_{\text{feed}} = 1000 \times 0.025 = 25
\qquad
m_{\text{rec}} = 0.92 \times 25 = 23
\qquad
m_{\text{rem}} = 25 - 23 = 2
\]

The example uses illustrative inputs only, not plant data.

## Conventions the API must make explicit

- unit of mass and the calculation basis (dry or wet)
- mass or volume basis for grades
- how grades are expressed (fraction, percent, g/t)
- recovery definition used

## Assumptions and limits

- steady-state, single-time-point balance
- grades are taken as given; analytical uncertainty is not applied unless `uncertainty_aware` mode is used
- a reconciliation gap is reported, never silently absorbed
- the balance is arithmetic: it says nothing about whether the recovery is achievable in a real circuit
