# CONTINUITÉ Ω — Banc d’essai et de vérification v0.1 — Passeport de continuité

[English](PASSPORT.en.md) · [Français](PASSPORT.fr.md)

**Exécution logicielle locale · données commerciales synthétiques**

Ce Passeport présente l’évaluation fraîche fournie. Il en constitue un rapport enregistré ; utiliser la commande ci-dessous pour examiner de nouveau les preuves actuelles.

Un artefact terminé est une sortie logicielle JSON locale durable. Il ne constitue ni bien imprimé, ni acceptation client, ni réservation réelle de fournisseur, ni revenu, ni certification externe.

## Évaluation

| Champ | Valeur consignée |
| --- | --- |
| Assertion du test | `PASSED` — Comportement attendu du test observé |
| Verdict du composant testé | `PARTIAL` — Résultat partiel |
| Stade des preuves | `LOCAL_SOFTWARE_EXECUTION` — Exécution logicielle locale avec données synthétiques |
| Affirmation sur la promesse complète | `FAILED` — Échec |
| Sûreté dans le modèle testé | `DEMONSTRATED` — Démontré dans le stade déclaré |
| Liaison à l’autorité | `DEMONSTRATED` — Démontré dans le stade déclaré |
| État de la vérification fraîche | `COMPLETE` — Enregistrement terminé |
| Toutes les obligations terminées | Non |
| Valeur commerciale | `NOT_ESTABLISHED` — Non établi |
| Authenticité d’instructions clients réelles | `NOT_ESTABLISHED` — Non établi |

Le comportement du test, la sortie du composant, le stade des preuves et l’affirmation métier sont distincts. Un refus correct peut satisfaire un test de sûreté tout en laissant une obligation inexécutée. Un test réussi révélant une acceptation indue ne qualifie pas le vérificateur défectueux.

## Résultats par obligation

| Commande | Destinataire | Unités requises | Unités observées | Unités acceptées | Résultat | Voie |
| --- | --- | --- | --- | --- | --- | --- |
| LBL-100 | CUSTOMER-A | 1100 | 1100 | 1100 | `COMPLETED` — Terminé | `backup` — Voie de secours |
| LBL-200 | CUSTOMER-B | 800 | 0 | 0 | `REFUSED` — Refusé | NON CONSIGNÉ / INCONNU |

### Commande `LBL-100`

| Champ | Valeur consignée |
| --- | --- |
| Produit | LABEL-A |
| SHA-256 de la spécification finale | 1b590fba52dad5b09041ead75f1b3057b233d8b1ac35d9d9d37905696fc9675c |
| Échéance logique (unités) | 100 |
| Position d’achèvement (unités) | 5 |
| Observation monotone après export (ns) | 25304882005406 |

**Achèvement durable observé au plus tard après:** 212,879 ms (212878776 ns)

**Transition du producteur avant validation (durée écoulée):** 167,702 ms (167701629 ns)

**Motifs consignés:**

Aucun élément consigné.

### Commande `LBL-200`

| Champ | Valeur consignée |
| --- | --- |
| Produit | LABEL-A |
| SHA-256 de la spécification finale | a813e867578702ddec11b49ace3a5fd745ff391a2f5c95e7fe8af1c1f6b6c0e2 |
| Échéance logique (unités) | 100 |
| Position d’achèvement (unités) | NON CONSIGNÉ / INCONNU |
| Observation monotone après export (ns) | NON CONSIGNÉ / INCONNU |

**Achèvement durable observé au plus tard après:** NON CONSIGNÉ / INCONNU

**Transition du producteur avant validation (durée écoulée):** NON CONSIGNÉ / INCONNU

**Motifs consignés:**

- `CAPACITY_EXCEEDED`: Refus : capacité restante insuffisante ; aucune surallocation n’est déduite.
- `NO_DURABLE_OUTPUT`: Aucun résultat durable accepté n’existe pour cette obligation.

## Totaux de la promesse conservée

| Champ | Valeur consignée |
| --- | --- |
| Obligations requises | 2 |
| Obligations acceptées | 1 |
| Unités requises | 1900 |
| Unités de sortie observées | 1100 |
| Unités acceptées | 1100 |
| Unités non acceptées | 800 |
| Obligations tardives | 0 |
| Obligations incorrectes | 0 |
| Obligations dupliquées | 0 |
| Obligations terminées sans justification | 0 |

## Échecs observés

