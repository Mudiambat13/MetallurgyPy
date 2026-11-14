# MetallurgyPy — Cahier des charges technique
## Bibliothèque scientifique Python avec interface graphique de visualisation

**Nom du projet :** MetallurgyPy  
**Nom du package Python :** `metallurgypy`  
**Slogan :** *Engineering Metallurgy with Python*  
**Type :** Bibliothèque scientifique open source + application graphique de bureau  
**Licence proposée :** MIT  
**Langue du code et de l'API :** anglais  
**Documentation initiale :** anglais, avec possibilité de traduction française  
**Public cible :** ingénieurs métallurgistes, ingénieurs procédés, laboratoires, chercheurs, enseignants et étudiants.

---

# 1. Mission de l'agent IA

Tu es un architecte logiciel senior Python, spécialisé en calcul scientifique, génie métallurgique, hydrométallurgie, visualisation de données et applications desktop.

Ta mission est de concevoir et développer **MetallurgyPy**, un écosystème composé de deux produits clairement séparés :

1. **MetallurgyPy Core** : bibliothèque Python destinée aux calculs scientifiques et métallurgiques.
2. **MetallurgyPy Studio** : interface graphique de bureau permettant de préparer des calculs, visualiser les résultats, explorer les données et exporter des rapports.

Le moteur scientifique doit fonctionner sans interface graphique. L'application graphique doit utiliser les API publiques du moteur, sans réimplémenter les équations scientifiques.

Ne développe pas tous les modules simultanément. Travaille par phases, teste chaque livraison et conserve le dépôt dans un état fonctionnel.

## Règles impératives

- Utiliser Python moderne, le typage statique et des API cohérentes.
- Séparer strictement le moteur scientifique, les données, la visualisation et l'interface graphique.
- Documenter chaque équation, chaque hypothèse et le domaine de validité de chaque modèle.
- Vérifier les unités et dimensions physiques.
- Ne jamais inventer de constantes, de données expérimentales ou de résultats de validation.
- Distinguer précision numérique, exactitude du modèle et incertitude des mesures.
- Ne jamais présenter un modèle simplifié comme une simulation industrielle validée.
- Signaler les avertissements, les échecs de convergence et les données manquantes.
- Ne pas arrondir les valeurs intermédiaires sans justification.
- Ne pas lancer de publication PyPI sans approbation explicite du propriétaire.
- Ne pas ajouter de dépendance sans justification technique.
- Avant de modifier un fichier existant, l'inspecter et préserver les fonctionnalités déjà validées.

---

# 2. Vision et périmètre

MetallurgyPy doit fournir des outils reproductibles pour les calculs et analyses des procédés métallurgiques :

- bilans massiques et métallurgiques ;
- préparation et analyse des solutions ;
- lixiviation, dissolution et précipitation ;
- extraction par solvant (SX) et stripping ;
- électrolyse et électro-obtention (electrowinning) ;
- flottation ;
- filtration et humidité des gâteaux ;
- dosage et consommation des réactifs ;
- thermodynamique et équilibres chimiques ;
- statistiques, analyse de données et visualisation.

L'interface MetallurgyPy Studio doit rendre ces outils accessibles aux utilisateurs qui ne souhaitent pas écrire du code pour chaque calcul. Elle ne doit toutefois pas cacher les hypothèses scientifiques ni les paramètres utilisés.

## Hors périmètre initial

- Remplacer un système DCS, PLC ou SCADA.
- Piloter directement des équipements industriels.
- Fournir des consignes opératoires de sécurité.
- Garantir des performances industrielles sans validation expérimentale.
- Remplacer un logiciel de simulation de procédés rigoureusement calibré.

Les connexions à des systèmes industriels, l'acquisition en temps réel et les fonctions de contrôle sont exclues du MVP.

---

# 3. Architecture générale

Adopter une architecture en couches :

```text
┌──────────────────────────────────────────────────────────┐
│                 MetallurgyPy Studio                      │
│  Interface PySide6 : formulaires, tableaux, graphiques   │
└────────────────────────────┬─────────────────────────────┘
                             │ API publique
┌────────────────────────────▼─────────────────────────────┐
│                 Application Services                    │
│  Cas d'utilisation, orchestration, validation, rapports  │
└────────────────────────────┬─────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────┐
│                  MetallurgyPy Core                       │
│  Bilans, hydrométallurgie, SX, EW, flottation, etc.       │
└────────────────────────────┬─────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────┐
│           Scientific & Numerical Foundations             │
│ NumPy, SciPy, Pint, uncertainties, SymPy, Pandas         │
└──────────────────────────────────────────────────────────┘
```

