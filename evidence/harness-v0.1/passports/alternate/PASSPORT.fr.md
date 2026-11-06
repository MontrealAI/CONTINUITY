# CONTINUITÉ Ω — Banc d’essai et de vérification v0.1 — Passeport de continuité

[English](PASSPORT.en.md) · [Français](PASSPORT.fr.md)

**Exécution logicielle locale · données commerciales synthétiques**

Ce Passeport présente l’évaluation fraîche fournie. Il en constitue un rapport enregistré ; utiliser la commande ci-dessous pour examiner de nouveau les preuves actuelles.

Un artefact terminé est une sortie logicielle JSON locale durable. Il ne constitue ni bien imprimé, ni acceptation client, ni réservation réelle de fournisseur, ni revenu, ni certification externe.

## Évaluation

| Champ | Valeur consignée |
| --- | --- |
| Assertion du test | `PASSED` — Comportement attendu du test observé |
| Verdict du composant testé | `COMPLETED` — Terminé |
| Stade des preuves | `LOCAL_SOFTWARE_EXECUTION` — Exécution logicielle locale avec données synthétiques |
| Affirmation sur la promesse complète | `DEMONSTRATED` — Démontré dans le stade déclaré |
| Sûreté dans le modèle testé | `DEMONSTRATED` — Démontré dans le stade déclaré |
| Liaison à l’autorité | `DEMONSTRATED` — Démontré dans le stade déclaré |
| État de la vérification fraîche | `COMPLETE` — Enregistrement terminé |
| Toutes les obligations terminées | Oui |
| Valeur commerciale | `NOT_ESTABLISHED` — Non établi |
| Authenticité d’instructions clients réelles | `NOT_ESTABLISHED` — Non établi |

Le comportement du test, la sortie du composant, le stade des preuves et l’affirmation métier sont distincts. Un refus correct peut satisfaire un test de sûreté tout en laissant une obligation inexécutée. Un test réussi révélant une acceptation indue ne qualifie pas le vérificateur défectueux.

## Résultats par obligation

| Commande | Destinataire | Unités requises | Unités observées | Unités acceptées | Résultat | Voie |
| --- | --- | --- | --- | --- | --- | --- |
| LBL-100 | CUSTOMER-A | 1100 | 1100 | 1100 | `COMPLETED` — Terminé | `backup` — Voie de secours |
| LBL-200 | CUSTOMER-B | 800 | 800 | 800 | `COMPLETED` — Terminé | `backup` — Voie de secours |

### Commande `LBL-100`

| Champ | Valeur consignée |
| --- | --- |
| Produit | LABEL-A |
| SHA-256 de la spécification finale | 1b590fba52dad5b09041ead75f1b3057b233d8b1ac35d9d9d37905696fc9675c |
| Échéance logique (unités) | 100 |
| Position d’achèvement (unités) | 5 |
| Observation monotone après export (ns) | 25304246174248 |

**Achèvement durable observé au plus tard après:** 100,854 ms (100853686 ns)

**Transition du producteur avant validation (durée écoulée):** 99,048 ms (99048041 ns)

**Motifs consignés:**

Aucun élément consigné.

### Commande `LBL-200`

| Champ | Valeur consignée |
| --- | --- |
| Produit | LABEL-A |
| SHA-256 de la spécification finale | a813e867578702ddec11b49ace3a5fd745ff391a2f5c95e7fe8af1c1f6b6c0e2 |
| Échéance logique (unités) | 100 |
| Position d’achèvement (unités) | 8 |
| Observation monotone après export (ns) | 25304250358462 |

**Achèvement durable observé au plus tard après:** 105,038 ms (105037900 ns)

**Transition du producteur avant validation (durée écoulée):** 103,191 ms (103190813 ns)

**Motifs consignés:**

Aucun élément consigné.

## Totaux de la promesse conservée

| Champ | Valeur consignée |
| --- | --- |
| Obligations requises | 2 |
| Obligations acceptées | 2 |
| Unités requises | 1900 |
| Unités de sortie observées | 1900 |
| Unités acceptées | 1900 |
| Unités non acceptées | 0 |
| Obligations tardives | 0 |
| Obligations incorrectes | 0 |
| Obligations dupliquées | 0 |
| Obligations terminées sans justification | 0 |

## Échecs observés

Aucun élément consigné.

## Preuves et affirmations non résolues

Aucun élément consigné.

## Conditions figées

| Champ | Valeur consignée |
| --- | --- |
| Identifiant du contrat | CONTRACT-labels-base-alternate |
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
| Capacités déclarées des voies (unités) | {"backup":2100,"primary":3000} |
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

Le journal complet des événements et interventions se trouve dans controller.json. Un calendrier ne prouve pas à lui seul que les pannes ont eu lieu ; la colonne d’observation indique les correspondances exactes dans l’enregistrement fourni du contrôleur.

## Mesures et lacunes comptables

