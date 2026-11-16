# Contribuer

Les contributions d'ingénieurs, de chercheurs, d'enseignants et de développeurs sont les bienvenues.

## Règles de base

- Le code et l'API sont en anglais.
- Documentez chaque équation, chaque hypothèse et chaque domaine de validité.
- N'ajoutez jamais de constantes, de données expérimentales ou de résultats de validation sans source.
- Gardez le Core libre de tout import graphique ; Studio n'utilise que l'API publique du Core.
- N'ajoutez une dépendance qu'avec une justification technique.
- Examinez les fichiers existants avant de les modifier et préservez le comportement validé.
- N'arrondissez jamais une valeur intermédiaire sans justification.

Merci de suivre aussi le [code de conduite](https://github.com/Mudiambat13/MetallurgyPy/blob/main/CODE_OF_CONDUCT.md).

## Installation pour le développement

```bash
pip install -e ".[dev]"

pytest                                  # les tests GUI s'ignorent sans PySide6
ruff check . && ruff format --check .
mypy                                    # mode strict
python tools/gen_model_reference.py --check
python tools/gen_api_reference.py --check
```

## Ajouter un modèle

1. Rédigez sa page scientifique : équations, hypothèses, domaine de validité, sources.
2. Implémentez-le avec contrôle des unités et validation des entrées.
3. Ajoutez des tests : formule, limites, entrées invalides, convergence le cas échéant, et un cas de référence documenté.
4. Ajoutez un exemple et enregistrez les métadonnées du modèle pour que Studio le découvre.

## Modifier la documentation

```bash
pip install -r docs/requirements.txt
mkdocs build --strict
```

Les sections « Models » des pages scientifiques et les pages de l'API sont **générées** depuis le code : après un changement de modèle ou de docstring, lancez `python tools/gen_model_reference.py` et `python tools/gen_api_reference.py` puis commitez le résultat. La même construction stricte tourne en CI sur les pull requests, et un push sur `main` déploie le site sur GitHub Pages.

Les pages de cette section française ne sont pas générées : si vous changez une page anglaise, mettez la page française correspondante à jour.
