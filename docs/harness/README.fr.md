# CONTINUITÉ Ω — Banc d’essai et de vérification v0.1

[English](README.md) · **Français** · [Architecture](ARCHITECTURE.fr.md) · [Modèle de menace](THREAT_MODEL.fr.md) · [Exigences](REQUIREMENTS.fr.md)

**Préserver la même promesse. Éprouver la voie choisie. Examiner les preuves.**

Le banc d’essai met à l’épreuve un service de commandes d’étiquettes d’emballage au moyen de données commerciales synthétiques, de processus locaux jetables et d’un stockage durable. La reprise et l’exécution des commandes ont lieu sous forme d’opérations logicielles. Les artefacts JSON produits attestent un travail logiciel local terminé ; ils ne constituent ni des étiquettes imprimées, ni des engagements fournisseurs, ni une acceptation client, ni des revenus.

Le module `continuity_harness`, versionné séparément, exécute les trois contrôles ci-dessous et produit une évaluation structurée fraîche accompagnée de Passeports complets en français et en anglais. La [matrice des exigences](REQUIREMENTS.fr.md) relie chaque affirmation à son implémentation et à ses tests. Une suite peut réussir ses assertions prévues tout en montrant correctement qu’une promesse client soumise à une contrainte n’a pas été entièrement tenue.

## Ce que l’exercice vérifie

Un contrat figé identifie le destinataire, la spécification finale, la quantité restante, l’échéance, la fenêtre de capacité, les voies autorisées et la borne d’observation. Une procédure peut rétablir le service original ou emprunter une voie de remplacement autorisée. Elle ne peut pas substituer discrètement une obligation plus facile à l’obligation originale.

Trois cas témoins rendent cette distinction observable :

| Exercice | Conditions | Interprétation requise |
| --- | --- | --- |
| Reprise réalisable | La base principale est restaurée à partir d’un instantané périmé, puis rapprochée du journal d’événements protégé. La capacité suffit. | Toutes les obligations restantes doivent disposer de sorties durables correctes, dans les conditions du contrat. |
| Remplacement réalisable | La voie principale est indisponible. Une solution de secours autorisée dispose d’une capacité déclarée suffisante et d’une dépendance déclarée non touchée. | Les mêmes obligations doivent être exécutées par la solution de secours. |
| Perturbation avec ressources insuffisantes | Deux commandes se disputent une capacité de secours insuffisante ; un accusé de réception est perdu après une action durable ; un processus de travail est arrêté puis relancé. | Indiquer chaque obligation terminée, refusée, retardée ou non résolue. Un refus sûr ne vaut pas exécution complète. |

La démonstration de base comporte `LBL-100` pour `CUSTOMER-A` (1 100 unités) et `LBL-200` pour `CUSTOMER-B` (800 unités), soit 1 900 unités. L’instantané périmé conserve l’ancienne spécification de 1 000 unités de la première commande, omet la deuxième et comprend `LBL-300` (600 unités) avant son annulation. Le rejeu du journal conservé de cinq événements rétablit la première commande modifiée et la deuxième manquante, et supprime l’obligation annulée. Le nouveau banc d’essai définit son propre contrat de données synthétiques. Les délais fournis, prix et affirmations commerciales de l’article historique ne deviennent pas des mesures de cette exécution.

La capacité principale de base est de 3 000 unités. La capacité de secours est de 2 100 dans les contrôles réalisables et de 1 500 dans le contrôle contraint. Le calendrier déterministe de ce dernier donne la première transaction à la commande prioritaire : ses 1 100 unités sont réalisables, mais les 400 restantes ne couvrent pas les 800 de la deuxième commande. Les deux voies sont des services logiques locaux utilisant le même hôte et registre de confiance ; ces cas ne démontrent pas l’indépendance physique de fournisseurs.

## Installation et commandes

Utiliser Python 3.10 ou ultérieur sur **Linux x86_64 avec seccomp BPF disponible**. Le banc d’essai utilise la bibliothèque standard de Python et la bibliothèque SQLite fournie ; aucun téléchargement de paquet, secret, compte, modèle ou service payant n’est requis. Les tests existants du site web exigent également Node.js. Les autres architectures et systèmes d’exploitation ne sont pas pris en charge pour l’exercice avec candidat confiné de la version 0.1. Si le filtre requis ne peut être installé, l’exercice refuse toute évaluation favorable de l’isolement ; aucun repli sans confinement n’est prévu. Consulter le [modèle de menace](THREAT_MODEL.fr.md).

Depuis la racine du dépôt, utiliser un nouveau répertoire de sortie pour chaque expérience :