| Code technique | Explication | Commande | Diagnostic technique original |
| --- | --- | --- | --- |
| `ALL_OBLIGATIONS_NOT_COMPLETED` | La promesse complète au client n’a pas été tenue. | NON CONSIGNÉ / INCONNU |  |

## Preuves et affirmations non résolues

Aucun élément consigné.

## Conditions figées

| Champ | Valeur consignée |
| --- | --- |
| Identifiant du contrat | CONTRACT-labels-base-constrained |
| Schéma du contrat | continuity-harness/contract/v1 |
| Version du contrat | 1 |
| Mode d’exercice déclaré | SYNTHETIC_LOCAL_EXECUTION |
| SHA-256 des événements sources | 1f5119db7e2bd8f280a98b97ae72aecf3cc859750cbe6ced7710d48608eb2bca |
| Borne d’observation de la source | 5 |
| Déclaration de complétude de la source rédigée | Oui |
| Échéance logique (unités) | 100 |
| Échéance réelle configurée (ms) | 30000 |
| Objectif de reprise configuré (ms) | 15000 |
| Fenêtre de capacité [début, fin) | {"end":100,"start":0} |
| Durée de réservation (unités logiques) | 20 |
| Capacités déclarées des voies (unités) | {"backup":1500,"primary":3000} |
| Voies autorisées | ["primary","backup"] |
| Permissions déclarées | {"activation":true,"sharing":true} |
| Dépendances déclarées des voies | {"backup":"GRID-A-INDEPENDENT","primary":"GRID-A"} |
| Dépendances indisponibles | ["GRID-A"] |
| Devise configurée du cas synthétique | USD |
| Budget configuré du cas synthétique (unités mineures) | 0 |
| Conditions figées de comparaison | {"fixture_id":"labels-base","held_out":false,"information":"EQUAL","resource_policy":"SHARED_SERVICES","suite_id":"CONTINUITY-HARNESS-001"} |

Les unités logiques appartiennent au calendrier du contrôleur ; ce ne sont pas des heures mesurées. Les millisecondes et nanosecondes ci-dessous représentent des mesures locales monotones. L’achèvement durable utilise l’observation de confiance après export comme borne supérieure prudente, distincte de l’horodatage de transition du producteur avant validation. Un retard d’observation peut faire rejeter une borne tardive même si la persistance a eu lieu plus tôt. L’échéance réelle et l’objectif de reprise configurés sont des limites d’acceptation, pas des durées atteintes.

## Calendrier des pannes et observations

| Code technique | Action | Cible | Observé |
| --- | --- | --- | --- |
| `PRIMARY_UNAVAILABLE` — Voie principale désactivée | DISABLE | primary | Oui |
| `CONCURRENT_FINAL_CAPACITY` — Concurrence sur la capacité restante | RACE | backup | Oui |
| `ACK_LOST_AFTER_DURABLE_FULFILLMENT` — Accusé perdu après réalisation durable | DROP_ACK | service | Oui |
| `RETRY_WHILE_OUTCOME_UNKNOWN` — Nouvelle tentative pendant l’incertitude du résultat initial | RETRY | service | Oui |
| `SERVICE_KILLED_AFTER_COMMIT` — Processus de service arrêté après validation | KILL | service | Oui |
| `CANDIDATE_KILLED_AFTER_REQUEST` — Processus candidat arrêté après sa demande | KILL | candidate | Oui |
| `RESTART_RECONCILIATION` — Redémarrer et rapprocher l’état durable | RESTART | candidate | Oui |

Le journal complet des événements et interventions se trouve dans controller.json. Un calendrier ne prouve pas à lui seul que les pannes ont eu lieu ; la colonne d’observation indique les correspondances exactes dans l’enregistrement fourni du contrôleur.

## Mesures et lacunes comptables

| Champ | Valeur consignée |
| --- | --- |
| Durée réelle d’exécution mesurée | 300,662 ms (300662295 ns) |
| Processeur des enfants observé : utilisateur | 275,806 ms (275806000 ns) |
| Processeur des enfants observé : système | 62,260 ms (62260000 ns) |
| Processeur du contrôleur observé : utilisateur | 14,943 ms (14942999 ns) |
| Processeur du contrôleur observé : système | 4,021 ms (4021000 ns) |
| Mémoire résidente maximale (octets) | NON CONSIGNÉ / INCONNU |
| Stockage mesuré avant rapports finaux (octets) | 180884 |
| Demandes du candidat au relais | 9 |
| Nouvelles tentatives consignées | 1 |
| Redémarrages de processus consignés | 2 |
| Interventions humaines pendant cette exécution | 0 |
| Travail de préparation consigné (secondes) | NON CONSIGNÉ / INCONNU |
| Travail d’intégration consigné (secondes) | NON CONSIGNÉ / INCONNU |
| Coût monétaire complet | NON CONSIGNÉ / INCONNU |
| Durée mesurée de reprise/préparation (ms) | NON CONSIGNÉ / INCONNU |

