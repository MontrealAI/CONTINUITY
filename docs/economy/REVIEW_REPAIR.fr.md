# CONTINUITÉ Ω — Correction après revue de la couverture expérimentale

[English](REVIEW_REPAIR.md) · [Résultats initiaux](RESULTS.fr.md) · [Preuves de correction](../../evidence/economy-v0.2/review-repair/QUALIFICATION.json) · [Constat de revue](https://github.com/MontrealAI/CONTINUITY/pull/3#discussion_r4498755611)

## Le défaut et ses contre-exemples réels

La revue automatisée de `46c2e0b2123cb56f24dd956b2dbfb79a7f7fbecd` a constaté que le vérificateur de l’expérience complète exigeait les noms `base`, `successor` et `challenges`, sans imposer les types de suites correspondants. Un enfant réussi pouvait donc être réutilisé sous les trois noms. L’expérience complète initiale contenait bien les preuves requises ; le défaut était l’acceptation par le vérificateur d’un remplacement incomplet.

Le défaut a été reproduit contre la source publiée inchangée à partir de copies physiques de preuves historiques réelles, avec les attentes consignées avant d’invoquer ce vérificateur :

| Contre-exemple conservé | Preuves historiques uniques fournies | Couverture requise absente | Ancien vérificateur |
| --- | --- | --- | --- |
| Trois noms désignent une seule démonstration de base | Sept cellules de base du banc seulement | Cellules conventionnelles/sans achat/IA, successeur, épreuves contradictoires | `PASSED`, sortie 0 |
| Trois noms désignent une seule comparaison de base | Vingt-huit cellules de comparaison de base | Successeur et épreuves contradictoires | `PASSED`, sortie 0 |

Les deux assertions externes ont réussi parce qu’elles exposaient le défaut. La qualification de l’ancien vérificateur est **ÉCHOUÉE** pour la couverture d’une expérience complète. Il s’agit d’une intervention sur les preuves, pas d’une nouvelle production ; elle n’efface pas l’acceptation légitime des exécutions individuelles initiales. Sorties, erreurs, entrées, source et commandes antérieures restent dans l’archive distincte de correction.

## La correction

La correction source `f9e56c7dd9627b322406e05c53b4f6537d434262` modifie le module de vérification agrégée pour exiger :

- La version externe prise en charge, un objet contenant exactement les trois noms requis et des chemins enfants sûrs et distincts.
- Une suite de **comparaison** de base dans la cohorte **base**.
- Une suite de **comparaison** du successeur dans la cohorte **successor**.
- La suite d’**épreuves contradictoires** préenregistrée.
- Une vérification fraîche de chaque préenregistrement, cellule/contrôle requis, contrat et politique conservés, et preuve durable. Les étiquettes favorables sauvegardées restent insuffisantes.

Une expérience imbriquée ne peut remplacer aucun enfant. Le contrôle de rôle consomme le même index de comparaison que la vérification fraîche. Les contrôles indépendants existants du produit, du destinataire, de la capacité et de l’économie restent intacts.

Les contre-exemples conservés exactement à l’identique retournent désormais **sortie 2 / `SUITE_COVERAGE`**, en anglais et en français. Les **1 955 fichiers d’entrée** sont restés identiques octet par octet. Le premier enregistrement APRÈS identifie explicitement sa source modifiée non encore consignée dans un commit ; les enregistrements de qualification distincts identifient la correction publiée propre. Aucun état source n’est présenté comme l’autre.

## Gel historique et portée des affirmations

Le premier successeur a été exécuté à `3494becbbfaf15ae571a71df05a49b9ce982cc84` avec les 42 fichiers figés d’implémentation/interfaces/documentation inchangés. Cette observation historique reste vraie. La correction ultérieure modifie **un seul** de ces fichiers, `continuity_economy/suite.py` ; les **41** autres restent identiques. Le vérificateur corrigé actuel n’est donc pas présenté comme l’implémentation initiale de 42 fichiers inchangés.

Contrats, politiques de participation, empreintes des cas, gel initial et archive initiale restent inchangés. Le SHA-256 de l’archive initiale reste `a96c6b7c25e0e17ed1c1f7d0fcf13b70c338159ae9c10c5f825699b9e186db25`. La version `0.2.0` de l’expérience et du format des preuves est conservée ; les commits source exacts distinguent cette correction avant publication de version. Aucun résultat antérieur, identité source ou version v0.1 publiée n’est remplacé.

Les exécutions complètes ultérieures sont des **reproductions de régression**, pas de nouveaux successeurs tenus à l’écart ni des comparaisons statistiques fusionnées avec les premières observations. Ni la correction ni ses tests n’établissent un avantage de méthode, une économie de coût complet ou une demande volontaire réelle. Le travail humain de correction et de revue n’a pas été chronométré.

## Validation et correspondance entre exigences et tests

Douze tests ciblés de couverture agrégée et les huit tests CLI existants ont réussi avant la qualification depuis une source propre. Les tests ciblés substituent explicitement les jugements terminaux afin d’isoler l’admission ; ils ne constituent pas une nouvelle preuve de production. Les contre-exemples conservés et les contrôles frais distincts des preuves durables réelles évaluent la correction au-delà de ces tests d’admission. La source exacte, les commandes et les résultats conservés sont identifiés dans [QUALIFICATION.json](../../evidence/economy-v0.2/review-repair/QUALIFICATION.json).

### Qualification observée à la source corrigée

Les observations suivantes portent sur la source propre `f9e56c7dd9627b322406e05c53b4f6537d434262`. Une tâche CI réussie et une reproduction locale réussie sont des observations distinctes ; les preuves favorables comme défavorables sont conservées.

| Observation | Résultat observé | Portée |
| --- | --- | --- |
| Suite locale complète de régression | **436 tests réussis en 76,716 secondes** | Régressions existantes et nouveaux tests de couverture |
| Flux CI pour envoi et demande de fusion | **Les six ont réussi** | La source corrigée exacte ; cela n’efface pas l’échec local distinct ci-dessous |
| Artefact CI réellement téléchargé `13551894820`, issu de l’exécution `42319942290` | **Vérification fraîche indépendante RÉUSSIE (`PASSED`)** | 28 cellules de base, 4 cellules du successeur et 26 épreuves contradictoires |
| Expérience complète historique initiale | **Vérification fraîche RÉUSSIE (`PASSED`)** | Le vérificateur corrigé accepte toujours les preuves durables complètes initiales |
| Reproduction locale `complete-replay-1` | **ÉCHOUÉE (`FAILED`)**, sortie 3 ; sa vérification fraîche distincte a aussi **ÉCHOUÉ (`FAILED`)**, sortie 3 | Une cellule de base n’a pas pu finaliser ses preuves ; aucune qualification favorable de cette cellule |

L’[artefact CI téléchargé](https://github.com/MontrealAI/CONTINUITY/actions/runs/42319942290/artifacts/13551894820) comptait **11 631 638 octets**, avec le SHA-256 `6cf6fc794789be983e320dba11b4c344cc2e708822d3c280ab8b5cddba00344a` ; **3 022 fichiers** ont été extraits. La vérification a porté sur ces fichiers téléchargés, sans s’appuyer sur une étiquette de flux CI ou un Passeport sauvegardé. L’[exécution CI](https://github.com/MontrealAI/CONTINUITY/actions/runs/42319942290), les métadonnées de téléchargement et l’enregistrement de vérification fraîche identifient cette observation positive séparément de la reproduction locale.

### Échec local de finalisation conservé

Dans `qualification/complete-replay-1`, la cellule `constructed-continuity.conventional` a consigné l’acceptation des **1 900 unités** par le destinataire et le règlement, puis a échoué lors de l’exportation des preuves avec **`DATABASE_STATE_CHANGED`** pour `runtime/capacity/COMPAT-A.W0.sqlite`. Le contrôleur a retourné une erreur, et le dossier de preuves incomplet a laissé le **résultat** et la **faisabilité du service** **NON ÉTABLIS (`NOT ESTABLISHED`)**. Sa vérification fraîche distincte a également échoué. Les enregistrements d’exécution antérieurs ne remplacent pas la copie de preuve qualifiée manquante.

L’examen diagnostique a utilisé des copies physiques conservées. La base principale seule correspondait à l’empreinte logique conservée avant fermeture et contenait l’action finale sur la capacité. L’ouverture de cette même base avec son journal d’écriture anticipée résiduel (WAL) exposait au contraire un état plus ancien, sans la réservation, l’engagement de capacité et l’exécution du dernier lot de **100 unités**. L’état antérieur a également été reproduit sans le fichier auxiliaire de mémoire partagée copié. Cela établit l’incohérence de la paire base principale/WAL conservée ; cela n’établit pas pourquoi l’ancien WAL est resté ou a réapparu après les points de contrôle réussis et les fermetures normales des processus consignés.

Un essai diagnostique borné a utilisé **deux bases de capacité distinctes**, des barrières transactionnelles explicites et la séquence inchangée d’empreinte/point de contrôle/fermeture/sauvegarde. Il **n’a pas reproduit** l’anomalie. Les points de contrôle ont réduit chaque WAL à zéro, la fermeture normale des processus l’a supprimé et les deux empreintes logiques exportées correspondaient aux valeurs conservées. Les exigences de point de contrôle, d’empreinte et d’acceptation des preuves n’ont pas été affaiblies, et cette enquête n’a pas justifié de correction supplémentaire du code d’exécution. Les octets de l’échec initial, le script diagnostique et les observations aux frontières des opérations restent conservés.

La reproduction locale échouée utilisait l’espace de travail partagé pour ses bases actives ; la commande documentée depuis une copie propre utilise `/tmp`, et la CI utilise le répertoire temporaire de son exécuteur. Une seule confirmation sur le chemin `/tmp` documenté a été préenregistrée. **Cette unique confirmation et sa vérification fraîche distincte ont toutes deux réussi : 28 enregistrements de base, quatre du successeur et 26 épreuves. Les 3 024 fichiers correspondaient après copie de l’exécution fermée dans les preuves conservées.** La différence d’emplacement motive ce contrôle borné ; elle ne constitue pas une explication démontrée de l’échec.

Les preuves CI positives et la tentative locale échouée restent des enregistrements distincts. Elles ne sont fusionnées ni entre elles ni avec les premières observations comparatives. L’échec de finalisation d’une cellule conventionnelle n’établit pas un avantage de méthode du banc, et le résultat CI positif ne résout pas l’incohérence locale inexpliquée entre base principale et WAL.

### Correspondance entre exigences et tests

| Exigence | Couverture exécutable dans `tests/test_economy_suite.py` |
| --- | --- |
| Des preuves complètes valides restent acceptables malgré les étiquettes sauvegardées | `test_complete_registered_children_are_verified_freshly_despite_saved_failed_labels` |
| Démonstrations, copies et comparaisons de base ne remplacent pas les rôles requis | Tests commençant par `test_passing_base_demo_` et `test_passing_base_comparison_` |
| Cohortes et schémas enfants restent contraignants | `test_swapped_comparison_cohorts_are_refused` ; `test_passing_nested_experiment_cannot_replace_any_required_child` |
| Admission externe stricte, versions prises en charge et chemins sûrs distincts | Tests commençant par `test_experiment_requires_`, `test_nonobject_indexes_`, `test_member_paths_` et `test_all_child_versions_` |
| Cellules/contrôles manquants et contrats modifiés empêchent la qualification | `test_missing_cell_or_challenge_cannot_be_hidden_by_saved_passes` ; `test_child_metadata_does_not_replace_independent_contract_binding` |
| Un enfant fraîchement échoué ne peut être remplacé par un PASS sauvegardé | `test_failed_fresh_run_or_challenge_cannot_be_hidden_by_saved_passes` |

```sh
python3 -m unittest discover -s tests -p 'test_economy_suite.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m continuity_economy --language fr experiment --out /tmp/continuite-economie-corrigee-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-corrigee-001
```

Choisir un nouveau répertoire de sortie. Les instructions de reproduction des dossiers AVANT/APRÈS accompagnent l’archive de correction. Le modèle de confiance et les limites économiques, de règlement et d’initialisation non résolues du rapport initial restent applicables ; une suite finie de régression n’est pas une preuve générale.