## Principe fondamental

Le package `metallurgypy` doit pouvoir être installé et utilisé sur un serveur ou dans un notebook sans installer PySide6.

L'interface graphique doit être une dépendance optionnelle :

```bash
pip install metallurgypy
pip install "metallurgypy[gui]"
```

Prévoir aussi des extras optionnels pour les fonctionnalités avancées :

```bash
pip install "metallurgypy[visualization]"
pip install "metallurgypy[uncertainty]"
pip install "metallurgypy[all]"
```

---

# 4. Modules scientifiques

## 4.1 Core

Package : `metallurgypy.core`

Responsabilités :

- gestion des unités et conversions ;
- validation des entrées ;
- constantes physiques documentées ;
- exceptions personnalisées ;
- objets de résultats ;
- métadonnées et traçabilité ;
- conventions numériques communes.

Exceptions minimales :

- `MetallurgyPyError`
- `InvalidParameterError`
- `UnitConversionError`
- `DimensionError`
- `CalculationError`
- `ConvergenceError`
- `ModelDomainError`

## 4.2 Mass Balance

Package : `metallurgypy.mass_balance`

Fonctionnalités :

- bilans massiques globaux et par composant ;
- bilans solides/liquides ;
- teneurs et masses métalliques ;
- récupération et pertes ;
- rendement massique ;
- bilans multi-flux ;
- fermeture de bilan et écarts de réconciliation.

Exemple d'API indicative :

```python
from metallurgypy.mass_balance import MassBalance

balance = MassBalance(
    feed_mass=1000,
    feed_grade=0.025,
    recovery=0.92,
)

result = balance.calculate()

print(result.metal_recovered)
print(result.metal_remaining)
print(result.recovery)
```

Les unités, la base de calcul, le caractère massique ou volumique des teneurs et les conventions doivent être explicites. Une récupération ne doit pas être confondue avec un rendement massique.

## 4.3 Hydrometallurgy

Package : `metallurgypy.hydrometallurgy`

Fonctionnalités :

- lixiviation ;
- dissolution ;
- précipitation ;
- neutralisation ;
- bilans solides/liquides ;
- concentration des solutions ;
- rendement d'extraction ;
- cinétique de réaction.

Classes candidates :

- `LeachingModel`
- `PrecipitationModel`
- `NeutralizationModel`
- `DissolutionModel`
- `SolutionAnalysis`

Distinguer les calculs stœchiométriques, les modèles d'équilibre et les modèles cinétiques. Ne pas supposer qu'une cinétique simplifiée représente tous les minerais ou toutes les conditions opératoires.

## 4.4 Solvent Extraction

Package : `metallurgypy.solvent_extraction`

Fonctionnalités :

- coefficient de distribution ;
- rapports O/A et A/O ;
- isothermes d'extraction et de stripping ;
- calculs d'étages théoriques ;
- circuits mixer-settler ;
- bilans de phases ;
- scénarios de circuits.

Classes candidates :

- `DistributionCoefficient`
- `ExtractionStage`
- `StrippingStage`
- `SXCircuit`
- `McCabeThieleAnalysis`

Les modèles doivent permettre de préciser le système chimique, les données d'équilibre et les hypothèses. Ne pas coder de comportement universel pour un extractant donné.

## 4.5 Electrowinning

Package : `metallurgypy.electrowinning`

Fonctionnalités :

- loi de Faraday ;
- rendement faradique ;
- masse déposée ;
- densité de courant ;
- surface cathodique ;
- production théorique ;
- consommation énergétique.

Classes candidates :

- `ElectrolysisModel`
- `CurrentEfficiency`
- `CathodeProduction`
- `EnergyConsumption`

Différencier production théorique et production réelle. Rendre visibles les hypothèses sur le rendement, les pertes et les conditions électriques.

## 4.6 Flotation

Package : `metallurgypy.flotation`

Fonctionnalités :

- récupération ;
- rendement massique ;
- enrichissement ;
- bilans concentré/rejet ;
- analyses de teneurs ;
- cinétique de flottation.

## 4.7 Filtration

Package : `metallurgypy.filtration`