Le temps réel mesure l’intervalle d’exécution locale du contrôleur. Les valeurs processeur des enfants et du contrôleur sont des différences distinctes d’utilisation des processus lorsqu’elles sont consignées. Le processeur de vérification/rapport et le développement n’y sont pas inclus. Le stockage mesure le contenu de l’exécution avant les fichiers finaux de contrôle/rapport et les métadonnées d’index, sans l’autorité conservée séparément. Les demandes au relais comptent celles du candidat ; les opérations internes du contrôleur restent dans le journal. Zéro intervention humaine ne concerne que cette exécution autonome.

Le travail de préparation et d’intégration, la mémoire non mesurée, les taux monétaires et les coûts commerciaux complets restent inconnus lorsqu’ils ne sont pas consignés. La devise et le budget configurés sont des données du cas synthétique, pas des dépenses mesurées ni un budget client. Aucun prix ni économie n’est déduit. Une observation bornée par méthode et par cas n’établit pas un avantage stable de performance.

| Champ | Valeur consignée |
| --- | --- |
| Allocation simultanée maximale par voie | {"backup":1100,"primary":0} |
| Transitions durables vérifiées | 5 |
| Reconstruction principale vérifiée | Non |

## Identité, versions et environnement

| Champ | Valeur consignée |
| --- | --- |
| Identifiant de l’exécution | labels-base-constrained-harness-c3af39df0a42 |
| Méthode candidate | `harness` — Procédure accompagnée par le banc d’essai |
| Scénario | `constrained` — Perturbation contrainte et reprise |
| Graine consignée | 101 |
| État du contrôleur | `COMPLETE` — Enregistrement terminé |
| Début d’exécution (UTC) | 2026-11-06T20:38:26.770841+00:00 |
| SHA-256 du contrat conservé | 6566ecb28c8e0d5a768812a4b3f41220cada58d01f1ab8f48de60ef623d9730a |
| SHA-256 de la référence observée | ec9f72beb31959636b8039bea70dfcf241091890ece0184e2bd7ecf51fb037e0 |
| Version du vérificateur frais | 0.1.0 |
| Schéma du résultat de vérification | continuity-harness/verification/v1 |
| Schéma de la référence conservée | continuity-harness/reference/v1 |
| Empreinte de référence fournie indépendamment | ec9f72beb31959636b8039bea70dfcf241091890ece0184e2bd7ecf51fb037e0 |
| SHA-256 du résultat structuré canonique | 47135b4f767ff6e40410b7c3a904192ef5de3fec9aeb2da7b6d358eb5c0d0d04 |
| Version de l’implémentation | 0.1.0 |
| Commit Git consigné | fa9da1f54acfaa82510a4b6b805c2980d3e5b31d |
| Arbre de travail avec modifications non commises | Non |
| Environnement Python consigné | 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ] |
| Plateforme et noyau consignés | Linux-6.18.57-x86_64-with-glibc2.39 |
| Version de SQLite consignée | 3.53.1 |
| Répertoire de travail consigné | /workspace/scratch/b1d5891eb025/continuity-harness-qualified-v2 |

### Identités des sources d’implémentation

