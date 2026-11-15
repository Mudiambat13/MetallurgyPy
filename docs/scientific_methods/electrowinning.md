# Electrowinning

**Package:** `metallurgypy.electrowinning` · **Status:** implemented (`electrowinning.faraday`)

## Scope

Faraday's law, current efficiency, deposited mass, current density, cathode area, theoretical production and energy consumption.

## Equations

Theoretical deposited mass from Faraday's law, for current \(I\), time \(t\), molar mass \(M\), electrons transferred per ion \(n\) and the Faraday constant \(F\):

\[
m_{\text{theo}} = \frac{I \, t \, M}{n \, F}
\]

\(F\) is the product of the Avogadro constant and the elementary charge, about \(96\,485\ \text{C/mol}\) (exact value fixed by the 2019 SI definition).

Actual deposited mass with current efficiency \(\eta\) (a fraction):

\[
m_{\text{actual}} = \eta \, m_{\text{theo}}
\qquad
\eta = \frac{m_{\text{actual}}}{m_{\text{theo}}}
\]

Current density for total current \(I\) on active cathode area \(A\):

\[
j = \frac{I}{A}
\]

Electrical energy for cell voltage \(U\), and specific energy per unit of deposited mass:

\[
E = U \, I \, t
\qquad
e = \frac{E}{m_{\text{actual}}} = \frac{U \, n \, F}{\eta \, M}
\]

## Theoretical and actual production

The two are reported side by side and never merged. Current efficiency, losses and electrical conditions are inputs supplied by the user and displayed with the result.

## Assumptions and limits

- a single electrode reaction with a fixed \(n\); side reactions appear only through \(\eta\)
- constant current and constant cell voltage over the period
- cell voltage is an input, not predicted by this model
- the model does not predict deposit quality, short circuits or process upsets