Fonctionnalités :

- débit de filtration ;
- résistance du gâteau ;
- résistance du média ;
- humidité du gâteau ;
- temps de filtration ;
- modèles de filtration sous pression.

## 4.8 Reagents

Package : `metallurgypy.reagents`

Fonctionnalités :

- dosage ;
- consommation spécifique ;
- préparation et dilution des solutions ;
- concentrations massiques et molaires ;
- consommation par tonne de minerai ;
- consommation horaire, journalière et par campagne.

Les exemples de réactifs peuvent inclure acide sulfurique, chaux, soude caustique, floculants, extractants, oxydants et réducteurs. Les dosages doivent toujours provenir de l'utilisateur ou d'une source explicitement documentée.

## 4.9 Thermodynamics

Package : `metallurgypy.thermodynamics`

Fonctionnalités progressives :

- énergie libre de Gibbs ;
- constantes d'équilibre ;
- équilibres acido-basiques ;
- calculs de pH selon les hypothèses ;
- réactions chimiques ;
- dissolution et précipitation ;
- résolution d'équilibres avec SciPy et SymPy.

Documenter les données thermodynamiques, leur source, leur température de référence et leur domaine de validité.

## 4.10 Statistics

Package : `metallurgypy.statistics`

Fonctionnalités :

- statistiques descriptives ;
- régression ;
- corrélations ;
- détection d'anomalies ;
- séries temporelles ;
- analyse de variabilité ;
- indicateurs de performance ;
- analyse de sensibilité.

---

# 5. Précision numérique, incertitudes et métrologie

La précision scientifique est une exigence centrale.

## 5.1 Trois notions à ne pas confondre

1. **Précision numérique** : comportement des algorithmes et erreurs d'arrondi.
2. **Incertitude de mesure** : dispersion ou incertitude des données d'entrée.
3. **Exactitude du modèle** : capacité du modèle physique ou chimique à représenter le procédé réel.

Un résultat affiché avec 12 décimales n'est pas nécessairement exact.

## 5.2 Modes de calcul

Prévoir trois modes explicites :

- `standard` : calcul scientifique usuel en `float64`.
- `high_precision` : méthodes de précision renforcée lorsque justifiées et disponibles.
- `uncertainty_aware` : propagation des incertitudes des mesures.

Ne pas promettre une précision supérieure lorsque l'algorithme, la plateforme ou les données ne la garantissent pas. `numpy.longdouble` dépend de la plateforme ; son comportement doit être détecté et documenté.

## 5.3 Outils

- NumPy : calcul vectoriel et `float64`.
- Decimal : opérations décimales où elles sont pertinentes.
- SymPy : calcul symbolique exact.
- SciPy : méthodes numériques et convergence.
- Pint : unités et dimensions.
- uncertainties : propagation d'incertitudes, si compatible avec le modèle.

Ne pas mélanger silencieusement des types numériques incompatibles.

## 5.4 Mesures

Créer un objet `Measurement` contenant au minimum :

- valeur ;
- unité ;
- incertitude ;
- type d'incertitude (standard, élargie ou autre) ;
- facteur de couverture si applicable ;
- origine ou méthode de mesure, si fournie ;
- horodatage facultatif.

Prendre en charge les incertitudes indépendantes et, lorsque les données le permettent, les corrélations.

## 5.5 Validation numérique

- Tolérances absolues et relatives configurables.
- Comparaisons approchées.
- Contrôle des divisions par zéro.
- Contrôle des valeurs non finies.
- Détection des problèmes de conditionnement lorsque pertinent.
- Critères d'arrêt et convergence documentés.
- Conservation des valeurs non arrondies dans les résultats.
- Arrondi uniquement pour la présentation, sauf règle scientifique explicitement justifiée.

## 5.6 Traçabilité

Chaque résultat important doit pouvoir exposer :

- entrées et unités ;
- formule ou modèle utilisé ;
- version du modèle ;
- méthode numérique ;
- hypothèses ;
- incertitudes ;
- avertissements ;
- tolérances ;
- statut de convergence ;
- date et version de MetallurgyPy.

---

# 6. Interface graphique — MetallurgyPy Studio

## 6.1 Choix technologique

Créer une application desktop multiplateforme avec :

