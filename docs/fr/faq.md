# FAQ

**Puis-je utiliser MetallurgyPy sans l'interface graphique ?**
Oui. Le Core n'a pas de dépendance à PySide6 et fonctionne sur un serveur ou dans un notebook.

**Studio contient-il ses propres équations ?**
Non. Il appelle l'API publique du Core : un calcul donne le même résultat en Python et dans Studio.

**Est-ce un simulateur de procédés validé ?**
Non. Les modèles sont documentés et testés, mais des modèles simplifiés ne sont pas des simulations industrielles validées sur des données d'usine. Voir l'[audit scientifique](audit.md).

**Peut-il piloter ou surveiller mon usine ?**
Non. La connexion à un DCS, un automate ou un SCADA, l'acquisition en temps réel et la conduite sont hors périmètre.

**Pourquoi les résultats ont-ils autant de chiffres ?**
Le moteur garde la pleine précision et n'arrondit que pour l'affichage. Plus de chiffres ne veut pas dire plus d'exactitude : voir [Précision et incertitude](precision.md).

**D'où viennent les dosages de réactifs et les données d'équilibre ?**
De vous, ou d'une source explicitement documentée. MetallurgyPy ne les invente pas.

**Peut-il propager l'incertitude de mesure ?**
Oui : propagation GUM au premier ordre et recoupement par Monte Carlo, en Python et dans Studio. Cela couvre l'effet de l'incertitude des entrées à travers le modèle, pas l'erreur du modèle.

**Puis-je importer mes données ?**
Oui : CSV, JSON et Excel, avec des unités explicites et un rapport des lignes rejetées. Voir [Données, comparaison, rapports et projets](flux.md).

**Pourquoi le code et les messages sont-ils en anglais ?**
Le code, l'API et les messages d'erreur sont en anglais pour rester utilisables par une communauté internationale. La documentation existe en anglais et en français.

**Est-ce sur PyPI ?**
Pas encore. Une publication demande l'approbation explicite du propriétaire.
