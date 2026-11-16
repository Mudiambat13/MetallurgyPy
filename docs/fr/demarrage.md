# Démarrage rapide

## Un premier calcul

```python
from metallurgypy.core import Quantity
from metallurgypy.mass_balance import MassBalance

resultat = MassBalance(
    feed_mass=Quantity(1000, "t"),
    feed_grade=Quantity(2.5, "%"),
    recovery=Quantity(92, "%"),
).calculate()

print(resultat.metal_recovered)  # 23.0 t
print(resultat.metal_remaining)  # 2.0 t
```

Une teneur de 2,5 % sur 1 000 t d'alimentation contient 25 t de métal ; avec 92 % de récupération, 23 t sont récupérées et 2 t restent dans les rejets. Les valeurs sont **illustratives**, pas des données d'usine.

Les nombres « nus » fonctionnent aussi : ils utilisent l'unité par défaut documentée du paramètre (masses en tonnes, **teneurs et récupérations en fractions** entre 0 et 1) :

```python
MassBalance(feed_mass=1000, feed_grade=0.025, recovery=0.92).calculate()
```

La démonstration est sur la page [Méthodes scientifiques](modules.md#bilan-de-matiere).

## Ce que porte un résultat

```python
print(resultat.provenance.model_version)  # '1.0'
print(resultat.provenance.equations)  # les formules utilisées
print(resultat.provenance.assumptions)  # les hypothèses, en clair
print(resultat.warnings)  # tuple d'avertissements (éventuellement vide)
```

Chaque résultat expose ses entrées et leurs unités, les équations, les hypothèses, les tolérances, le mode de calcul, la version de MetallurgyPy et un horodatage UTC. Les valeurs ne sont **jamais arrondies** dans le résultat.

## Les erreurs sont explicites

```python
from metallurgypy.mass_balance import MassBalance

try:
    MassBalance(feed_mass=1000, feed_grade=0.025, recovery=1.2)
except Exception as erreur:
    print(type(erreur).__name__)  # InvalidParameterError
```

Toutes les erreurs de la bibliothèque dérivent de `MetallurgyPyError`. Donner une masse là où une teneur est attendue lève `DimensionError`, et un partage que les teneurs ne permettent pas de déterminer lève `ModelDomainError`.

## Enregistrer, rouvrir, exporter

```python
from metallurgypy.core import Quantity
from metallurgypy.mass_balance import MassBalance
from metallurgypy.records import export_result_csv, load_record, save_record, verify

resultat = MassBalance(Quantity(1000, "t"), Quantity(2.5, "%"), Quantity(92, "%")).calculate()
save_record("bilan.mpy.json", resultat, name="Démo", notes="données illustratives", overwrite=True)
fiche = load_record("bilan.mpy.json")
print(verify(fiche))  # [] : un nouveau calcul reproduit le résultat enregistré
export_result_csv("bilan.csv", resultat, overwrite=True)
```

Un fichier n'est jamais écrasé sauf si vous passez `overwrite=True`. Un fichier enregistré n'est que de la donnée : le rouvrir cherche le modèle par son nom dans un registre et n'exécute jamais de code contenu dans le fichier.

## Lancer n'importe quel modèle par son identifiant

```python
from metallurgypy.registry import get_model, list_models

print(len(list_models()), "modèles")  # 21 modèles

modele = get_model("solvent_extraction.countercurrent_kremser")
for sortie in modele.run(modele.example).outputs():
    print(f"{sortie.label}: {sortie.quantity}")
```

Les valeurs d'exemple sont fictives : elles montrent seulement la forme de l'appel.

## Modes de calcul

`standard` (flottants 64 bits) fonctionne pour tous les modèles. `high_precision` (arithmétique rationnelle exacte) existe pour `MassBalance` ; les autres modèles le refusent avec un message clair. Les résultats avec incertitude viennent de `propagate_model` (voir [Précision et incertitude](precision.md)).

## Utiliser Studio

```bash
pip install -e ".[gui]"
metallurgypy-studio
```

Studio exécute le même calcul du Core que les extraits ci-dessus. Voir le [guide de Studio](studio.md).
