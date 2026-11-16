# Audit scientifique et sécurité

Un état honnête de ce qui a été vérifié et de ce qui ne l'a pas été. À lire avant de s'appuyer sur un résultat.

## Ce que « vérifié » veut dire ici

Pour chaque modèle, les tests comparent l'implémentation avec :

1. des **calculs à la main** faits séparément du code ;
2. des **limites analytiques** (par exemple : un étage de Kremser égale la formule d'un étage ; \(\varphi = 1/(N+1)\) quand \(E = 1\) ; l'extraction est plafonnée à \(1-E\) pour \(E<1\) ; un acide très faible et très dilué donne un pH de 7 ; un acide très fort se comporte comme totalement dissocié) ;
3. la **fermeture et la cohérence** (les bilans de matière et de métal se ferment ; les allers-retours, comme « étages requis » puis Kremser, retrouvent la cible) ;
4. les **entrées invalides et les bords du domaine** (négatif, zéro, non fini, hors plage, mauvaises unités).

Cela montre que le code implémente correctement les équations annoncées. Cela ne montre **pas** que ces équations décrivent une usine, un minerai ou un système chimique donné.

## Ce qui n'a *pas* été vérifié

- **Aucune comparaison avec des données expérimentales ou d'usine.** Aucun résultat de validation sur des mesures n'est revendiqué.
- **Aucune relecture scientifique indépendante.** Les équations sont des relations classiques de manuel, écrites d'après les connaissances de l'auteur. Un expert du domaine doit relire chaque page. Les références bibliographiques n'ont **pas** été ajoutées ni vérifiées ; aucune n'est inventée.
- **Aucune comparaison avec un autre logiciel** (simulateur de procédés, base de données thermodynamiques).
- **Studio n'a pas été lancé** sur un vrai écran par l'auteur du code. Sa logique est testée sans Qt ; les widgets ne sont exercés que par le job de la CI.
- **Les workflows GitHub Actions** ont été validés localement (syntaxe, étapes rejouées à la main) mais **n'ont pas été exécutés sur GitHub** par l'auteur.
- **Python 3.10** : la syntaxe est vérifiée, mais les tests n'y ont pas tourné localement (3.11 à 3.13 oui).

Les contrôles `ruff` (lint et format), `mypy --strict` et la construction stricte de la documentation passent.

## État modèle par modèle