| Champ | Valeur consignée |
| --- | --- |
| Durée réelle d’exécution mesurée | 141,992 ms (141992478 ns) |
| Processeur des enfants observé : utilisateur | 91,503 ms (91503000 ns) |
| Processeur des enfants observé : système | 15,698 ms (15698000 ns) |
| Processeur du contrôleur observé : utilisateur | 14,330 ms (14330000 ns) |
| Processeur du contrôleur observé : système | 0,000 ms (0 ns) |
| Mémoire résidente maximale (octets) | NON CONSIGNÉ / INCONNU |
| Stockage mesuré avant rapports finaux (octets) | 201029 |
| Demandes du candidat au relais | 8 |
| Nouvelles tentatives consignées | 0 |
| Redémarrages de processus consignés | 0 |
| Interventions humaines pendant cette exécution | 0 |
| Travail de préparation consigné (secondes) | NON CONSIGNÉ / INCONNU |
| Travail d’intégration consigné (secondes) | NON CONSIGNÉ / INCONNU |
| Coût monétaire complet | NON CONSIGNÉ / INCONNU |
| Durée mesurée de reprise/préparation (ms) | NON CONSIGNÉ / INCONNU |

Le temps réel mesure l’intervalle d’exécution locale du contrôleur. Les valeurs processeur des enfants et du contrôleur sont des différences distinctes d’utilisation des processus lorsqu’elles sont consignées. Le processeur de vérification/rapport et le développement n’y sont pas inclus. Le stockage mesure le contenu de l’exécution avant les fichiers finaux de contrôle/rapport et les métadonnées d’index, sans l’autorité conservée séparément. Les demandes au relais comptent celles du candidat ; les opérations internes du contrôleur restent dans le journal. Zéro intervention humaine ne concerne que cette exécution autonome.

Le travail de préparation et d’intégration, la mémoire non mesurée, les taux monétaires et les coûts commerciaux complets restent inconnus lorsqu’ils ne sont pas consignés. La devise et le budget configurés sont des données du cas synthétique, pas des dépenses mesurées ni un budget client. Aucun prix ni économie n’est déduit. Une observation bornée par méthode et par cas n’établit pas un avantage stable de performance.

| Champ | Valeur consignée |
| --- | --- |
| Allocation simultanée maximale par voie | {"backup":1900,"primary":0} |
| Transitions durables vérifiées | 8 |
| Reconstruction principale vérifiée | Non |

## Identité, versions et environnement

| Champ | Valeur consignée |
| --- | --- |
| Identifiant de l’exécution | labels-base-alternate-harness-c3af39df0a42 |
| Méthode candidate | `harness` — Procédure accompagnée par le banc d’essai |
| Scénario | `alternate` — Exécution de remplacement réalisable |
| Graine consignée | 101 |
| État du contrôleur | `COMPLETE` — Enregistrement terminé |
| Début d’exécution (UTC) | 2026-11-06T20:38:26.247035+00:00 |
| SHA-256 du contrat conservé | 86e7a72cc3e25bf924d9a5632f710dc0f6a8708317f99cc2bfc2def70604f2cf |
| SHA-256 de la référence observée | 1d306ee5dca5af968d65ba0c73bd10a481cf7dd383c03b8ceda75cfa6111f5ef |
| Version du vérificateur frais | 0.1.0 |
| Schéma du résultat de vérification | continuity-harness/verification/v1 |
| Schéma de la référence conservée | continuity-harness/reference/v1 |
| Empreinte de référence fournie indépendamment | 1d306ee5dca5af968d65ba0c73bd10a481cf7dd383c03b8ceda75cfa6111f5ef |
| SHA-256 du résultat structuré canonique | e2e2c755d76a46569ac358226e45b4ff29be9d0e089284061721c6a298d11ade |
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
| evidence/artifacts/LBL-100.json | `3adf2e49ff4e900a1cf8f2122bd4c1cf36055ba5167d2ab355d028c2c22b93f2` |
| evidence/artifacts/LBL-200.json | `04d1fbd55539d0d37da4279ad115614c28ede75ec96a6eeca4b6dda653f6f9c8` |
| evidence/service.sqlite | `34bd8e009594175fe24333ac6e8e83e81e05dea81f0d0f4562ff6b6706ecbaf4` |

Le vérificateur compare les octets actuels au sceau d’exécution conservé séparément. Ces empreintes identifient des octets ; elles n’authentifient pas une instruction client réelle et ne prouvent pas la complétude du monde réel.

## Vérification fraîche et commandes consignées

```sh
python3 -m continuity_harness --language fr verify --run /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison/runs/labels-base-alternate-harness-c3af39df0a42 --authority /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison/authority/labels-base-alternate-harness-c3af39df0a42 --reference-sha256 1d306ee5dca5af968d65ba0c73bd10a481cf7dd383c03b8ceda75cfa6111f5ef
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