```sh
python3 -m continuity_harness --language fr demo --out /tmp/continuite-banc-essai-001
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuite-banc-essai-001
python3 -m continuity_harness --language fr verify --run RUN_DIRECTORY --authority AUTHORITY_DIRECTORY --reference-sha256 REFERENCE_SHA256
python3 -m continuity_harness --language fr compare --out /tmp/continuite-comparaison-001
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuite-comparaison-001
python3 -m continuity_harness --language fr challenge --out /tmp/continuite-epreuves-001
python3 -m unittest discover -s tests -p 'test_harness*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

`RUN_DIRECTORY`, `AUTHORITY_DIRECTORY` et `REFERENCE_SHA256` désignent le chemin de l’exécution, celui de l’autorité conservée et l’empreinte de référence enregistrée indépendamment dans `INDEX.json` de la suite. La référence faisant autorité est conservée séparément du travail candidat. Ne pas remplacer cette empreinte figée par une valeur recalculée à partir d’un paquet candidat non fiable. Une empreinte de référence absente ne peut produire d’évaluation favorable de l’autorité. Utiliser `--language en` pour l’interface anglaise. Les identifiants techniques, commandes, schémas et empreintes des preuves restent communs aux deux langues.

`demo` exécute les trois contrôles de base avec la méthode accompagnée par le banc d’essai. `compare` exécute 24 essais conventionnels/accompagnés sur quatre cas et trois contrôles, et conserve 12 entrées d’IA explicitement **NOT RUN — NON EXÉCUTÉES**. `verify-suite` relit chaque exécution actuelle et sa référence conservée ; les résultats enregistrés ne font pas foi. Utiliser `--help` avec la commande principale ou une sous-commande pour l’aide intégralement localisée.

Le code de sortie **0** signifie que les assertions prévues de la suite demandée ont réussi, ou qu’une vérification individuelle a démontré l’exécution complète. Le code **3** signifie que ce critère de suite ou cette affirmation individuelle de promesse complète n’a pas été établi avec succès. Ainsi, la vérification fraîche d’une exécution correctement contrainte et partiellement terminée renvoie **3**, tandis que la démonstration peut renvoyer **0** parce qu’elle a observé exactement le résultat partiel déclaré. Le code **2** indique une commande invalide ou une erreur au niveau de la commande. Lire toujours les champs structurés ; le seul code de sortie ne décrit pas chaque obligation.

Chaque nouveau répertoire de suite contient :

| Enregistrement | Rôle |
| --- | --- |
| `INDEX.json` | Emplacements des exécutions, empreintes de référence consignées séparément et complétude de la suite. |
| `ATTEMPTS.jsonl` | Tentatives commencées et terminées, conservées en cas d’interruption. |
| `SUMMARY.json`, `SUMMARY.en.md`, `SUMMARY.fr.md` | Comparaison structurée de la suite et ses deux résumés linguistiques. |
| `runs/RUN/RESULT.json` | Résultat d’acceptation fraîche de l’exécution. |
| `runs/RUN/PASSPORT.en.md`, `PASSPORT.fr.md` | Deux présentations complètes du même résultat, avec la commande exacte de vérification fraîche. |
| `runs/RUN/evidence/` et `controller.json` | Base durable fermée, artefacts de réalisation et observations de l’exécution et des pannes. |
| `authority/RUN/` | Contrat, référence, journal et sceau d’exécution conservés, inaccessibles aux candidats. |

Les répertoires de sortie existants sont refusés. Utiliser un nouveau chemin pour préserver une tentative antérieure infructueuse ou incomplète. Seuls les processus créés par cette invocation du banc d’essai sont nettoyés.

La vérification fraîche examine les preuves durables actuelles. L’ouverture d’un Passeport enregistré ne fait que lire un rapport antérieur. Un artefact modifié, une autorité absente, une exécution incomplète, une erreur du vérificateur ou une version non prise en charge doivent rester visibles dans la nouvelle évaluation.

## Interpréter correctement un résultat

Chaque exécution distingue les champs suivants :

| Champ | Signification |
| --- | --- |
| Assertion du test | Le test a-t-il observé le comportement attendu déclaré ? |
| Verdict du composant testé | Ce que le composant mis à l’épreuve a déclaré. |
| Stade des preuves | L’exercice ou l’observation qui a réellement eu lieu. |
| État de l’affirmation | L’affirmation précisée est-elle démontrée, réfutée ou non établie à ce stade ? |
| Résultat par obligation | Ce qui est arrivé à l’obligation exacte de chaque destinataire. |

Un test réussi peut reproduire l’acceptation indue d’un vérificateur défectueux. Le refus correct d’une demande de capacité peut démontrer une propriété de sûreté tout en laissant une commande inexécutée. Aucun des deux ne permet d’affirmer une continuité complète.

## Comparaison et coûts

La procédure conventionnelle et celle accompagnée par le banc d’essai reçoivent les mêmes informations visibles, services, permissions et calendriers de panne. Le rapprochement ordinaire, les transactions et l’idempotence sont disponibles à la procédure conventionnelle. Chaque méthode utilise le même vérificateur d’acceptation fraîche et un état initial isolé.

L’adaptateur d’IA constitue un groupe de comparaison distinct. Sans capacité locale appropriée configurée explicitement, son résultat de performance est **NOT RUN — NON EXÉCUTÉ**. Une réponse enregistrée ou un substitut peut tester l’interface, sans établir la performance d’une IA. La démonstration par défaut n’exige ni téléchargement de modèle, ni API payante, ni création de compte, ni identifiant secret.

La durée réelle d’exécution, le processeur des enfants et du contrôleur, le stockage, les demandes au relais, les tentatives répétées et les redémarrages sont consignés avec les limites de leur mesure. Les unités logiques configurées ne sont pas des heures réelles mesurées. L’instant d’achèvement accepté est une observation prudente de confiance après export/fsync de l’artefact, distincte de l’horodatage antérieur de transition du producteur. Mémoire maximale, effort distinct de vérification, préparation, intégration, travail humain, taux monétaires et coûts commerciaux externes restent inconnus s’ils n’ont pas été mesurés. Le zéro consigné pour les interventions humaines concerne uniquement l’exécution autonome. Des coûts manquants empêchent d’affirmer sans réserve qu’une méthode est moins coûteuse.

Les trois cas de transfert préenregistrés fixent les quantités à 700/900, 600/500 et 1 200/1 000 unités, modifient les capacités et identifiants de dépendance, et ajoutent une modification de spécification de la deuxième commande. Les deux méthodes réelles réutilisent les mêmes interfaces et déduisent leurs commandes du journal fourni. Ces cas sont réservés hors de la démonstration de base ; ce ne sont ni des données secrètes du dépôt ni un échantillon représentatif d’entreprises. Une observation par méthode/contrôle/cas peut établir les sorties de cette exécution ; elle ne démontre pas un avantage stable de performance ou de découverte.

## Preuves conservées des épreuves adverses et de l’ablation

`challenge` conserve huit contrôles identifiés séparément : ablation de la reprise sans rapprochement du journal ; dossier candidat cohérent de 1 850 unités avec empreintes recalculées ; empreinte de référence omise ; octets d’artefact modifiés avec ancien Passeport favorable ; dépendance défaillante partagée ; et trois vérificateurs volontairement défectueux qui ignorent l’intégrité des octets, ignorent le retrait d’autorisation ou rejettent une reprise valide. L’ablation conserve la validation et les transactions ordinaires du service. Son échec ne démontre pas une valeur supplémentaire de l’IA.

Cette suite non comparative crée quatre nouvelles exécutions locales : un contrôle positif et trois épreuves de procédure. Les autres cas réutilisent des copies des preuves du contrôle positif. Les coûts d’exécution copiés ne doivent pas être additionnés comme nouvelles mesures. Les durées de vérification fraîche de l’épreuve sont mesurées séparément dans son enregistrement structuré.

La sortie contient `CHALLENGE_SPEC.json`, `ATTEMPTS.jsonl`, `SUMMARY.json` et les résumés bilingues ; `positive-control/run` et `positive-control/authority` ; puis `cases/CASE/` pour chaque épreuve. Chaque cas conserve ses propres `run/`, `authority/`, `TARGET_RESULT.json`, `REFERENCE_RESULT.json`, `CHALLENGE.json` et Passeports complets français/anglais. L’assertion externe et l’affirmation limitée évaluent la propriété nommée de la procédure ou du vérificateur ; la référence inchangée fournit les résultats sous-jacents par obligation. Un test révélant une acceptation indue peut réussir alors que la qualification du vérificateur mutant échoue.

Utiliser la commande `verify` exacte et l’empreinte consignée indépendamment dans le Passeport d’un cas pour inspecter ses preuves actuelles avec le vérificateur inchangé. Omettre volontairement l’empreinte pour reproduire le cas d’empreinte manquante. `verify` ordinaire reproduit l’évaluation de référence ; relancer `challenge` dans un nouveau répertoire pour reproduire un composant volontairement modifié. `verify-suite` s’applique au format indexé de démonstration/comparaison, pas à ce répertoire d’épreuves. Aucun mutant ne modifie le code du vérificateur installé.

## Historique préservé et prochaines preuves

Cette implémentation est versionnée séparément du prototype de recherche préservé `continuity_omega`. Le [périmètre de migration](../../MIGRATION.md), le [manifeste de provenance](../../PROVENANCE.json), les PDF originaux, les preuves, les publications et leurs liens gardent leur sens historique. Une nouvelle implémentation n’efface pas les [contre-exemples historiques](../continuity-omega-paper/EVIDENCE.fr.md).

Avant tout exercice réel, il faut encore établir l’autorité véritable sur une commande, la garde et la divulgation autorisées des sources, la qualification réelle d’un fournisseur de secours et de sa fenêtre de capacité, une procédure d’acceptation convenue, des conditions opérationnelles mesurées et l’ensemble des obligations commerciales. Le [pilote proposé](../continuity-omega/REAL_PILOT.fr.md) décrit ce stade distinct. Un transfert synthétique local n’établit ni client payant ni réseau de fournisseurs.
