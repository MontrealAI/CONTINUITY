# CONTINUITÉ Ω — Résultats exécutés du banc d’essai v0.1

[English](RESULTS.md) · **Français** · [Guide de reproduction](README.fr.md) · [Matrice des exigences](REQUIREMENTS.fr.md)

**Date de qualification : 6 novembre 2026 (UTC). Code qualifié : [fa9da1f54acfaa82510a4b6b805c2980d3e5b31d](https://github.com/MontrealAI/CONTINUITY/commit/fa9da1f54acfaa82510a4b6b805c2980d3e5b31d).**

Le jalon local borné a été démontré lors de la deuxième tentative de qualification. Les procédures conventionnelle et accompagnée par le banc d’essai ont rétabli puis exécuté les obligations réalisables, utilisé le secours autorisé lorsque nécessaire et conservé l’échec partiel lorsque sa capacité ne suffisait pas à toutes les commandes. Leurs résultats fonctionnels sont identiques dans les 12 paires préenregistrées. La première tentative reste non qualifiée : une vérification fraîche distincte a détecté des fichiers auxiliaires SQLite non scellés dans un cas de transfert ; son ancien résumé favorable n’a pas été réécrit.

Les preuves livrées établissent une exécution logicielle locale avec données synthétiques. Elles n’établissent ni étiquettes imprimées, ni client payant, ni fournisseurs physiquement indépendants, ni coût économique complet, ni valeur supplémentaire de l’IA, ni cyberrésilience générale. Les 12 entrées de comparaison d’IA sont **NOT RUN — NON EXÉCUTÉES**. Le coût complet, l’avantage comparatif et la valeur commerciale restent **NOT ESTABLISHED — NON ÉTABLIS**.

L’[enregistrement de livraison lisible par machine](../../evidence/harness-v0.1/RESULTS.json) et l’[archive complète des preuves](../../evidence/harness-v0.1/continuity-harness-v0.1-evidence.tar.xz) conservent les deux tentatives, les résultats individuels et Passeports bilingues, l’autorité, les artefacts durables, commandes, échecs et journaux de validation capturés. Les chemins d’archive cités sont relatifs au répertoire supérieur extrait `continuity-harness-v0.1-evidence/`. Un Passeport enregistré décrit une évaluation passée ; les reçus de vérification fraîche distincts établissent ce qui a été contrôlé ensuite.

## 1. Version, préenregistrement et historique de qualification

La révision initiale réelle était `8776d70ba091f71dab12fc9d3195baf7fc789676`. Le nouveau module `continuity_harness` possède sa version distincte 0.1.0. La spécification a été commise localement avant les résultats comparatifs au commit `318f6d76868fa63ce3e25805e1c11bbfc057f981` ; son arbre de contenu identique a été publié au commit `0b9eac772d8088a0ee44605aead85fa5d36dd93b` par l’interface GitHub connectée. La publication distante a suivi les contrôles préliminaires d’ingénierie et précédé la comparaison complète. Elle n’efface pas les observations antérieures. Cette distinction figure dans [AMENDMENTS.md](AMENDMENTS.md).

Les deux comparaisons utilisent la même spécification en version 1, de SHA-256 canonique `5b4304d1c855cd241a08f4ffc0bd83f95ee3c8ce3af9a06cb40b679f418edabc`. Le SHA-256 du fichier brut est `8f08c8d524ab4aab9528728725d528eaa5f7e701403c9e176e8dff9b17380880` ; ces valeurs identifient deux sérialisations de la même spécification. Hypothèses, quantités, capacités, voies autorisées, pannes, critères d’acceptation et conditions comparatives n’ont pas été assouplis après le premier échec.

| Tentative | Révision source | Comparaison initiale | Vérification fraîche distincte | Qualification |
| --- | --- | --- | --- | --- |
| 1, à la racine de la livraison | `5c92fd03a258a3f4845c50a5b37e7a14cd2aa40c` | 24 exécutions, 12 IA non exécutées ; contrôle enregistré PASSED | FAILED ; sortie 3 ; intégrité insuffisante des preuves d’un cas de transfert | **Non qualifiée ; conservée inchangée** |
| 2, sous `attempt-2/` | `fa9da1f54acfaa82510a4b6b805c2980d3e5b31d` | 24 exécutions, 12 IA non exécutées ; contrôle PASSED | PASSED ; sortie 0 ; aucune assertion échouée ni sûreté non établie | **Qualifiée dans le modèle local déclaré** |

### Le premier échec et la correction bornée

Le cas concerné était `labels-transfer-a-constrained-harness-8b9332cbc97f`. Son producteur annonçait `PARTIAL` et la vérification enregistrée acceptait initialement la première commande de 700 unités. La vérification distincte a trouvé des fichiers `service.sqlite-wal` et `service.sqlite-shm` non scellés. Elle a signalé `UNSEALED_EVIDENCE` et `DATABASE_NOT_CHECKPOINTED`, ramené la quantité acceptée à 0 sur 1 600 et laissé les deux obligations **UNRESOLVED — NON RÉSOLUES**. La sûreté est devenue **NOT_ESTABLISHED — NON ÉTABLIE**. La liste `critical_safety_failures` est un critère de qualification ; cette observation ne démontre ni surallocation effective ni exécution en double.

Cette observation défavorable reste dans l’historique : les 12 assertions conventionnelles attendues ont réussi la vérification fraîche, contre 11 sur 12 pour le banc. Les totaux acceptés fraîchement sont de 17 200 unités pour la méthode conventionnelle et 16 500 pour le banc, car sa sortie de 700 unités manquait de preuves suffisamment fiables. C’est un échec observé de qualification de cette tentative du banc, pas une infériorité universelle de la méthode. Il n’a été ni supprimé, ni rebaptisé égalité, ni regroupé avec la deuxième tentative.

L’empreinte du fichier principal scellé correspondait toujours. L’inspection de copies isolées a observé `last_tick=8` dans l’état principal scellé et `last_tick=5` lorsque le WAL périmé était appliqué. La cause de la réapparition des fichiers auxiliaires reste **NON ÉTABLIE**. Aucune attribution non justifiée à un processus, stockage ou acteur de l’hôte n’est faite. L’ancien résumé favorable, le reçu d’échec distinct et le diagnostic restent disponibles sous `comparison/` et `validation/compare-fresh*`.

La nouvelle finalisation capture l’état complet du service vivant avant fermeture, arrête tous les processus appartenant à l’exercice, sauvegarde la base SQLite active réelle, exige l’égalité avec l’état capturé, convertit la copie de preuve en base autonome à journal DELETE, la synchronise, puis publie seulement la base fermée dans `evidence/`. Les fichiers actifs restent séparés. Une différence ou une sauvegarde échouée empêche la qualification complète. Le vérificateur continue de refuser tout journal non vide à côté des preuves ; la correction n’ignore pas ces fichiers et n’assouplit pas leur contrôle. Neuf tests ciblés couvrent ces frontières, dont le WAL actif périmé, la reprise de vrais engagements présents dans un WAL, les modifications après fermeture et les échecs de finalisation. C’est une atténuation testée, pas une preuve couvrant toutes les pannes d’hôte/stockage ni une explication de la cause initiale. Voir [l’implémentation](../../continuity_harness/controller.py) et les [tests de finalisation](../../tests/test_harness_finalization.py).

### Commandes de qualification terminées

La deuxième tentative a utilisé une copie propre avant et après exécution, avec Python **3.12.14**, SQLite **3.53.1** et **Linux 6.18.57 x86_64, glibc 2.39**. L’enregistrement contient le chemin exact de l’interpréteur, les arguments et le répertoire de travail. Ces durées de commande incluent leur démarrage et leur production de rapports ; elles ne mesurent pas uniquement le candidat.

| Commande | Début UTC | Durée réelle (ms) | Sortie |
| --- | --- | --- | --- |
| demo (fr) | 2026-11-06T20:38:24Z | 967,963 | 0 |
| verify-suite / demo (en) | 2026-11-06T20:38:25Z | 114,918 | 0 |
| compare (en) | 2026-11-06T20:38:25Z | 6 089,120 | 0 |
| verify-suite / comparison (fr) | 2026-11-06T20:38:31Z | 365,171 | 0 |
| challenge (fr) | 2026-11-06T20:38:31Z | 816,276 | 0 |

Source : `attempt-2/QUALIFICATION.json` et les reçus `validation/*.stdout.json` correspondants. La démonstration a exécuté trois contrôles accompagnés ; la comparaison, 24 cellules de méthodes réelles ; la suite contradictoire, quatre nouvelles exécutions locales pour huit cas. Une copie de preuves n’est pas une autre exécution. Les deux tentatives restent des observations distinctes, pas des essais favorables indépendants regroupés.

## 2. Obligations effectivement préservées

Le journal de base conservé modifie `LBL-100` pour `CUSTOMER-A` à 1 100 unités avec sa spécification finale, rétablit `LBL-200` manquante pour `CUSTOMER-B` à 800 unités et annule `LBL-300`. L’instantané périmé conserve l’ancienne première commande, omet la deuxième et contient encore celle annulée. Les cas de transfert changent quantités, capacité, identifiants de dépendance et ajoutent une modification de spécification de la deuxième commande. Le vérificateur reconstitue indépendamment la source conservée ; le candidat ne redéfinit pas l’obligation en réécrivant son dossier.

Les résultats suivants sont identiques pour les deux méthodes réelles lors de la deuxième tentative. Chaque achèvement conserve le bon destinataire, produit/spécification, quantité et état final. Un refus accepte zéro unité. Aucune troisième commande annulée n’a été exécutée.

| Cas | Contrôle | LBL-100 / CUSTOMER-A | LBL-200 / CUSTOMER-B | Total accepté |
| --- | --- | --- | --- | --- |
| labels-base | Reprise | 1 100/1 100 — terminé | 800/800 — terminé | 1 900 |
| labels-base | Secours | 1 100/1 100 — terminé | 800/800 — terminé | 1 900 |
| labels-base | Contrainte | 1 100/1 100 — terminé | 0/800 — refusé | 1 100 |
| labels-transfer-a | Reprise | 700/700 — terminé | 900/900 — terminé | 1 600 |
| labels-transfer-a | Secours | 700/700 — terminé | 900/900 — terminé | 1 600 |
| labels-transfer-a | Contrainte | 700/700 — terminé | 0/900 — refusé | 700 |
| labels-transfer-b | Reprise | 600/600 — terminé | 500/500 — terminé | 1 100 |
| labels-transfer-b | Secours | 600/600 — terminé | 500/500 — terminé | 1 100 |
| labels-transfer-b | Contrainte | 600/600 — terminé | 0/500 — refusé | 600 |
| labels-transfer-c | Reprise | 1 200/1 200 — terminé | 1 000/1 000 — terminé | 2 200 |
| labels-transfer-c | Secours | 1 200/1 200 — terminé | 1 000/1 000 — terminé | 2 200 |
| labels-transfer-c | Contrainte | 1 200/1 200 — terminé | 0/1 000 — refusé | 1 200 |

Les capacités de secours contraintes sont respectivement de 1 500, 1 000, 700 et 1 300 unités. Le calendrier déterministe laisse avancer la première transaction prioritaire ; les capacités restantes—400, 300, 100 et 100—ne couvrent pas les deuxièmes commandes. L’ordre inverse des gagnants est testé séparément. La comparaison n’est pas un concours aléatoire de politiques d’allocation.

Dans les 12 cellules de chaque méthode, **20 obligations sur 24** et **17 200 unités sur 20 400** sont acceptées. Les quatre deuxièmes commandes refusées laissent **3 200 unités inexécutées**. Ces sommes portent sur des contrats synthétiques distincts, pas sur le volume de production d’un client unique. Les obligations terminées incorrectes, dupliquées, tardives ou sans justification sont chacune au nombre de zéro dans la comparaison qualifiée. Aucun défaut critique de sûreté n’a été observé dans ce modèle testé.

| Contrôle | Assertion du test | Verdict cible | Stade des preuves | Promesse complète | Sûreté |
| --- | --- | --- | --- | --- | --- |
| Reprise réalisable | PASSED | COMPLETED | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | DEMONSTRATED |
| Secours réalisable | PASSED | COMPLETED | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | DEMONSTRATED |
| Perturbation contrainte | PASSED | PARTIAL | LOCAL_SOFTWARE_EXECUTION | **FAILED** | DEMONSTRATED |

Codes partagés : `PASSED` = assertion réussie ; `COMPLETED` = terminé ; `PARTIAL` = partiel ; `DEMONSTRATED` = démontré ; `FAILED` = échec ; `NOT_ESTABLISHED` = non établi ; `NOT_RUN` = non exécuté. `LOCAL_SOFTWARE_EXECUTION` désigne l’exécution logicielle locale ; `FRESH_VERIFICATION_CHALLENGE`, l’épreuve de vérification fraîche ; `CHECKER_MUTATION_EXERCISE`, l’exercice de mutation du vérificateur.

Un refus sûr préserve l’invariant de capacité mais ne préserve pas l’obligation du deuxième client. Les cas contraints ne constituent pas une exécution complète. Cette distinction figure dans les résultats techniques et les deux Passeports linguistiques.

Toutes les cellules contraintes ont observé l’indisponibilité principale, la concurrence sur la capacité restante, la perte d’accusé après réalisation durable, la nouvelle tentative pendant l’incertitude, l’arrêt réel du service, celui du candidat et le rapprochement au redémarrage. Chacune consigne une nouvelle tentative et deux redémarrages. Clés stables et reçus durables rapprochent le travail achevé sans créer de deuxième réalisation. Il s’agit d’une suppression locale des doublons lors d’interruptions testées, pas d’une livraison universellement garantie exactement une fois.

## 3. Temps, ressources et coûts complets manquants

L’échéance logique est l’instant 100 ; l’échéance réelle est de 30 000 ms ; l’objectif de reprise principale est de 15 000 ms. Ce sont des limites configurées d’acceptation, pas des estimations commerciales. L’achèvement utilise une observation exacte de confiance après export/fsync comme borne supérieure prudente. La transition antérieure du reçu est présentée séparément. Les observations absentes restent non établies ; une borne tardive peut refuser prudemment une persistance survenue plus tôt. L’acceptation de la reprise compare l’observation monotone exacte à la limite inclusive en nanosecondes, pas les millisecondes arrondies affichées.

Le tableau présente les 12 paires. La durée réelle couvre l’intervalle mesuré du contrôleur. La borne de sortie est la dernière observation d’artefact **accepté**, relative au début ; dans les cas contraints, elle décrit uniquement la première commande terminée, pas toute la promesse. Les valeurs sont en millisecondes, arrondies à trois décimales ; les nanosecondes exactes restent dans les fichiers JSON.

| Cas | Contrôle | Durée conventionnelle | Durée banc | Borne sortie conventionnelle | Borne sortie banc |
| --- | --- | --- | --- | --- | --- |
| labels-base | Reprise | 185,704 | 192,737 | 138,536 | 154,133 |
| labels-base | Secours | 154,521 | 141,992 | 117,311 | 105,038 |
| labels-base | Contrainte | 301,391 | 300,662 | 206,149 | 212,879 |
| labels-transfer-a | Reprise | 123,234 | 126,309 | 95,191 | 98,162 |
| labels-transfer-a | Secours | 140,151 | 137,607 | 104,924 | 98,523 |
| labels-transfer-a | Contrainte | 316,363 | 326,561 | 214,913 | 208,516 |
| labels-transfer-b | Reprise | 183,216 | 176,334 | 137,212 | 126,816 |
| labels-transfer-b | Secours | 152,341 | 114,990 | 114,448 | 88,244 |
| labels-transfer-b | Contrainte | 339,709 | 324,555 | 241,190 | 213,372 |
| labels-transfer-c | Reprise | 153,450 | 161,540 | 114,199 | 122,837 |
| labels-transfer-c | Secours | 148,381 | 159,699 | 115,286 | 121,098 |
| labels-transfer-c | Contrainte | 329,290 | 271,192 | 229,499 | 191,075 |

Les durées affichées de reprise principale pour base, transfert A, B et C sont respectivement **124/140**, **84/85**, **113/114** et **101/109 ms**, dans l’ordre conventionnel/banc d’essai. Les cas de secours et contraints ne prétendent pas avoir rétabli le principal et n’en consignent pas de durée de reprise.

### Ressources des deux tentatives

Chaque colonne de méthode additionne ses 12 enregistrements d’exécution. La première tentative reste non qualifiée ; ses observations de ressources sont conservées comme coût d’une tentative réelle, pas comme acceptation favorable. Les valeurs processeur sont des différences utilisateur/système distinctes pour les enfants et le contrôleur. Le processeur cumulé des enfants simultanés peut dépasser le temps écoulé. Le stockage mesure les contenus à la borne consignée, avant les fichiers finaux du contrôleur/rapports et les métadonnées d’index, sans l’autorité conservée séparément. La deuxième tentative conserve en plus l’état actif et une base durable de preuve distincte : son périmètre de stockage diffère matériellement.

| Mesure | T1 conventionnel | T1 banc | T2 conventionnel | T2 banc |
| --- | --- | --- | --- | --- |
| Durée réelle d’exécution (ms) | 2 121,971 | 2 125,257 | 2 527,752 | 2 434,178 |
| Processeur enfants utilisateur (ms) | 1 724,224 | 1 683,202 | 1 886,864 | 1 796,073 |
| Processeur enfants système (ms) | 388,474 | 495,574 | 448,857 | 457,749 |
| Processeur contrôleur utilisateur (ms) | 82,160 | 82,456 | 159,312 | 164,946 |
| Processeur contrôleur système (ms) | 16,174 | 18,859 | 35,993 | 28,168 |
| Stockage consigné (octets) | 941 419 | 941 259 | 2 336 441 | 2 335 721 |
| Demandes au relais | 104 | 104 | 104 | 104 |
| Nouvelles tentatives | 4 | 4 | 4 | 4 |
| Redémarrages | 8 | 8 | 8 | 8 |
| Interventions humaines pendant l’exécution | 0 | 0 | 0 | 0 |

Les deux méthodes utilisent **104 demandes au relais, quatre nouvelles tentatives et huit redémarrages par tentative comparative**. Le zéro d’interventions humaines ne concerne que l’exécution autonome. Il ne signifie pas absence de travail d’ingénierie, d’investigation, de préparation, d’intégration ou de revue. Le premier échec et sa correction ont nécessité un travail de développement dont la durée n’a pas été mesurée.

Mémoire maximale, préparation/intégration, processeur de vérification/rapport, tarifs, prix et coûts commerciaux complets restent inconnus. Les durées de vérification fraîche des suites et de chaque épreuve sont mesurées séparément ; elles ne remplacent pas ces catégories manquantes. La devise USD et le budget synthétique nul sont des entrées, pas des budgets clients ni des dépenses observées. Aucune économie estimée ni affirmation de méthode moins coûteuse n’est justifiée.

Les durées favorisent parfois l’une ou l’autre méthode. Une observation séquentielle par cellule sur un hôte partagé, l’ordre fixe conventionnel → banc → IA, les effets partagés de cache/interpréteur/fichiers et la finalisation modifiée entre tentatives empêchent d’affirmer un gain stable de vitesse. De petits écarts d’octets reflètent en partie les identifiants consignés ; ils n’établissent pas un avantage de stockage. Aucun échec critique n’est fondu dans une moyenne favorable.

## 4. Comparaison équitable, ablation et transfert

La méthode conventionnelle reçoit les mêmes journal et instantané, permissions, capacité/dépendances, outils, pannes et possibilités d’observation. Elle utilise le rapprochement ordinaire des sources, des transactions, des clés idempotentes stables et la recherche d’état durable. Le banc ajoute un contrôle de cohérence de l’état restauré. Les deux partagent les services et le vérificateur frais ; l’oracle et les preuves d’acceptation conservées restent inaccessibles aux candidats. La mécanique commune contribue donc aux deux résultats. La comparaison n’isole pas un avantage de marque ou de privation sélective de protections ordinaires.

Les **12 paires fonctionnelles sont à égalité**. L’hypothèse comparative reste **NON ÉTABLIE** en tant qu’amélioration : la suite démontre des méthodes exécutables et une discipline de preuve, pas davantage de résultats acceptés ou des économies complètes grâce au contrôle supplémentaire du banc.

Les trois cas de transfert apportent neuf contrôles exécutés par méthode et les mêmes résultats avec la réutilisation conventionnelle ordinaire. Leurs 15 obligations acceptées par méthode totalisent 12 300 unités sur 14 700 requises ; la quantité contrainte manquante est de 2 400. Les intervalles d’exécution cumulés sont de 1 886,135 ms pour la méthode conventionnelle et 1 798,787 ms pour le banc, avec 78 demandes, trois nouvelles tentatives et six redémarrages chacun. Ils décrivent cette réutilisation, pas une réduction mesurée du travail d’adaptation.

Aucune modification spécifique de l’exécuteur n’a été nécessaire pour chaque cas pendant la deuxième suite : quantités, spécifications et dépendances sont des entrées, et la copie du dépôt est restée propre. Préparation et intégration n’ont pas été chronométrées. La deuxième tentative a bien exigé une correction générale de finalisation après le premier échec, consignée plutôt qu’attribuée à un transfert gratuit. Les variantes réservées hors démonstration sont publiques, rédigées, petites et structurellement apparentées. Les identifiants de dépendance changent ; cela ne démontre ni nouveau réseau physique ni avantage de découverte pour des entreprises sans rapport.

Aucun modèle local approprié déjà autorisé n’a été fourni ; ni `ollama` ni `llama-cli` n’a été trouvé. L’adaptateur et le protocole borné existent, mais les **12 cellules IA sont NON EXÉCUTÉES**, sans performance simulée. Leur exécution exigerait un modèle/environnement local inspecté, une identité explicite de capacité, un confinement et des observations équivalents, puis une nouvelle exécution consignée. L’aide à l’implémentation de ce dépôt ne constitue pas un banc de performance de l’adaptateur IA.

## 5. Résultats adverses et mutations conservés

La suite conserve huit cas, un contrôle positif et quatre nouvelles exécutions locales au total. Les autres cas copient les preuves positives, avec leurs anciens Passeports favorables. Leurs ressources d’exécution ne doivent pas être comptées plusieurs fois. `TARGET_RESULT.json`, `REFERENCE_RESULT.json` et `CHALLENGE.json` restent distincts. Toutes les assertions externes réussissent ; les affirmations de qualification des trois vérificateurs volontairement défectueux échouent comme prévu.

| Cas | Assertion | Verdict cible | Stade | Affirmation du composant | Promesse de référence | Unités acceptées/requises |
| --- | --- | --- | --- | --- | --- | --- |
| no-journal-ablation | PASSED | PARTIAL | LOCAL_SOFTWARE_EXECUTION | FAILED | FAILED | 0/1 900 |
| rewritten-1850 | PASSED | PARTIAL | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | FAILED | 1 100/1 900 |
| missing-reference-pin | PASSED | NOT_ESTABLISHED | FRESH_VERIFICATION_CHALLENGE | DEMONSTRATED | NOT_ESTABLISHED | 0/1 900 |
| changed-artifact | PASSED | FAILED | FRESH_VERIFICATION_CHALLENGE | DEMONSTRATED | FAILED | 0/1 900 |
| shared-failed-dependency | PASSED | REFUSED | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | FAILED | 0/1 900 |
| mutant-ignores-byte-integrity | PASSED | DEMONSTRATED | CHECKER_MUTATION_EXERCISE | FAILED | FAILED | 0/1 900 |
| mutant-ignores-revocation | PASSED | DEMONSTRATED | CHECKER_MUTATION_EXERCISE | FAILED | FAILED | 0/1 900 |
| mutant-rejects-valid-recovery | PASSED | FAILED | CHECKER_MUTATION_EXERCISE | FAILED | DEMONSTRATED | 1 900/1 900 |

L’ablation sans journal conserve les protections ordinaires et refuse les obligations périmées, acceptant 0/1 900. Elle démontre la nécessité du rapprochement dans ce cas, pas une valeur supplémentaire de l’IA. Le dossier candidat cohérent de 1 850 unités laisse un contrat conservé de 1 900 : seules les 1 100 unités de la première commande inchangée sont acceptées. L’empreinte indépendante absente conserve l’affirmation métier sous-jacente **NON ÉTABLIE**, tandis que le vérificateur préserve correctement l’incertitude.

Pour les mutants d’intégrité et d’autorisation, `PASSED` signifie que l’assertion adverse révèle correctement l’acceptation indue. Le mutant testé annonce `DEMONSTRATED`, mais sa qualification est **FAILED — ÉCHOUÉE**. Le mutant du contrôle positif rejette à tort un travail valide et reste également non qualifié. Le retrait d’autorisation est ici une modification synthétique déclarée de preuves copiées, rescellées par une autorité de test privilégiée, pas un retrait exécuté en direct par le service ; des tests distincts couvrent ce dernier. Aucun mutant limité à l’appel ne modifie le code installé.

La revue indépendante a aussi révélé un défaut de développement distinct : admission et vérification partageaient une fonction sémantique de rejeu. Une mutation commune a produit puis accepté indûment 1 850 unités contre l’autorité originale de 1 900. Le contre-exemple et la vérification corrigée sont conservés sous `development/harness-review-shared-replay-usdotr7w/`. Le vérificateur final utilise son propre rejeu et n’importe pas la fonction de décision du producteur sur les obligations restantes. C’est une mutation sémantique supplémentaire du producteur, distincte des trois mutants ciblés ci-dessus. Des chemins indépendants dans ce projet ne constituent pas une certification tierce.

## 6. Tests exécutés et historique préservé

L’exécution consolidée hors ligne a réussi **245 tests en 15,384 secondes, sans test ignoré** : **160 tests du banc et 85 régressions existantes**. Le journal réel est `validation/finalization-complete-tests.log`.

| Fichier de tests | Nombre | Portée |
| --- | --- | --- |
| [test_harness_boundaries.py](../../tests/test_harness_boundaries.py) | 14 | Protocole, permissions, délais et vrais processus |
| [test_harness_challenges.py](../../tests/test_harness_challenges.py) | 11 | Épreuves adverses, ablation et mutations conservées |
| [test_harness_cli.py](../../tests/test_harness_cli.py) | 10 | Interface bilingue et couverture fraîche de suite |
| [test_harness_controller.py](../../tests/test_harness_controller.py) | 14 | Contrôles exécutés, adaptateurs, équité et transfert |
| [test_harness_finalization.py](../../tests/test_harness_finalization.py) | 9 | Preuve de base fermée et finalisation échouée |
| [test_harness_reporting.py](../../tests/test_harness_reporting.py) | 16 | Faits français/anglais, incertitude et portée des épreuves |
| [test_harness_services.py](../../tests/test_harness_services.py) | 34 | Registre durable, concurrence, arrêts et 432 traces finies |
| [test_harness_verifier.py](../../tests/test_harness_verifier.py) | 52 | Acceptation indépendante autorité/source/sortie et mutations |
| [test_bilingual_cli.py](../../tests/test_bilingual_cli.py) | 17 | Interface bilingue existante |
| [test_bilingual_repository.py](../../tests/test_bilingual_repository.py) | 5 | Politique linguistique existante du dépôt |
| [test_continuity_omega.py](../../tests/test_continuity_omega.py) | 29 | Prototype historique de recherche |
| [test_continuity_passport.py](../../tests/test_continuity_passport.py) | 14 | Comportement existant du Passeport |
| [test_research_tools.py](../../tests/test_research_tools.py) | 19 | Outils existants de recherche/publication |
| [test_web_interactions.py](../../tests/test_web_interactions.py) | 1 | Interactions bilingues existantes du site |

Les exécutions CI de cette révision ont aussi réussi : [comparaison et épreuves du banc](https://github.com/MontrealAI/CONTINUITY/actions/runs/42289983351), et [régressions du dépôt et vérification historique](https://github.com/MontrealAI/CONTINUITY/actions/runs/42289983392). Leur réussite consignée figure dans l’enregistrement de livraison lisible par machine.

Le modèle fini épuise **432 traces de trois étapes** : deux capacités × six actions au cube, deux obligations d’une unité, instants 0/1/2 et expiration à 2. Il n’épuise pas les quantités arbitraires, historiques longs, toutes les transitions de la deuxième commande ou les ordonnancements du système. Concurrence réelle, arrêts, écritures partielles, bornes temporelles, mutations et variantes sont des contrôles supplémentaires sélectionnés. Une suite finie réussie n’est pas une preuve générale.

Le contrôle de copie vérifie **74 fichiers inchangés et quatre adaptations web déjà documentées** dans le périmètre migré de 78 fichiers. La cohérence de l’article historique reste en édition 1.1.1, anglais 27 pages/français 29 pages, avec 31 empreintes enregistrées ; le compagnon reste qualifié seulement comme présentation empaquetée. Le banc ne renforce rétroactivement ni articles, PDF, identités de preuve, publications, tests originaux ou affirmations commerciales. Le dépôt original du Lab n’a pas été modifié.

Les échecs de développement figurent dans [VALIDATION_HISTORY.md](VALIDATION_HISTORY.md) : le contrôle intermédiaire de 95 tests sur métadonnées/schéma a eu 24 échecs et deux erreurs ; son journal brut complet n’a pas été capturé et n’a pas été inventé. Une exécution distincte de 48 tests a eu trois erreurs de nettoyage de mutation, suivie d’une exécution corrigée réussie ; les deux journaux sont conservés. Les anciennes conventions d’empreinte de reçu gardent leurs sorties et identités sources initiales. Cette conservation n’en fait pas des résultats actuels qualifiés.

## 7. Reproduire et vérifier indépendamment

Utiliser une copie propre et de nouveaux chemins de sortie. Le banc exige Python 3.10+ sur Linux x86_64 avec seccomp BPF fonctionnel ; il utilise la bibliothèque standard et SQLite, sans API payante, secret ou téléchargement de modèle. Git consigne la révision de l’implémentation ; Node.js est également nécessaire pour la régression du site existant.

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git CONTINUITY-harness-review
cd CONTINUITY-harness-review
git checkout --detach fa9da1f54acfaa82510a4b6b805c2980d3e5b31d
python3 -m continuity_harness --language fr demo --out /tmp/continuity-demo-v0.1
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-demo-v0.1
python3 -m continuity_harness --language en compare --out /tmp/continuity-comparison-v0.1
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuity-comparison-v0.1
python3 -m continuity_harness --language fr challenge --out /tmp/continuity-challenges-v0.1
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

Pour un cas individuel, utiliser chemins et empreinte conservée indépendamment de son `INDEX.json` ou Passeport :

```sh
python3 -m continuity_harness --language fr verify --run RUN_DIRECTORY --authority AUTHORITY_DIRECTORY --reference-sha256 RETAINED_REFERENCE_SHA256
```

Ne pas remplacer l’empreinte par un nouveau calcul issu des données candidates. La vérification individuelle d’une réalisation partielle correcte renvoie 3 parce que la promesse complète échoue ; le test contraint global peut néanmoins réussir. `verify-suite` concerne les index de démonstration/comparaison. Pour une épreuve, la vérification ordinaire reproduit la référence inchangée ; relancer `challenge` dans un nouveau répertoire reproduit les mutants limités. Les anciens répertoires et rapports ne sont pas écrasés. Identités, durées et empreintes peuvent différer lors d’une nouvelle exécution tout en conservant des résultats métier comparables.

| Fichier archivé | SHA-256 |
| --- | --- |
| `attempt-2/QUALIFICATION.json` | `f68d465beba111a3b95c3d7ce40b0b66f7af6a40a0499c7e289b9a9cc3605456` |
| `attempt-2/demonstration/SUMMARY.json` | `c47e80fce83c6bd318fe132a869104e5a35f2bded8c266bbb0a0c4cc8a741227` |
| `attempt-2/comparison/SUMMARY.json` | `17596a837f221db72988da0d701e903802326d78a14022aa57157f2f0c66af82` |
| `attempt-2/challenges/SUMMARY.json` | `3fcf5138f0324edf6114dbf2e5be97fa014f0be8476765ed3782ea1d4ff01cd2` |

L’archive mesure **313 736 octets**, avec le SHA-256 `a7115c8d499377152d6e4c1e83e44ca5997b5452ff3847ad061e73b4bac711b9`. Après extraction, les **1 722 fichiers du manifeste** correspondent tous à leurs empreintes. Une vérification fraîche distincte de la comparaison extraite renvoie 0, avec 24 exécutions, 12 non-exécutions et aucune assertion échouée ni sûreté non établie. Une vérification séparée ultérieure avant empaquetage a également réussi. Les reçus sont conservés dans [PACKAGE_CHECK.json](../../evidence/harness-v0.1/PACKAGE_CHECK.json) et l’enregistrement de livraison.

Après téléchargement de l’archive, inspecter sa comparaison conservée avec :

```sh
tar -xJf continuity-harness-v0.1-evidence.tar.xz -C /tmp
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuity-harness-v0.1-evidence/attempt-2/comparison
```

Ce sont les empreintes des octets bruts des fichiers archivés nommés, pas une authentification client réelle ou une signature externe. Les empreintes d’autorité par exécution et manifestes complets restent dans l’archive et l’enregistrement de livraison.

## 8. Publication et preuves encore nécessaires

Le code qualifié est publié sur [`feat/continuity-harness-v0.1`](https://github.com/MontrealAI/CONTINUITY/tree/feat/continuity-harness-v0.1). Ce rapport identifie cette révision exacte ; la publication ultérieure des documents et preuves constitue un commit distinct. L’état de demande de fusion et de fusion relève du reçu final de publication et ne découle pas de la seule branche publiée. Aucun déploiement de production, contact client, réservation réelle, service payant, création de secret ou changement de permission externe ne fait partie de ces expériences.

La cause non résolue des fichiers auxiliaires de la première tentative demeure une limite. La deuxième tentative qualifie le chemin de finalisation testé et les preuves conservées aux instants observés, pas une immunité à un hôte hostile ou à toute panne future. Hôte, noyau, lanceur/imports de confiance, contrôleur, service, journal rédigé, horloge et vérificateur restent de confiance. Le confinement seccomp est éprouvé après les imports fiables ; les modules Python tiers arbitraires et une protection complète de l’hôte contre le déni de service ne sont pas qualifiés. Les voies logiques partagent hôte et registre ; les artefacts sont logiciels, pas des biens physiques.

Avant un exercice réel autorisé, les preuves supplémentaires minimales sont :

1. Autorité réelle des commandes, garde et complétude des sources jusqu’à une borne convenue, avec modifications et annulations.
2. Fenêtre de capacité réelle d’un fournisseur qualifié et preuves de dépendances/domaines de panne, avec permissions explicites d’activation et de partage.
3. Acceptation réelle convenue, contrôles destinataire/spécification/quantité, échéances et horloges, plus rapprochement des réalisations externes incertaines.
4. Environnement jetable ou expressément isolé, opérateurs nommés, interventions consignées, limites de retour arrière et autorisation de l’exercice.
5. Mesures du travail de préparation, intégration, vérification et exploitation, tarifs/prix explicites et obligations commerciales complètes avant d’affirmer économies ou marché viable.

La prochaine décision dispose désormais d’un système local exécutable et inspectable. Sa capacité à réduire l’effort de continuité d’une autre entreprise, à dépasser une procédure conventionnelle compétente ou à soutenir un arrangement commercial viable reste une question empirique exigeant ces preuves supplémentaires.
