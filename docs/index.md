# MetallurgyPy

*Engineering Metallurgy with Python.*

MetallurgyPy is an open-source scientific library for metallurgical process calculations, paired with a desktop application for people who prefer forms and charts to scripts.

!!! warning "Project status: early development (0.1.0.dev0)"
    The Core foundation, **Mass Balance** and a first **Studio** are implemented and tested. Every other module is planned: its page describes the intended design and says so. Nothing is published on PyPI yet.

## Two products, one engine

| Product | What it is | Install |
|---|---|---|
| **MetallurgyPy Core** | Python library: units, validation, traceable results, process models. Works on servers and in notebooks, with no GUI dependency. | `pip install metallurgypy` |
| **MetallurgyPy Studio** | PySide6 desktop application: forms, tables, interactive charts, projects, reports. Calls the Core public API and never re-implements equations. | `pip install "metallurgypy[gui]"` |

## What it covers

- Mass and metallurgical balances
- Hydrometallurgy: leaching, dissolution, precipitation, neutralization
- Solvent extraction and stripping
- Electrowinning
- Flotation and filtration
- Reagent dosing and consumption
- Thermodynamics and chemical equilibria
- Statistics and visualization

## Design principles

1. **Every equation is documented**, with its assumptions and domain of validity.
2. **Units are checked**, not assumed.
3. **No invented data.** Constants, reference data and validation results always have a stated source.
4. **Three things are never confused:** numerical precision, measurement uncertainty and model accuracy. See [Numerical precision and uncertainty](scientific_methods/precision.md).
5. **Simplified models are labelled as such.** MetallurgyPy is not a validated industrial simulator and does not replace DCS, PLC or SCADA systems.
6. **Results are traceable:** inputs, model version, method, assumptions, warnings and software version travel with each result.

## Where to go next

- [Install the library](installation.md)
- [Run a first calculation](getting_started.md)
- [Understand the architecture](architecture.md)
- [Browse the scientific methods](scientific_methods/index.md)