- **PySide6** : interface Qt native ;
- **pyqtgraph** : graphiques interactifs et affichage de séries volumineuses ;
- **Matplotlib** : graphiques scientifiques destinés à l'export et aux publications ;
- **Pandas** : tableaux et import/export de données ;
- **qt-material** ou feuilles de style Qt personnalisées : thème visuel, uniquement si cela n'alourdit pas inutilement le projet.

L'interface doit fonctionner sous Windows et Linux. Garder la compatibilité macOS possible.

Ne pas utiliser Streamlit comme interface principale : le produit attendu est une application de bureau. Une interface web pourra être envisagée dans une version future.

## 6.2 Identité visuelle

Créer une interface moderne, professionnelle et adaptée à un logiciel scientifique industriel.

Direction visuelle :

- thème clair et thème sombre ;
- navigation latérale ;
- barre supérieure avec nom du projet et état du calcul ;
- espace de travail central ;
- panneaux de paramètres et résultats ;
- typographie lisible ;
- unités visibles à proximité des valeurs ;
- couleurs sobres avec contrastes accessibles ;
- icônes cohérentes ;
- tableaux avec tri, filtres et export.

Nom affiché : **MetallurgyPy Studio**.

Ne pas copier l'interface d'un logiciel commercial existant.

## 6.3 Écrans principaux

### A. Dashboard

Afficher :

- bienvenue et version du logiciel ;
- accès rapide aux modules ;
- derniers projets ouverts ;
- derniers calculs ;
- état des tâches de calcul ;
- raccourcis vers les tutoriels et exemples ;
- avertissements scientifiques importants, le cas échéant.

Les indicateurs du dashboard doivent provenir de données réelles du projet. Ne pas afficher de fausses statistiques industrielles.

### B. Module Explorer

Présenter les modules scientifiques sous forme de navigation :

- Mass Balance
- Hydrometallurgy
- Solvent Extraction
- Electrowinning
- Flotation
- Filtration
- Reagents
- Thermodynamics
- Statistics

Chaque module doit présenter une courte description, les modèles disponibles et un accès à la documentation.

### C. Calculation Workspace

Créer un espace de calcul commun :

- sélection du modèle ;
- formulaire d'entrée dynamique ;
- unités explicites ;
- validation avant exécution ;
- bouton Calculate ;
- affichage des résultats ;
- messages d'erreur compréhensibles ;
- avertissements et hypothèses ;
- sauvegarde du calcul dans le projet.

Ne pas coder un formulaire différent de manière arbitraire pour chaque modèle : concevoir des composants réutilisables et des schémas de paramètres.

### D. Results Explorer

Présenter :

- résultats numériques ;
- tableaux ;
- graphiques ;
- incertitudes ;
- comparaison de scénarios ;
- détails de calcul ;
- export CSV, JSON et Excel lorsque disponible ;
- export PDF des rapports.

Les valeurs calculées, les valeurs estimées et les valeurs mesurées doivent être visuellement distinguées.

### E. Scientific Visualization

Fournir des graphiques interactifs adaptés aux procédés :

- courbes de récupération ;
- évolution de la teneur ;
- cinétique de lixiviation ;
- évolution du pH ;
- consommation des réactifs ;
- courbes d'extraction et de stripping ;
- diagrammes de bilan ;
- graphiques de filtration ;
- séries temporelles ;
- nuages de points et régressions ;
- intervalles d'incertitude lorsque disponibles.

Fonctions attendues :

- zoom et déplacement ;
- affichage des coordonnées ;
- légendes ;
- choix des séries ;
- choix des unités ;
- export PNG et SVG ;
- export des données sous-jacentes ;
- indication de la provenance des données.

Ne jamais inventer de courbe ou de donnée pour remplir un graphique. Les exemples doivent être clairement marqués comme données fictives ou pédagogiques.

### F. Data Import

Prendre en charge progressivement :

- CSV ;
- XLSX ;
- JSON.

Prévoir :

- aperçu avant import ;
- choix du séparateur CSV ;
- association des colonnes ;
- détection des types ;
- sélection des unités ;
- validation des données ;
- rapport sur les lignes invalides.

Ne jamais écraser un fichier source sans confirmation.

### G. Project Manager

Permettre :

- créer un projet ;
- ouvrir et enregistrer un projet ;
- enregistrer les paramètres et résultats ;
- ajouter des notes ;
- organiser les calculs ;
- comparer plusieurs scénarios ;
- exporter une archive de projet.

