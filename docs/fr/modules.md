# Méthodes scientifiques

Cette page résume, pour chaque module, **le périmètre, les équations, les hypothèses et les limites**. Les tableaux détaillés (paramètres, valeurs d'exemple, listes complètes d'hypothèses) sont générés depuis le code et restent en anglais : voir les [pages de référence](../scientific_methods/index.md).

!!! warning "Des modèles, pas des simulateurs validés"
    Un modèle simplifié n'est pas une simulation industrielle validée sur des données d'usine. Les implémentations sont vérifiées par des calculs à la main et des cas limites analytiques, **pas** par des données expérimentales. Voir l'[audit scientifique](audit.md). Utilisez les résultats comme des estimations d'ingénieur et confrontez-les à des mesures.

!!! note "Rien n'est inventé"
    Dosages, constantes d'équilibre, constantes de vitesse, coefficients de distribution ou résistances de gâteau ne sont **pas fournis** : ils viennent de vous, avec leur source. Seules les constantes exactes par définition (SI 2019) sont intégrées.

| Module | Modèles | Identifiants |
|---|---|---|
| [Bilan de matière](#bilan-de-matiere) | 2 | `mass_balance.recovery`, `mass_balance.two_product` |
| [Réactifs](#reactifs) | 3 | `reagents.dilution`, `.concentration_conversion`, `.consumption` |
| [Électrolyse](#electrolyse-electrowinning) | 1 | `electrowinning.faraday` |
| [Flottation](#flottation) | 2 | `flotation.balance`, `.kinetics_first_order` |
| [Filtration](#filtration) | 2 | `filtration.constant_pressure_cake`, `.cake_moisture` |
| [Hydrométallurgie](#hydrometallurgie) | 4 | `hydrometallurgy.leaching_yield`, `.leach_kinetics_first_order`, `.neutralization`, `.precipitation_yield` |
| [Extraction par solvant](#extraction-par-solvant) | 4 | `solvent_extraction.single_stage`, `.stripping_single_stage`, `.countercurrent_kremser`, `.stages_required` |
| [Thermodynamique](#thermodynamique) | 3 | `thermodynamics.gibbs_equilibrium`, `.strong_acid_ph`, `.weak_acid_ph` |
| [Statistiques](#statistiques) | API | `describe`, `linear_regression`, `correlation`… |

## Bilan de matière

**Paquet :** `metallurgypy.mass_balance`. Notations : \(F\) masse d'alimentation, \(g\) teneur de l'alimentation en **fraction massique** du métal (0,025 pour 2,5 %), \(R\) récupération (fraction entre 0 et 1).

Métal contenu, récupéré et restant :

\[
m_{\text{alim}} = F\,g \qquad m_{\text{réc}} = R\,F\,g \qquad m_{\text{rest}} = (1-R)\,F\,g
\]

**Exemple (illustratif)** : \(F = 1000\) t, \(g = 0{,}025\), \(R = 0{,}92\) donnent 25 t, 23 t et 2 t.

### Partage en deux produits

Pour une alimentation \(F\) séparée en concentré (masse \(C\), teneur \(c\)) et rejets (masse \(T\), teneur \(t\)), les bilans \(F = C + T\) et \(F g = C c + T t\) donnent :

\[
C = F\,\frac{g - t}{c - t} \qquad T = F\,\frac{c - g}{c - t}
\]
\[
\text{rendement massique} = \frac{C}{F} \qquad R = \frac{C\,c}{F\,g} \qquad \text{rapport d'enrichissement} = \frac{c}{g}
\]

**Exemple (illustratif)** : \(F = 1000\) t, \(g = 2\) %, \(c = 20\) %, \(t = 0{,}4\) % donnent \(C \approx 81{,}63\) t, un rendement massique d'environ 8,2 % et une récupération d'environ 81,6 %.

!!! tip "La récupération n'est pas le rendement massique"
    La récupération est la part du **métal contenu** qui va dans un produit ; le rendement massique est la part de la **masse totale**. Ici 82 % contre 8 % : la bibliothèque les garde dans des champs séparés et nommés explicitement.

**Domaine.** La teneur d'alimentation doit être comprise entre celles des rejets et du concentré, et les deux teneurs de produits doivent différer ; sinon un produit aurait une masse négative ou le partage est indéterminé. Hors de ce domaine, le modèle lève `ModelDomainError` au lieu de renvoyer un nombre. Une teneur d'alimentation nulle rend la récupération indéfinie : elle est refusée.

**Hypothèses et limites.** Bilan d'un seul constituant, en régime permanent et à un instant donné. Les teneurs sont prises comme exactes en mode `standard` (utilisez `propagate_model` pour propager l'incertitude analytique). Les erreurs d'échantillonnage et d'analyse peuvent rendre un rendement ou une récupération physiquement absurdes même si l'arithmétique est correcte. L'utilisateur est responsable de la même base (sèche ou humide) pour les masses et les teneurs.

## Réactifs

**Paquet :** `metallurgypy.reagents`.

\[
\rho = \frac{m}{V} \qquad c = \frac{m}{M\,V} \qquad c_1 V_1 = c_2 V_2 \qquad \dot m_{\text{réactif}} = d\,\dot m_{\text{minerai}}
\]

Concentration massique \(\rho\) et molaire \(c\) (masse de soluté \(m\), masse molaire \(M\), volume \(V\)) ; dilution qui conserve la quantité de soluté ; consommation pour un dosage \(d\) (masse de réactif par tonne de minerai) et un débit de minerai. Les consommations journalière et par campagne s'obtiennent en multipliant par le temps de fonctionnement fourni par l'utilisateur ; la pureté commerciale divise la masse de produit.

!!! warning "Aucun dosage n'est intégré"
    Les dosages viennent toujours de l'utilisateur ou d'une source documentée.

**Limites.** Mélange idéal : les volumes ne sont additifs que là où c'est dit. La pureté et le titre du réactif sont fournis par l'utilisateur.

## Électrolyse (electrowinning)

**Paquet :** `metallurgypy.electrowinning`. Courant \(I\), durée \(t\), masse molaire \(M\), nombre d'électrons \(n\), constante de Faraday \(F\) :

\[
m_{\text{théo}} = \frac{I\,t\,M}{n\,F} \qquad m_{\text{réelle}} = \eta\,m_{\text{théo}} \qquad j = \frac{I}{A}
\]
\[
E = U\,I\,t \qquad e = \frac{E}{m_{\text{réelle}}} = \frac{U\,n\,F}{\eta\,M}
\]

avec \(\eta\) le rendement de courant (fraction), \(A\) la surface cathodique active, \(U\) la tension de cellule et \(e\) l'énergie spécifique. \(F\) vaut environ \(96\,485\) C/mol, valeur exacte fixée par la définition du SI de 2019.

La production théorique et la production réelle sont affichées côte à côte, **jamais fusionnées**.

**Limites.** Une seule réaction d'électrode avec un \(n\) fixe ; les réactions parasites n'apparaissent qu'à travers \(\eta\). Courant et tension constants. La tension de cellule est une entrée, pas une prédiction. Le modèle ne prédit ni la qualité du dépôt, ni les courts-circuits, ni les incidents de marche.

## Flottation

**Paquet :** `metallurgypy.flotation`. Deux outils simples : le bilan concentré/rejets (mêmes formules que le [partage en deux produits](#partage-en-deux-produits)) et une cinétique du premier ordre :

\[
R(t) = R_\infty\left(1 - e^{-k t}\right) \qquad t_{95} = \frac{\ln 20}{k}
\]

!!! warning "Ce que ce n'est pas"
    Ce sont des outils de comptabilité et d'ajustement empirique. MetallurgyPy ne simule pas un circuit de flottation, ne prédit pas la flottabilité et ne fournit aucune constante de vitesse : \(R_\infty\) et \(k\) viennent de vos essais.

**Limites.** Les teneurs portent des erreurs d'analyse et d'échantillonnage que les formules amplifient quand la teneur d'alimentation est proche de celle du concentré ou des rejets. Les deux paramètres cinétiques ne valent que pour le minerai, les réactifs et les conditions de cellule où ils ont été ajustés. **Non implémenté :** cinétique multi-classes, simulation de circuit, modèles bulle/particule, changement d'échelle.

## Filtration

**Paquet :** `metallurgypy.filtration`. Filtration à pression constante, forme classique \(t/V\) en fonction de \(V\), et humidité du gâteau.

\[
\frac{dt}{dV} = K V + B \qquad K = \frac{\mu\,\alpha\,c}{A^2\,\Delta P} \qquad B = \frac{\mu\,R_m}{A\,\Delta P} \qquad t(V) = \frac{K V^2}{2} + B V
\]

avec \(\mu\) la viscosité, \(\alpha\) la résistance spécifique du gâteau, \(c\) la masse de solides par volume de filtrat, \(R_m\) la résistance du milieu, \(A\) la surface et \(\Delta P\) la perte de charge. Humidité sur base humide \(m_{\text{eau}}/m_{\text{humide}}\) et sur base sèche \(m_{\text{eau}}/m_{\text{sec}}\).

!!! warning "Périmètre"
    Gâteau incompressible seulement. Gâteaux compressibles, filtration à débit constant, lavage et essorage ne sont pas modélisés. \(\alpha\) et \(R_m\) doivent être mesurés pour la pulpe et le filtre utilisés ; aucun n'est fourni. Si vos points \(t/V\) ne sont pas alignés en fonction de \(V\), le modèle ne décrit pas votre filtration et le résultat ne doit pas être utilisé.

## Hydrométallurgie

**Paquet :** `metallurgypy.hydrometallurgy`.

**Rendement de lixiviation** à partir des analyses des solides, recoupé avec l'analyse de la solution :

\[
X_{\text{solides}} = 1 - \frac{m_{\text{résidu}}}{m_{\text{alim}}} \qquad m_{\text{sol}} = V\,C \qquad \text{écart} = m_{\text{dissous (solides)}} - m_{\text{sol}}
\]

L'**écart** est une information (erreur d'analyse, solution entraînée, précipitation) ; MetallurgyPy ne fixe aucun seuil d'acceptation.

**Cinétique de lixiviation du premier ordre** (ajustement empirique, pas un mécanisme) :

\[
X(t) = X_{\max}\left(1 - e^{-k t}\right) \qquad t_{90} = \frac{\ln 10}{k}
\]

**Neutralisation stœchiométrique** : \(n_H = V c_H\), \(n_{\text{base}} = n_H / z\), \(m_{\text{base}} = n_{\text{base}} M / p\) (pureté \(p\)).

**Rendement de précipitation** : \(m_{\text{précipitée}} = (C_0 - C_f)V\) et rendement \((C_0 - C_f)/C_0\).

!!! warning "Stœchiométrie n'est pas équilibre"
    La neutralisation donne le **minimum stœchiométrique**. Elle ne modélise ni le pouvoir tampon, ni l'hydrolyse des métaux, ni la précipitation, ni la formation de gypse : la consommation réelle de réactif est généralement plus élevée.

**Non implémenté :** spéciation, diagrammes d'équilibre, cinétiques mécanistes (cœur rétrécissant, diffusion, passivation), simulation de tas ou de cuves, produits de solubilité.

## Extraction par solvant

**Paquet :** `metallurgypy.solvent_extraction`. Tous les modèles supposent un **coefficient de distribution \(D\) constant** (isotherme linéaire). \(r = O/A\) est le rapport des volumes organique/aqueux.

**Un étage** : \(D = C_{\text{org}}/C_{\text{aq}}\) à l'équilibre,

\[
C_{\text{aq}} = \frac{C_{\text{alim}}}{1 + D\,r} \qquad C_{\text{org}} = D\,C_{\text{aq}} \qquad \text{extraction} = \frac{D\,r}{1 + D\,r}
\]

**Stripping en un étage** : bilan \(y_0 O + x_{\text{in}} A = y O + x A\) avec \(y = D_s\,x\), d'où \(x = \dfrac{y_0 + (A/O)\,x_{\text{in}}}{D_s + A/O}\) et stripping \(= (y_0 - y)/y_0\).

**Contre-courant (Kremser)** : facteur d'extraction \(E = D\,r\) et fraction restant dans le raffinat après \(N\) étages :

\[
\varphi = \frac{E - 1}{E^{N+1} - 1} \qquad \left(\varphi = \frac{1}{N+1}\ \text{si}\ E = 1\right) \qquad C_{\text{raffinat}} = \varphi\,C_{\text{alim}}
\]

**Nombre d'étages requis** pour une extraction cible :

\[
N = \frac{\ln\!\left(1 + \dfrac{E - 1}{\varphi}\right)}{\ln E} - 1 \qquad \varphi = 1 - \text{extraction}
\]

Le Core fournit aussi un pas à pas de McCabe–Thiele contre une isotherme **tabulée par l'utilisateur** : il interpole vos données et n'en invente aucune.

!!! warning "Isotherme linéaire seulement"
    Les extractants réels saturent : \(D\) diminue quand la phase organique se charge. Utilisez ces modèles pour des systèmes dilués ou comme première estimation ; vous fournissez \(D\) pour le système chimique, le pH et la température indiqués. Aucune donnée d'extractant n'est intégrée.

**Limites.** Les étages sont des étages d'équilibre : le rendement réel d'un mélangeur-décanteur est inférieur à 100 % et n'est pas appliqué ; le nombre d'étages requis est donné en valeur continue, le nombre pratique étant son plafond avant rendement. **Non implémenté :** rendement de mélangeur-décanteur, systèmes multi-constituants, isothermes dépendant du pH, simulation de circuit.

## Thermodynamique

**Paquet :** `metallurgypy.thermodynamics`.

**Énergie de Gibbs et constante d'équilibre** à partir de \(\Delta H\) et \(\Delta S\) :

\[
\Delta G = \Delta H - T\,\Delta S \qquad \ln K = -\frac{\Delta G}{R\,T}
\]

**pH d'un acide fort monoprotique** (solution idéale) : \([\mathrm{H^+}] = z\,c\), \(\mathrm{pH} = -\log_{10}[\mathrm{H^+}]\).

**pH d'un acide faible** : le bilan de charge est résolu numériquement par **bissection**.

\[
[\mathrm{A^-}] = \frac{C\,K_a}{K_a + [\mathrm{H^+}]} \qquad [\mathrm{OH^-}] = \frac{K_w}{[\mathrm{H^+}]} \qquad [\mathrm{H^+}] - [\mathrm{A^-}] - [\mathrm{OH^-}] = 0
\]

L'intervalle de départ, le nombre d'itérations et le résidu sont enregistrés dans le résultat.

!!! warning "Solutions idéales"
    L'activité est prise égale à la concentration. Pour des acides concentrés et des liqueurs de procédé, les coefficients d'activité sont loin de 1 et un pH mesuré peut différer de plus d'une unité de ces résultats. \(\Delta H\), \(\Delta S\), \(K_a\) et \(K_w\) viennent de votre source documentée ; aucune base de données thermodynamique n'est fournie.

**Non implémenté :** spéciation, diagrammes de Pourbaix, modèles de coefficients d'activité, acides polyprotiques, \(\Delta H\) et \(\Delta S\) dépendant de la température.

## Statistiques

**Paquet :** `metallurgypy.statistics` (API seulement, pas de formulaire dans Studio) : `describe`, `linear_regression`, `correlation`, `detect_outliers`, `moving_average`, `variability`. Ce sont des outils descriptifs usuels, vérifiés sur des valeurs calculées à la main et des cas d'erreur.
