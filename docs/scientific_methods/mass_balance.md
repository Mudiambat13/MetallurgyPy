# Mass balance

**Package:** `metallurgypy.mass_balance` · **Status:** two models implemented (`MassBalance`, `TwoProductBalance`), tested, model version 1.0

## Scope

Implemented now:

- metal balance from a feed mass, a grade and a recovery (`MassBalance`)
- two-product split (concentrate and tailings) from the three grades (`TwoProductBalance`), with mass yield, recovery and enrichment ratio
- closure checks and warnings

Planned: solid/liquid balances, multi-stream balances, reconciliation of measured data.

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

## Two-product balance

For a feed \(F\) split into a concentrate (grade \(c\)) and tailings (grade \(t\)), the mass and metal balances

\[
F = C + T \qquad F g = C c + T t
\]

give

\[
C = F\,\frac{g - t}{c - t} \qquad T = F\,\frac{c - g}{c - t}
\]

and the derived quantities

\[
\text{mass yield} = \frac{C}{F} \qquad
R = \frac{C\,c}{F\,g} \qquad
\text{enrichment ratio} = \frac{c}{g}
\]

**Worked example (illustrative data):** \(F = 1000\) t, \(g = 2\,\%\), \(c = 20\,\%\), \(t = 0.4\,\%\).

\[
C = 1000 \times \frac{0.020 - 0.004}{0.200 - 0.004} = \frac{16}{0.196} \approx 81.63\ \text{t}
\qquad
\text{yield} \approx 8.16\,\%
\qquad
R \approx 81.6\,\%
\]

The mass yield (about 8 %) and the recovery (about 82 %) are very different numbers.

**Domain.** The feed grade must lie between the tailings and concentrate grades, and the two product grades must differ; otherwise a product would need a negative mass or the split is undetermined. Outside this domain the model raises `ModelDomainError` instead of returning a number. A zero feed grade makes recovery undefined and is also refused.

## Conventions

- Bare numbers use documented default units: **mass in tonnes, grades and recoveries as fractions** (0.025 means 2.5 %). Pass a `Quantity` to use another unit. Mass units: `g`, `kg`, `t`, `kt`, `Mt`. Grade units: `fraction`, `%`, `ppm`, `g/t`.
- `ppm` and `g/t` are by mass and equal 1e-6, so they only make sense for mass-basis grades.
- A recovery can only be given as a `fraction` or in `%`: `g/t` is refused for it.
- Grades must be between 0 and 1 (0 % to 100 %); a recovery outside that range is refused.
- Results are returned in the unit of the mass input.
- The user is responsible for using the same dry or wet basis for masses and grades.

## Checks

The metal balance is closed by construction, and the code cross-checks the two ways of computing the remaining metal against the configurable tolerances. A failure raises `CalculationError`, which would indicate a bug rather than bad input. Display of numbers is rounded by Studio only; results, saved files and exports keep full float64 values.

## Assumptions and limits

- steady-state, single-time-point balance of one component
- grades are taken as exact: analytical uncertainty is not propagated in `standard` mode (uncertainty propagation is planned for Phase 3)
- real sampling and assay errors can make a computed yield or recovery physically meaningless even when the arithmetic is valid
- the balance is arithmetic: it says nothing about whether a recovery is achievable in a real circuit