Utiliser un format de projet versionné, documenté et migrable. SQLite peut être utilisé pour les métadonnées et l'historique ; les données tabulaires volumineuses peuvent être stockées séparément.

### H. Report Builder

Créer des rapports contenant :

- titre et informations du projet ;
- objectif du calcul ;
- données d'entrée ;
- unités ;
- équations et modèles ;
- hypothèses ;
- résultats ;
- graphiques ;
- incertitudes ;
- avertissements ;
- date et version du logiciel.

Formats initiaux : PDF, HTML et CSV/Excel pour les données.

Un rapport doit distinguer clairement les résultats de calcul des observations expérimentales.

### I. Settings

Prévoir :

- langue de l'interface ;
- thème clair/sombre ;
- précision d'affichage ;
- unités par défaut ;
- emplacement des projets ;
- préférences d'export ;
- paramètres de calcul et tolérances, avec valeurs documentées.

La précision d'affichage ne doit jamais modifier les valeurs conservées dans le moteur.

---

# 7. Architecture logicielle de l'interface

Utiliser une architecture de type Model-View-ViewModel ou une séparation équivalente adaptée à Qt.

Principes :

- les widgets ne contiennent pas les équations scientifiques ;
- les services applicatifs appellent les API de MetallurgyPy Core ;
- les tâches longues s'exécutent hors du thread graphique avec les mécanismes Qt adaptés ;
- l'interface reste réactive ;
- les erreurs sont converties en messages utiles sans perdre les détails techniques dans les journaux ;
- les résultats peuvent être testés sans démarrer l'interface.

Prévoir un registre de modèles permettant à l'interface de découvrir les calculateurs disponibles à partir de métadonnées contrôlées.

Ne pas exécuter du code Python arbitraire provenant d'un projet importé.

---

# 8. Arborescence proposée

```text
MetallurgyPy/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── .gitignore
│
├── src/
│   └── metallurgypy/
│       ├── __init__.py
│       ├── version.py
│       ├── core/
│       │   ├── units.py
│       │   ├── constants.py
│       │   ├── exceptions.py
│       │   ├── validation.py
│       │   ├── results.py
│       │   └── provenance.py
│       ├── precision/
│       │   ├── numerical.py
│       │   ├── uncertainty.py
│       │   ├── measurements.py
│       │   ├── tolerances.py
│       │   ├── significant_figures.py
│       │   └── sensitivity.py
│       ├── mass_balance/
│       ├── hydrometallurgy/
│       ├── solvent_extraction/
│       ├── electrowinning/
│       ├── flotation/
│       ├── filtration/
│       ├── reagents/
│       ├── thermodynamics/
│       ├── statistics/
│       └── visualization/
│
├── studio/
│   └── metallurgypy_studio/
│       ├── __init__.py
│       ├── main.py
│       ├── app.py
│       ├── resources/
│       │   ├── icons/
│       │   └── styles/
│       ├── views/
│       │   ├── dashboard/
│       │   ├── modules/
│       │   ├── workspace/
│       │   ├── results/
│       │   ├── data_import/
│       │   ├── projects/
│       │   ├── reports/
│       │   └── settings/
│       ├── viewmodels/
│       ├── services/
│       ├── widgets/
│       └── workers/
│
├── tests/
│   ├── core/
│   ├── precision/
│   ├── mass_balance/
│   ├── hydrometallurgy/
│   ├── solvent_extraction/
│   ├── electrowinning/
│   ├── gui/
│   └── integration/
│
├── examples/
│   ├── mass_balance/
│   ├── hydrometallurgy/
│   ├── solvent_extraction/
│   └── electrowinning/
│
├── docs/
│   ├── index.md
│   ├── installation.md
│   ├── getting_started.md
│   ├── scientific_methods/
│   ├── gui/
│   ├── api/
│   └── tutorials/
│
└── .github/
    └── workflows/
        ├── tests.yml
        ├── docs.yml
        └── publish.yml
```

Cette arborescence est une proposition initiale. L'agent doit la faire évoluer sans créer des dossiers vides ou des abstractions inutiles.

---

# 9. Stack technique et dépendances

