# MetallurgyPy

*Engineering Metallurgy with Python.*

Open-source scientific library for metallurgical process calculations (**MetallurgyPy Core**) and a desktop application for visualization and reporting (**MetallurgyPy Studio**).

> **Status: specification stage.** The design and documentation are in place; the code is being developed phase by phase. Nothing is published on PyPI.

📖 **Documentation:** https://mudiambat13.github.io/MetallurgyPy/

## Planned scope

Mass balance, hydrometallurgy, solvent extraction, electrowinning, flotation, filtration, reagents, thermodynamics, statistics and visualization, with checked units, traceable results and explicit handling of numerical precision, measurement uncertainty and model accuracy.

MetallurgyPy is not a validated industrial simulator and does not replace DCS/PLC/SCADA systems.

## Planned installation

```bash
pip install metallurgypy              # Core, no GUI dependency
pip install "metallurgypy[gui]"       # Core + Studio
```

## Repository contents

| Path | Content |
|---|---|
| `specs/` | Technical specification (French) |
| `docs/`, `mkdocs.yml` | Documentation site (MkDocs Material) |
| `.github/workflows/docs.yml` | Build and deploy to GitHub Pages |

## Build the docs locally

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

## Roadmap

See the [roadmap](https://mudiambat13.github.io/MetallurgyPy/roadmap/). Next: Phase 0 (design confirmation), then Phase 1 (Core foundation).

## License

MIT, see [LICENSE](LICENSE).
