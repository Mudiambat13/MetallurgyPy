# Installation

!!! note "Pas encore sur PyPI"
    MetallurgyPy n'est pas publié sur PyPI. Tant que le propriétaire n'a pas approuvé une publication, on l'installe depuis un clone du dépôt.

## Prérequis

- Python 3.10 ou plus récent (testé en CI sur 3.10, 3.11, 3.12 et 3.13)
- Windows ou Linux pour Studio ; la compatibilité macOS reste possible

## Installation depuis un clone

```bash
git clone https://github.com/Mudiambat13/MetallurgyPy.git
cd MetallurgyPy
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

pip install -e .                 # Core seul : aucune dépendance
pip install -e ".[gui]"          # Core + Studio
pip install -e ".[dev]"          # tests, lint, vérification de types
```

## Les options (extras)

| Extra | Ajoute | Sert à |
|---|---|---|
| *(aucun)* | rien | la bibliothèque Core |
| `visualization` | matplotlib | graphiques, export PNG/SVG, rapports PDF |
| `excel` | openpyxl | lecture des fichiers `.xlsx` |
| `gui` | PySide6, pyqtgraph, matplotlib | MetallurgyPy Studio |
| `dev` | pytest, mypy, ruff, build, twine… | le développement |
| `docs` | mkdocs, mkdocs-material | construire cette documentation |

Le Core n'a **aucune dépendance obligatoire** : il n'utilise que la bibliothèque standard de Python.

## Lancer Studio

```bash
metallurgypy-studio
# ou
python -m metallurgypy_studio
```

Si PySide6 n'est pas installé, la commande l'indique et s'arrête avec un message clair.

## Vérifier l'installation

```bash
python -c "import metallurgypy; print(metallurgypy.__version__)"
metallurgypy-studio --version
```

Pour vérifier que le Core n'a pas besoin de l'interface graphique, contrôlez que `PySide6` est absent d'un environnement neuf (`pip list`).

## Construire cette documentation en local

```bash
pip install -r docs/requirements.txt
mkdocs serve            # aperçu sur http://127.0.0.1:8000
mkdocs build --strict   # même contrôle que la CI
```