| Outil | Rôle |
|---|---|
| Python | Langage principal |
| NumPy | Calcul numérique |
| SciPy | Méthodes scientifiques |
| Pandas | Données tabulaires |
| SymPy | Calcul symbolique |
| Pint | Unités physiques |
| Pydantic | Validation de données et schémas |
| uncertainties | Propagation des incertitudes |
| PySide6 | Interface desktop |
| pyqtgraph | Graphiques interactifs |
| Matplotlib | Graphiques scientifiques exportables |
| openpyxl | Export/import Excel |
| SQLite | Métadonnées et historique des projets |
| Pytest | Tests |
| Hypothesis | Tests basés sur les propriétés |
| Ruff | Lint et formatage |
| MyPy | Vérification statique des types |
| MkDocs | Documentation |

Organiser les dépendances dans `pyproject.toml` :

- dépendances minimales du Core ;
- extra `visualization` ;
- extra `uncertainty` ;
- extra `gui` ;
- extra `dev` ;
- extra `docs` ;
- extra `all`.

Vérifier les versions compatibles avant de les figer.

---

# 10. API publique et exemple d'utilisation

L'API doit rester utilisable sans GUI :

```python
from metallurgypy.mass_balance import MassBalance

calculation = MassBalance(
    feed_mass=1000,
    feed_grade=0.025,
    recovery=0.92,
)

result = calculation.calculate()

print(result.metal_recovered)
```

L'application graphique doit appeler le même service ou la même API publique.

Exemple de lancement de l'application :

```bash
metallurgypy-studio
```

Prévoir également un lancement de développement :

```bash
python -m metallurgypy_studio
```

L'entrée CLI doit être déclarée proprement dans `pyproject.toml`.

---

# 11. Tests et assurance qualité

## Tests du Core

- tests unitaires de chaque formule ;
- tests dimensionnels et de conversion ;
- tests de valeurs limites ;
- tests de valeurs invalides ;
- tests de convergence ;
- tests de propriétés ;
- tests de non-régression ;
- cas de référence documentés.

## Tests de précision

- comparaison avec des résultats de référence ;
- tolérances absolues et relatives justifiées ;
- tests de propagation d'incertitude ;
- tests des corrélations ;
- tests de stabilité numérique ;
- tests de formatage et chiffres significatifs.

## Tests de l'interface

- démarrage de l'application ;
- navigation ;
- validation des formulaires ;
- affichage des résultats ;
- affichage des avertissements ;
- import de données ;
- sauvegarde et réouverture de projets ;
- export des graphiques et rapports.

Les tests GUI doivent utiliser des données de test déterministes et ne doivent pas dépendre d'une connexion Internet.

Configurer GitHub Actions pour tester les versions de Python prises en charge et séparer les tests Core des tests GUI.

---

# 12. Documentation et expérience développeur

Créer une documentation MkDocs avec :

- installation ;
- démarrage rapide ;
- architecture ;
- guide de chaque module ;
- références mathématiques ;
- hypothèses et limites ;
- guide de l'interface ;
- tutoriels ;
- API Reference ;
- contribution ;
- FAQ.

Chaque modèle doit avoir une page scientifique expliquant ses équations et ses limites.

Fournir des exemples reproductibles avec jeux de données clairement identifiés.

---

# 13. Packaging et distribution

Le Core et Studio doivent pouvoir être installés proprement.

Commandes attendues :

```bash
pip install metallurgypy
pip install "metallurgypy[gui]"
```

Prévoir une commande de lancement `metallurgypy-studio`.

Vérifier la construction :

```bash
python -m build
python -m twine check dist/*
```

Prévoir une distribution desktop ultérieure avec un outil de packaging adapté à chaque système d'exploitation. Ne pas engager cette étape avant que l'application soit stable.

Publication PyPI uniquement après validation explicite.

---

# 14. Feuille de route

## Phase 0 — Conception

- confirmer les API ;
- confirmer les versions et dépendances ;
- établir les conventions d'unités ;
- rédiger les premières spécifications scientifiques ;
- valider l'architecture Core/Studio.

**Livrable :** architecture approuvée et dépôt initial.

## Phase 1 — Core Foundation

- packaging ;
- unités ;
- validation ;
- exceptions ;
- résultats ;
- traçabilité ;
- tests.

**Livrable :** Core minimal installable.

## Phase 2 — Premiers calculateurs

- Mass Balance ;
- Reagents ;
- premiers cas de référence ;
- exemples et documentation.

**Livrable :** premiers calculs utilisables et testés.

## Phase 3 — Précision et incertitudes

- Measurement ;
- propagation ;
- tolérances ;
- analyse de sensibilité ;
- traçabilité renforcée.