| Module | Famille d'équations | Vérifié contre | Principale limite scientifique |
|---|---|---|---|
| Bilan de matière | Bilan de métal et à deux produits | Calcul à la main, fermeture, recoupement en arithmétique exacte | Teneurs prises comme exactes en mode standard ; les analyses réelles rendent rendement et récupération incertains |
| Réactifs | Dilution, conversion massique/molaire, dosage × débit | Calcul à la main | Volumes supposés additifs ; dosages, pureté et débit fournis par l'utilisateur |
| Électrolyse | Loi de Faraday, rendement de courant, énergie | Formule de référence avec les constantes exactes du SI, énergie et densité de courant calculées à la main | Courant constant ; rendement et tension fournis par l'utilisateur |
| Flottation | Bilan à deux produits, cinétique du premier ordre | Calcul à la main, limites (\(t\to\infty\)) | Une seule constante de vitesse ; paramètres empiriques propres au minerai |
| Filtration | Gâteau incompressible à pression constante | Calcul à la main | Gâteau incompressible seulement ; \(\alpha\) et \(R_m\) fournis par l'utilisateur |
| Hydrométallurgie | Rendement, cinétique du premier ordre, neutralisation stœchiométrique, précipitation | Calcul à la main, fermeture | Stœchiométrique/empirique ; ni spéciation ni mécanisme |
| Extraction par solvant | Un étage, Kremser, étages requis, McCabe–Thiele | Calcul à la main, limites analytiques, aller-retour. Le pas à pas de McCabe–Thiele est comparé à Kremser pour une isotherme linéaire à environ 8 % près, car le dernier étage est proratisé linéairement | \(D\) constant (isotherme linéaire) ; étages d'équilibre, sans rendement |
| Thermodynamique | \(\Delta G\), \(K\) ; pH idéal | Calcul à la main (pH d'un acide faible : 2,883), limites, résidu du bilan de charge, convergence de la bissection | Solutions idéales ; \(\Delta H\) et \(\Delta S\) constants |
| Incertitude | GUM premier ordre, Monte Carlo | Cas analytiques (produits, sommes), accord avec Monte Carlo, gestion des corrélations | Premier ordre ; entrées normales en Monte Carlo ; exclut l'erreur du modèle |
| Statistiques | Outils descriptifs usuels | Valeurs calculées à la main et cas d'erreur | Descriptif seulement |

## Constantes et données

Seules les constantes exactes par définition sont incluses (\(N_A\), \(e\), \(k_B\) du SI 2019 ; \(F\) et \(R\) dérivées). Aucune table thermodynamique, donnée d'extractant, constante de vitesse ou dosage de réactif n'est fournie. Les valeurs d'exemple de l'interface et de la documentation sont signalées comme fictives.

## Avant d'utiliser un résultat pour une décision

1. Lisez les hypothèses du modèle sur sa page.
2. Vérifiez que vos conditions sont dans son domaine de validité.
3. Comparez avec au moins une mesure ou un calcul indépendant.
4. Propagez l'incertitude de vos entrées et regardez laquelle domine.

## Revue de sécurité

Il s'agit d'une auto-revue du code de ce dépôt, faite par lecture, recherche dans les sources et tests. Ce **n'est pas** un audit indépendant ni un test d'intrusion.

**Modèle de menace.** MetallurgyPy est une bibliothèque et une application locales : aucune connexion réseau, aucun serveur, aucun identifiant. Les risques réalistes sont les **fichiers non fiables** (projet, calcul ou données reçus d'autrui) et le **texte non fiable** (noms, notes, en-têtes de colonnes) qui finit dans un fichier exporté.

| Sujet | Constat |
|---|---|
| Exécution de code depuis un fichier | Aucune. Un fichier de calcul est du JSON ; le rouvrir cherche le modèle par `model_id` dans un registre fixe et le relance avec les nombres enregistrés. Pas de `eval`, `exec`, `pickle`, `marshal`, `subprocess` ni `os.system` dans `src/` ou `studio/`. |
| Fichiers de calcul ou de projet malformés | Rejetés avec une erreur claire (`RecordFormatError`, `ProjectError`). |
| Traversée de chemin dans les projets | Une entrée d'index qui pointe hors de `calculations/` est refusée avant lecture. |
| Archives | Seule l'écriture d'archives zip existe, avec des noms relatifs fixes ; rien n'en extrait, donc pas de « zip-slip ». |
| Écrasement de données | Tout écrivain refuse d'écraser un fichier existant sans `overwrite=True` ; l'écriture est atomique ; les fichiers sources ne sont que lus. |
| SQL | Le seul SQL est l'historique du projet, avec des paramètres liés. |
| Rapports HTML | Tout texte contrôlé par l'utilisateur est échappé. |
| Injection de formules (tableur) | Les cellules de texte qui commencent par `=`, `+`, `-` ou `@` reçoivent une apostrophe en tête dans les CSV exportés. |
| Nombres non finis | NaN et l'infini sont refusés en entrée et à l'écriture JSON. |

**Limites connues.** Les fichiers `.xlsx` sont lus avec `openpyxl` en lecture seule (formules non évaluées, macros non exécutées), mais un classeur énorme ou forgé peut consommer beaucoup de mémoire ou de temps ; il n'y a pas de limite de taille, ni pour les CSV et JSON. Aucune analyse des dépendances (`pip-audit`) n'a été faite. Studio n'a pas été lancé dans l'environnement de développement. Rien n'est publié sur PyPI : une future publication demandera un éditeur de confiance (*trusted publisher*) et des étiquettes signées, non configurés. Qt et PySide6 eux-mêmes ne sont pas revus.

Pour signaler une faille, ouvrez un avis de sécurité privé sur le dépôt GitHub ou contactez la personne responsable, plutôt qu'un ticket public.
