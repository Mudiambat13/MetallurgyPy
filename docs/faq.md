# FAQ

**Can I use MetallurgyPy without the GUI?**
Yes. The Core has no PySide6 dependency and runs on servers and in notebooks.

**Does Studio contain its own equations?**
No. It calls the Core public API, so a calculation gives the same result in Python and in Studio.

**Is it a validated process simulator?**
No. Models are documented and tested, but simplified models are not industrial simulations validated against plant data.

**Can it control or monitor my plant?**
No. Connections to DCS, PLC or SCADA, real-time acquisition and control are out of scope.

**Why are results shown with many digits?**
The engine keeps full precision and only rounds for display. More digits do not mean more accuracy; see [Numerical precision and uncertainty](scientific_methods/precision.md).

**Where do reagent dosages and equilibrium data come from?**
From you, or from an explicitly documented source. MetallurgyPy does not invent them.

**Can it propagate measurement uncertainty?**
Yes: GUM first-order propagation and a Monte Carlo cross-check, in Python and in Studio. It covers the effect of input uncertainty through the model, not model error. See [Numerical precision and uncertainty](scientific_methods/precision.md).

**Can I import my data?**
Yes: CSV, JSON and Excel, with explicit units and a report of rejected rows. See [Data, comparison, reports and projects](guides/workflows.md).

**Which languages are supported?**
Code and API are English. Documentation starts in English, with French translation possible later.

**Is it on PyPI?**
Not yet. Publication requires the owner's explicit approval.