**Livrable :** calculs avec incertitudes documentées.

## Phase 4 — MetallurgyPy Studio MVP

- fenêtre principale ;
- navigation latérale ;
- dashboard ;
- workspace Mass Balance ;
- résultats et graphiques ;
- thème clair/sombre ;
- sauvegarde d'un calcul.

**Livrable :** application desktop utilisable avec le module Mass Balance.

## Phase 5 — Procédés métallurgiques

- Hydrometallurgy ;
- Solvent Extraction ;
- Electrowinning ;
- Flotation ;
- Filtration ;
- Reagents avancé.

**Livrable :** modules scientifiques testés et accessibles dans Studio.

## Phase 6 — Visualisation et rapports avancés

- import CSV/XLSX ;
- comparaison de scénarios ;
- visualisations avancées ;
- rapports PDF/HTML ;
- gestion des projets.

**Livrable :** environnement de travail scientifique complet.

## Phase 7 — Stabilisation et version 1.0

- audit scientifique et logiciel ;
- tests multiplateformes ;
- documentation ;
- packaging ;
- revue de sécurité ;
- publication après approbation.

---

# 15. Critères d'acceptation du MVP

Le MVP est accepté uniquement si :

1. Le Core s'installe sans PySide6.
2. L'installation `[gui]` installe l'application desktop.
3. Le moteur Mass Balance fonctionne depuis Python.
4. Le même calcul fonctionne depuis Studio.
5. Les unités sont contrôlées.
6. Les erreurs d'entrée sont expliquées.
7. Les résultats conservent leur précision interne.
8. Les hypothèses et avertissements sont visibles.
9. Les résultats peuvent être visualisés et exportés.
10. Un calcul peut être sauvegardé et rouvert.
11. Les tests automatiques passent.
12. La documentation explique les équations et les limites.

---

# 16. Première mission à exécuter par Claude Code ou Codex

Commence par lire ce document intégralement.

### Étape 1 — Analyse

Présente :

- architecture proposée ;
- risques techniques ;
- risques scientifiques ;
- choix des dépendances ;
- découpage des phases ;
- points nécessitant une décision.

Ne commence pas par générer tout le projet sans analyse.

### Étape 2 — Initialisation

Créer le dépôt, le `pyproject.toml`, les outils de qualité, les dossiers réellement nécessaires et les workflows CI.

### Étape 3 — Core

Développer les unités, les exceptions, les validations, les résultats et la traçabilité.

### Étape 4 — Premier calculateur

Développer Mass Balance avec :

- équations documentées ;
- unités explicites ;
- validation des entrées ;
- cas de référence ;
- tests ;
- exemples.

### Étape 5 — Première interface

Créer MetallurgyPy Studio avec PySide6 :

- fenêtre principale ;
- navigation latérale ;
- dashboard sobre ;
- workspace Mass Balance ;
- formulaire de saisie ;
- affichage des résultats ;
- graphique interactif ;
- thème clair et sombre.

Le calcul doit être exécuté par le Core, jamais recodé dans les widgets.

### Étape 6 — Persistance et export

Permettre de sauvegarder un calcul, de le rouvrir et d'exporter les résultats.

### Étape 7 — Validation

Exécuter les tests, construire le package et vérifier les deux modes d'installation :

```bash
pip install -e .
pip install -e ".[gui]"
```

Adapter ces commandes à la configuration réelle du projet.

### Étape 8 — Rapport

Fournir un rapport précisant :

- fichiers créés ;
- fonctionnalités terminées ;
- commandes exécutées ;
- tests réussis et échoués ;
- limites connues ;
- prochaine étape recommandée.

Ne prétends jamais qu'une fonctionnalité est terminée si elle n'a pas été exécutée et vérifiée.

---

# 17. Vision finale

MetallurgyPy doit réunir la rigueur d'une bibliothèque scientifique Python et l'accessibilité d'un logiciel graphique de calcul métallurgique.

Le projet doit permettre à un ingénieur de passer naturellement :

- d'un calcul manuel à un calcul reproductible ;
- d'une feuille Excel à un modèle scientifique documenté ;
- d'un résultat isolé à une analyse de procédé ;
- d'une série de mesures à une visualisation exploitable ;
- d'un script Python à une interface graphique professionnelle.

**MetallurgyPy — Engineering Metallurgy with Python.**
