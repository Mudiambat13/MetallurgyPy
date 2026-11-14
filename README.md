# MetallurgyPy

*Engineering Metallurgy with Python.*

Open-source scientific library for metallurgical process calculations (**MetallurgyPy Core**) and a desktop application for visualization and reporting (**MetallurgyPy Studio**).

> **Status: early development (0.1.0.dev0).** Core foundation, Mass Balance and a first Studio are implemented. Other modules are planned. Nothing is published on PyPI.

📖 **Documentation:** https://mudiambat13.github.io/MetallurgyPy/

## Planned scope

Mass balance, hydrometallurgy, solvent extraction, electrowinning, flotation, filtration, reagents, thermodynamics, statistics and visualization, with checked units, traceable results and explicit handling of numerical precision, measurement uncertainty and model accuracy.

MetallurgyPy is not a validated industrial simulator and does not replace DCS/PLC/SCADA systems.

## Install (from a clone, until a release is approved)

```bash
pip install -e .                # Core, no GUI dependency
pip install -e ".[gui]"         # Core + Studio
metallurgypy-studio             # launch Studio
```

```python
from metallurgypy.core import Quantity
from metallurgypy.mass_balance import MassBalance

result = MassBalance(Quantity(1000, "t"), Quantity(2.5, "%"), Quantity(92, "%")).calculate()
print(result.metal_recovered)   # 23.0 t
```

## Repository contents

| Path | Content |
|---|---|
| `src/metallurgypy/` | Core library |
| `studio/metallurgypy_studio/` | Desktop application |
| `tests/` | Core, Studio logic and GUI tests |
| `examples/` | Runnable examples |
| `specs/` | Technical specification (French) |
| `docs/`, `mkdocs.yml` | Documentation site (MkDocs Material) |
| `.github/workflows/docs.yml` | Build and deploy to GitHub Pages |

## Run the tests

```bash
pip install -e ".[dev]"
pytest                          # GUI tests are skipped if PySide6 is absent
```

## Build the docs locally

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

## Roadmap

See the [roadmap](https://mudiambat13.github.io/MetallurgyPy/roadmap/). Next: Phase 0 (design confirmation), then Phase 1 (Core foundation).

## License

MIT, see [LICENSE](LICENSE).
