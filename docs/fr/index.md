# MetallurgyPy

*Engineering Metallurgy with Python* : la métallurgie de l'ingénieur avec Python.

MetallurgyPy est une bibliothèque scientifique libre pour les calculs de procédés métallurgiques, accompagnée d'une application de bureau pour celles et ceux qui préfèrent les formulaires et les graphiques aux scripts.

!!! info "Documentation en français"
    Cette section est la version française de la documentation. Le code, l'API et les messages d'erreur sont en anglais. Les pages de référence détaillées (tableaux générés depuis le code, référence de l'API) restent en anglais : elles sont liées là où c'est utile.

!!! warning "Statut du projet : développement précoce (0.2.0.dev0)"
    Tous les modules prévus, la propagation d'incertitude, l'import de données, la comparaison, les rapports, les projets et **Studio** sont écrits et testés. Mais les modèles sont simplifiés et **n'ont pas été validés sur des données expérimentales ou d'usine**, et Studio n'a pas encore été lancé sur un vrai écran par l'auteur du code. Voir l'[audit scientifique](audit.md). Rien n'est publié sur PyPI.

## Deux produits, un seul moteur

| Produit | Ce que c'est | Installation |
|---|---|---|
| **MetallurgyPy Core** | Bibliothèque Python : unités, validation, résultats traçables, modèles de procédé. Fonctionne sur un serveur ou dans un notebook, sans dépendance graphique. | `pip install -e .` |
| **MetallurgyPy Studio** | Application de bureau PySide6 : formulaires, tableaux, graphiques interactifs, projets, rapports. Elle appelle l'API publique du Core et ne réécrit jamais une équation. | `pip install -e ".[gui]"` |

## Ce que couvre la bibliothèque

- Bilans de matière et bilans métallurgiques
- Hydrométallurgie : lixiviation, dissolution, précipitation, neutralisation
- Extraction par solvant et stripping
- Électrolyse (electrowinning)
- Flottation et filtration
- Dosage et consommation de réactifs
- Thermodynamique et équilibres chimiques
- Statistiques et visualisation

## Principes de conception

1. **Chaque équation est documentée**, avec ses hypothèses et son domaine de validité.
2. **Les unités sont vérifiées**, pas supposées.
3. **Aucune donnée inventée.** Les constantes, les données de référence et les résultats de validation ont toujours une source indiquée.
4. **Trois notions ne sont jamais confondues** : précision numérique, incertitude de mesure et exactitude du modèle. Voir [Précision et incertitude](precision.md).
5. **Les modèles simplifiés sont présentés comme tels.** MetallurgyPy n'est pas un simulateur industriel validé et ne remplace pas un DCS, un automate ou un SCADA.
6. **Les résultats sont traçables** : entrées, version du modèle, méthode, hypothèses, avertissements et version du logiciel accompagnent chaque résultat.

## Pour commencer

- [Installer la bibliothèque](installation.md)
- [Faire un premier calcul](demarrage.md)
- [Comprendre les concepts](concepts.md) : unités, résultats, fichiers
- [Parcourir les méthodes scientifiques](modules.md)
- [Propager l'incertitude](precision.md)
- [Utiliser Studio](studio.md) et [importer, comparer, produire un rapport](flux.md)
- [Audit scientifique](audit.md), [FAQ](faq.md), [contribuer](contribuer.md)
