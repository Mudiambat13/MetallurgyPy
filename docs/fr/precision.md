# Précision numérique et incertitude

La rigueur scientifique exige de ne jamais confondre trois notions.

| Notion | Question à laquelle elle répond | Où MetallurgyPy la traite |
|---|---|---|
| **Précision numérique** | Avec quelle exactitude l'algorithme calcule-t-il, compte tenu des erreurs d'arrondi ? | Modes de calcul, tolérances, arithmétique exacte pour le bilan de matière |
| **Incertitude de mesure** | Quelle est l'incertitude des données d'entrée ? | `Measurement`, `propagate_model`, `monte_carlo` |
| **Exactitude du modèle** | Dans quelle mesure le modèle physique ou chimique représente-t-il le procédé réel ? | Non calculable par la bibliothèque. Elle est exposée dans les hypothèses de chaque modèle et dans l'[audit scientifique](audit.md) |

Un résultat affiché avec 12 décimales n'est pas forcément exact : les entrées peuvent n'être connues qu'à trois chiffres significatifs, et le modèle peut être une approximation grossière. **La propagation d'incertitude ne mesure que l'effet de l'incertitude des entrées à travers le modèle. Elle ne dit rien de l'erreur du modèle.**

## Modes de calcul

| Mode | Disponibilité | Ce qu'il fait |
|---|---|---|
| `standard` | Tous les modèles | Évaluation en forme fermée en `float64`. Les entrées sont prises comme exactes. |
| `high_precision` | `MassBalance` seulement | Les entrées deviennent des rationnels exacts, le bilan est calculé en arithmétique `Fraction` exacte puis arrondi une seule fois. Les autres modèles refusent ce mode avec un message clair. |
| `uncertainty_aware` | Via `propagate_model` | Ce n'est pas une option de constructeur : un modèle calcule un nombre, `propagate_model` calcule le nombre **et** son incertitude. |

`high_precision` supprime seulement l'erreur d'arrondi de l'arithmétique. Il ne rend pas une teneur de 2,5 % plus exacte que l'analyse qui l'a produite.

## Mesures

```python
from metallurgypy.precision import Measurement

m1 = Measurement(2.5, "%", 0.05)  # incertitude-type
m2 = Measurement(2.5, "%", 0.1, kind="expanded", coverage_factor=2.0)
m3 = Measurement(10.0, "g/L", 0.2, kind="rectangular")  # demi-largeur de l'intervalle
m4 = Measurement.from_replicates([2.48, 2.52, 2.51], "%")  # type A : s / racine(n)
print(m1.standard_uncertainty, m2.standard_uncertainty)
```

`kind` vaut `standard`, `expanded` (exige `coverage_factor`), `rectangular` (\(u = a/\sqrt{3}\)) ou `triangular` (\(u = a/\sqrt{6}\)). Tout est converti en incertitude-type, dans l'unité de la valeur.

## Propagation au premier ordre (GUM)

`propagate_model(modèle, mesures, correlations=None)` applique la loi de propagation des incertitudes (JCGM 100:2008, équation 13) :

\[
u_c^2(y) = \sum_i \sum_j \frac{\partial f}{\partial x_i}\frac{\partial f}{\partial x_j}\,u(x_i)\,u(x_j)\,r_{ij}
\]

- Les dérivées sont des **différences finies centrées** du modèle enregistré : tous les modèles sont donc pris en charge sans formule séparée. Un pas qui sort du domaine du modèle est signalé, jamais caché.
- `correlations` est un dictionnaire `{("a", "b"): r}`. La matrice de corrélation doit être semi-définie positive (vérifiée par une décomposition de Cholesky), sinon l'appel échoue.
- Chaque sortie donne son incertitude-type, sa sensibilité à chaque entrée et la **contribution de chaque entrée à la variance** (la somme vaut 1 ; avec des entrées corrélées une part peut être négative).
- Des avertissements sont ajoutés quand l'incertitude relative d'une entrée dépasse 10 % (le premier ordre devient douteux) et quand la valeur nominale est au bord du domaine du modèle (dérivée unilatérale).

**Limites.** La méthode est du premier ordre : fiable pour de petites incertitudes relatives et des modèles réguliers, elle peut se tromper près d'une singularité (division par une grandeur qui peut tendre vers zéro) ou pour de grandes incertitudes. Recoupez avec Monte Carlo.

## Exemple

Les nombres sont **fictifs**.

```python
from metallurgypy.precision import (
    Measurement,
    format_with_uncertainty,
    monte_carlo,
    propagate_model,
)

mesures = {
    "feed_mass": Measurement(1000, "t", 5),  # incertitude-type 5 t
    "feed_grade": Measurement(2.5, "%", 0.05),  # ± 0,05 point de pourcentage
    "recovery": Measurement(92, "%", 1.0),
}

u = propagate_model("mass_balance.recovery", mesures)
metal = u.outputs["metal_recovered"]
print(format_with_uncertainty(metal.value, metal.standard_uncertainty), metal.unit)
# 23.00(54) t

for nom, part in sorted(metal.contributions.items(), key=lambda kv: -kv[1]):
    print(f"{nom}: {part:.0%} de la variance")
```

La valeur s'écrit `23.00(54)` : 23,00 t avec une incertitude-type de 0,54 t (facteur d'élargissement k = 1). La teneur contribue pour environ 74 % de la variance et la récupération pour 22 % : mieux analyser la teneur réduirait davantage l'incertitude qu'une pesée plus précise.

## Recoupement par Monte Carlo

La méthode du premier ordre est une approximation. On la contrôle par échantillonnage :

```python
mc = monte_carlo("mass_balance.recovery", mesures, samples=20_000, seed=42)
echantillon = mc.outputs["metal_recovered"]
print(echantillon.standard_deviation, metal.standard_uncertainty)
assert abs(echantillon.standard_deviation - metal.standard_uncertainty) < 0.05
```

`monte_carlo` échantillonne des entrées **normales** (avec les corrélations demandées) et relance le modèle. `seed` est obligatoire pour que les résultats soient reproductibles. Les tirages hors du domaine sont comptés dans `rejected`, pas écartés en silence. Pour ce modèle presque linéaire, les deux méthodes concordent ; si elles divergent nettement, faites confiance au Monte Carlo.

## Sensibilité

- `sensitivity_coefficients` donne la dérivée locale et l'élasticité sans dimension \(\frac{x}{y}\frac{\partial y}{\partial x}\) de chaque sortie par rapport à chaque entrée.
- `one_at_a_time` fait varier chaque entrée seule de ±10 % (réglable) et note toutes les sorties : il montre les effets non linéaires que la dérivée cache.

## Présenter un résultat avec son incertitude

`format_with_uncertainty(valeur, u)` suit la convention du GUM : l'incertitude est arrondie à deux chiffres significatifs et la valeur à la même décimale, d'où `23.00(54)`. `round_sig` et `format_sig` arrondissent aux chiffres significatifs **pour la présentation seulement** ; les valeurs enregistrées ne sont jamais arrondies.

## Constantes

Seules les constantes **exactes par définition** sont intégrées : \(N_A\), \(e\) et \(k_B\) de la redéfinition du SI de 2019. La constante de Faraday \(F = N_A e\) et la constante des gaz \(R = N_A k_B\) en sont dérivées. Les constantes mesurées, qui ont une incertitude, ne sont pas fournies.

## Dans Studio

Dans l'espace de calcul, saisissez l'incertitude-type à côté d'une valeur (même unité). Studio affiche une colonne « Std. uncertainty » et un budget d'incertitude dans les détails, et enregistre les incertitudes dans le fichier de calcul.
