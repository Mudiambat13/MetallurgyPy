# MetallurgyPy

*Engineering Metallurgy with Python.*

Open-source scientific library for metallurgical process calculations (**MetallurgyPy Core**) and a desktop application for visualization and reporting (**MetallurgyPy Studio**).

> **Status: development release (0.2.0.dev0).** Core, 21 process models, uncertainty propagation, data import, scenario comparison, HTML/PDF reports, projects and Studio are implemented and tested. The models are simplified and **not validated against experimental or plant data**, and Studio has not been run on a real display by the author of the code (see the [scientific audit](https://mudiambat13.github.io/MetallurgyPy/project/scientific_audit/)). Nothing is published on PyPI.

📖 **Documentation:** https://mudiambat13.github.io/MetallurgyPy/

## Scope

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
| `.github/workflows/` | Tests (Core matrix, quality, GUI, packaging) and docs deployment |
| `SECURITY.md`, `CODE_OF_CONDUCT.md` | Reporting vulnerabilities, community rules |

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

See the [roadmap](https://mudiambat13.github.io/MetallurgyPy/roadmap/). Remaining work before a release candidate: review of the equations by a domain expert, validation against real data, and a run of Studio and CI on real machines.

## License

MIT, see [LICENSE](LICENSE).