| Chemin | SHA-256 |
| --- | --- |
| continuity_harness/__init__.py | `577ece33903d70ce17189e594370916b485efec1e66ee07f099b4f62ebd4219e` |
| continuity_harness/__main__.py | `c89523d1e0bbfc47bdcef086a06fabefacde32b7aca6be132e79d78b11e003c8` |
| continuity_harness/adapters.py | `ba0be575481384b74dfbc407c4e575bb8f561c50f1235fdf51f0b4b9c19865b0` |
| continuity_harness/candidate.py | `938d73f546c774452b22823639beda4b0f89d911abe429da48039bf1808e3141` |
| continuity_harness/challenges.py | `d14ec02a127eaab94bf440ccb76b38aa735983f393d6ccae80eb6fcdb1215a5d` |
| continuity_harness/controller.py | `7bbc8a87d34b64d8e9e621de5a907f3b123a3a0e973745c73385b73f3a52d1fd` |
| continuity_harness/fixtures.py | `4464f7c9b151300858703f2332049f83c2df429684326b5be3f4e45e7da11b9e` |
| continuity_harness/reporting.py | `e89eee75a923f9489112e243f140f17adba916627d3c02ff6ac2b58e9a1f8645` |
| continuity_harness/rpc.py | `36e48a53bd6c99a51f85fe1183f6e6e3ff9b0c3f3501c3d8c080ab1ff099b745` |
| continuity_harness/sandbox.py | `7ae5423afd96847b1c38c746a7c417f938624e32acf97273c27757b46e3d556f` |
| continuity_harness/schema.py | `4ad738e4b1ef001d039d92ffad897241be7605189b579abd69e38cfe3660427c` |
| continuity_harness/service.py | `6b2c1816e71b6d0768024ed2a2273d98929fd42c223853eff7f7ccd63108055c` |
| continuity_harness/suite.py | `bac676e2886e2ca434b775fe58a0f87b33c4c97f32badd5d2c63659323a5c4dc` |
| continuity_harness/verifier.py | `2177652f986f9a305d7d3c90e808ba15651a58280c4a6bfd3f37da028542df38` |
| experiments/harness-v0.1/PROVENANCE.json | `0c8697da8cd4eb8635cf5413c0f3e0b4c2dc82ea6cd7d8bc6cac194bed7f5f32` |
| experiments/harness-v0.1/spec.json | `8f08c8d524ab4aab9528728725d528eaa5f7e701403c9e176e8dff9b17380880` |

## Identités des preuves actuelles

| Chemin | SHA-256 |
| --- | --- |
| evidence/artifacts/LBL-100.json | `16bbece2f62fec92a1aa60a09e15ffc64a244a1ee71e85aaa537164af0c35c8f` |
| evidence/service.sqlite | `cf86f8ef0d75d92658ccd51ae0aa3aa26ae47afe85d40955c3efed0525a8c2d7` |

Le vérificateur compare les octets actuels au sceau d’exécution conservé séparément. Ces empreintes identifient des octets ; elles n’authentifient pas une instruction client réelle et ne prouvent pas la complétude du monde réel.

## Vérification fraîche et commandes consignées

```sh
python3 -m continuity_harness --language fr verify --run /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison/runs/labels-base-constrained-harness-c3af39df0a42 --authority /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison/authority/labels-base-constrained-harness-c3af39df0a42 --reference-sha256 ec9f72beb31959636b8039bea70dfcf241091890ece0184e2bd7ecf51fb037e0
```

Exécuter depuis la copie de l’implémentation consignée. Fournir l’empreinte de référence conservée indépendamment dans l’index de la suite ; ne pas la remplacer par une valeur dérivée des données candidates. La vérification n’écrase pas ce Passeport enregistré.

### Autres commandes consignées pour cette exécution

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m continuity_harness --language en compare --out /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison
```


## Hypothèses de confiance et limites restantes

| Champ | Valeur consignée |
| --- | --- |
| Mécanisme d’isolement du candidat | SECCOMP_BPF |
| Isolement appliqué | Oui |
| Observations des tests d’isolement | {"authority_open_denied":true,"network_denied":true,"process_inspection_denied":true,"spawn_denied":true,"workspace_open_denied":true} |
| Périmètre de confiance déclaré | TRUSTED_HOST_CONTROLLER_CLOCK_AND_VERIFIER_AUTHORED_SYNTHETIC_SOURCE |

L’hôte, le contrôleur, le journal rédigé, les services locaux, l’horloge et le vérificateur d’acceptation sont de confiance dans le modèle de panne déclaré. Le code candidat fourni et ses imports sont de confiance avant l’activation de seccomp ; aucun module tiers arbitraire n’est pris en charge. Le candidat reçoit des données bornées après filtrage et agit uniquement par le relais autorisé. Cela ne protège pas contre un administrateur malveillant de l’hôte.

L’identité, la garde, la complétude des sources et l’intégrité des octets sont des propriétés différentes. Des tests locaux finis ne constituent ni preuve générale, ni garantie universelle d’exécution exactement une fois, ni certification externe indépendante, ni validation commerciale. Un transfert synthétique n’établit que le transfert mesuré dans les conditions consignées.

Un modèle indisponible, un substitut ou une réponse enregistrée n’établissent aucune performance d’IA. Le groupe IA est NON EXÉCUTÉ à moins qu’une véritable capacité locale autorisée ait été exécutée et mesurée.

Enregistrements structurés : [RESULT.json](RESULT.json) · [controller.json](controller.json). Les deux Passeports linguistiques dérivent du même résultat structuré.
