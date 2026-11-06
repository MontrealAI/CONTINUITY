# CONTINUITÉ Ω — Produit numérique d’étiquettes et spécification d’acceptation

[English](PRODUCT.md) · [Architecture](ARCHITECTURE.fr.md) · [Modèle de menace](THREAT_MODEL.fr.md)

## Le produit promis

L’obligation porte sur un **paquet numérique de travail contenant le contenu littéral et substantiel d’étiquettes pour des unités déterminées**. Un processus destinataire local séparé lit réellement ses octets et importe le contenu accepté dans des lignes SQLite durables. Métadonnées de quantité, empreinte de spécification, état d’achèvement ou reçu autoémis ne suffisent pas à satisfaire ce contrat.

Il s’agit d’une nouvelle obligation numérique. Elle n’accomplit pas l’engagement historique d’étiquettes physiques. Son acceptation établit le contenu sémantique exact et la couverture des unités dans le format pris en charge. Elle n’établit ni mise en page, rendu, polices, lisibilité de codes-barres, aptitude à l’impression, qualité d’impression, adhésion, performance d’emballage, biens physiques ou acceptation d’un client externe.

La spécification d’acceptation originale est conservée hors du contrôle du candidat. Chaque obligation active fixe destinataire, révision, quantité, échéance et spécification matérialisée. Les modifications sont rejouées depuis le journal source conservé avant le gel du contrat ; les obligations annulées restent annulées. Aucune unité ne peut être perdue pendant la reprise.

## Version et contenu pris en charge

L’identifiant de format du produit et de sa spécification est `continuity-economy/label-job/v1`. Les fichiers sont du JSON UTF-8 borné, de 1 Mio maximum chacun. Versions, champs et fonctionnalités non pris en charge sont refusés. Les clés des objets JSON sont uniques ; quantités et ordinaux sont des entiers exacts, jamais des chaînes ou booléens. Valeurs non finies, nombres à virgule flottante, structures mal formées et plages invalides sont refusés.

Les constructeurs directs et interfaces de commande des deux services valident le schéma neutre complet `continuity-economy/contract/v1` avant de créer une base ou un répertoire de résultats. Cela comprend rejeu des sources, identifiants, fournisseurs, fenêtres, bornes et champs racines interdits. Le contrat conservé est copié contre une modification ultérieure par l’appelant. L’exercice complet pris en charge comporte au plus 8 obligations et 8 lots fixes actifs ; sa déclaration intégrale figure dans [le schéma contractuel](../../continuity_economy/schema.py). Une admission commune ne constitue pas une acceptation de contenu commune.

La spécification matérialisée possède exactement les champs suivants :

| Champ | Sens |
| --- | --- |
| `format` | Identifiant du format pris en charge |
| `sku` | Référence exacte du produit |
| `name_en`, `name_fr` | Noms exacts du produit en anglais et en français |
| `instructions_en`, `instructions_fr` | Instructions substantielles exactes en anglais et en français |
| `lot` | Identité exacte du lot de matière |
| `serial_prefix` | Préfixe des numéros uniques liés aux ordinaux |

Le texte littéral est limité à 160 caractères, sans caractères de contrôle. Le contrat racine impose également ses contraintes d’identifiants plus strictes. Aucune traduction, abréviation, normalisation ou substitution n’est permise pendant la production : les deux textes linguistiques conservés doivent correspondre littéralement. Chaque obligation comporte au plus 2 000 unités.

L’enveloppe d’un produit contient exactement :

```text
schema, run_id, contract_id, contract_sha256,
obligation_id, revision, recipient,
production_id, arrangement_id, provider_id, delivery_id,
capacity_key, lot_id, attempt, first_unit, last_unit, supersedes, labels
```

Le tableau `labels` possède un objet par ordinal de la plage inclusive déclarée, dans l’ordre. Chaque objet contient exactement :

```text
ordinal, serial, sku, name_en, name_fr, instructions_en, instructions_fr, lot
```

Chaque `serial` est le `serial_prefix` conservé suivi de l’ordinal sur six chiffres. Ordinaux répétés, numéros répétés, trous, unités réordonnées ou champs littéraux différents font échouer l’examen. Un paquet de 100 unités doit contenir 100 objets d’étiquette substantiels ; une déclaration `quantity:100` seule ne suffit pas.

## Lots et identités de correction

Si `allow_split` vaut vrai, `lot_size` figé partitionne les ordinaux de chaque obligation active. Le dernier lot peut être plus petit. Sinon, l’obligation entière forme un lot, même lorsque sa quantité dépasse `lot_size`. Les plages exactes découlent du contrat conservé et ne constituent pas une souplesse choisie par le candidat.

Pour le lot `ORDER.L001` de l’accord `proposal-001` :

| Étape | Première tentative | Correction prise en charge |
| --- | --- | --- |
| Production et clé de capacité | `proposal-001.ORDER.L001.A1` | `proposal-001.ORDER.L001.A2` |
| Livraison | `proposal-001.ORDER.L001.A1.D` | `proposal-001.ORDER.L001.A2.D` |
| `supersedes` | `null` | `proposal-001.ORDER.L001.A1.D` |

La correction doit désigner la première livraison existante et durablement **refusée** du même accord et du même lot. Une `A2` initiale, la correction d’une livraison acceptée, une plage modifiée ou un prédécesseur d’un autre accord sont refusés. Le maximum est de deux tentatives lorsque le contrat permet une correction. Une réparation ne peut écraser un fichier, reçu, verdict ou unité acceptée antérieur.

Une nouvelle tentative exige sa propre réservation de capacité et sa charge de production. Une nouvelle requête stable pour la même tentative retrouve l’état précédent sans nouvelle facturation ni génération d’une seconde copie. Une requête différente sous une clé existante est un conflit, pas une modification autorisée.

Un autre accord ne peut commencer une nouvelle `A1` qu’après constatation par le courtier de l’annulation durable de l’ancien accord et de l’absence de travail déjà accepté, puis acceptation et financement distincts du nouvel accord. Le vérificateur frais contrôle ces conditions et tous les coûts antérieurs. Le destinataire examine le contenu de cette A1 sans la confondre avec A2 ; il ne décide pas lui-même de l’autorisation économique.

Si une partie du contenu est déjà acceptée et que la suite échoue, l’accord reste `ACTIVE`. Le courtier refuse l’annulation après toute décision réelle d’acceptation du destinataire, même si son délai ou son accusé reste incertain. Cette version ne possède aucune opération de règlement partiel : séquestre restant, responsabilités et sous-ensemble accepté restent durables et non résolus. Il ne s’agit ni d’une livraison complète ni d’un paiement achevé. La résolution exige une procédure de règlement explicitement autorisée ; effacer silencieusement l’acceptation ou libérer son financement n’est pas pris en charge.

## Matérialisation, réception et acceptation

Le producteur conserve le contenu généré complet dans sa base avant export. Il exporte les mêmes octets par fichier temporaire, synchronisation du fichier, création atomique et synchronisation du répertoire. Un arrêt pendant l’export laisse le contenu durable et tout fichier partiel inspectables. Le redémarrage réemploie ce contenu ; un fichier existant contradictoire est refusé.

Le contrôleur autorise le transfert, compare les octets exportés au registre du producteur et les copie dans la boîte du destinataire. L’opération `receive` conserve les octets réels et les métadonnées de réception sans déclarer une acceptation sémantique. Les octets corrompus ou tronqués restent la preuve d’une tentative reçue susceptible d’être refusée ; ils ne sont pas supprimés.

L’opération séparée `inspect` :

1. Valide l’enveloppe bornée et les liens exacts entre exécution, contrat, obligation, révision, destinataire, lot, tentative et clé de capacité.
2. Vérifie que l’obligation conservée est active, que ses sources sont déclarées complètes et que sa plage correspond au lot figé.
3. Vérifie indépendamment chaque champ littéral, ordinal et numéro selon la spécification conservée.
4. Vérifie le prédécesseur de correction permis et exclut les unités déjà acceptées par une autre livraison.
5. Vérifie le temps logique, consigne la décision et importe transactionnellement les unités littérales réelles.
6. Consigne séparément une observation monotone durable après validation de la transaction. L’échéance logique et l’échéance en temps écoulé doivent toutes deux être respectées.

Le destinataire n’importe pas la fonction de génération du producteur. Le vérificateur frais implémente ses propres contrôles sémantiques et rapproche les lignes importées des octets réels du produit. Ces implémentations partagent leur auteur et la confiance dans l’hôte ; elles ne constituent pas une certification par un tiers.

## Registres durables et interface de service

Le producteur conserve `productions`, les demandes `attempts`, les observations de matérialisation `observations` et les `events`. Le destinataire conserve les `receipts` bruts, les `decisions` immuables, les `observations` après validation, les `imported_units` littérales et les `events`. Les métadonnées imposent le même contrat conservé lors de la réouverture d’une base.

| Processus | Commande de lancement | Opérations |
| --- | --- | --- |
| Producteur | `python3 -m continuity_economy.producer --db DB --artifacts PRODUCTS --contract CONTRACT` | `produce`, `status`, `snapshot`, `checkpoint` |
| Destinataire | `python3 -m continuity_economy.receiver --db DB --inbox INBOX --contract CONTRACT` | `receive`, `inspect`, `status`, `snapshot`, `checkpoint` |

Il s’agit d’interfaces internes de processus de confiance. Les opérateurs emploient normalement les commandes principales `python3 -m continuity_economy`. Une requête suit la forme `{"id":"request-1","op":"inspect","args":{"delivery_id":"…","now_tick":1},"hooks":[]}`. La réponse conserve son identité et renvoie un résultat structuré ou un code d’erreur stable accompagné d’explications anglaise et française. L’aide des services présente les deux langues.

Les instantanés renvoient des métadonnées et nombres bornés, pas l’ensemble des octets ou lignes d’étiquettes. Les preuves finales contiennent les bases autonomes et fichiers réels : le vérificateur frais peut examiner leur substance sans se fier au résumé.

## Temps et signification des défaillances

Les échéances contractuelles sont inclusives. L’observation d’acceptation doit survenir au plus tard à l’échéance logique de l’obligation et à la limite conservée en temps écoulé. Horodatages du producteur et de réception ne peuvent remplacer l’observation après validation de l’acceptation.

Un arrêt après validation de la décision mais avant son observation laisse le respect du délai non établi jusqu’à une observation ultérieure. Celle-ci peut établir un retard ; elle ne peut inventer une réussite antérieure. Un accusé perdu après une observation durable dans les délais se résout grâce à l’identité existante de livraison, en conservant décision et instant originaux. Un rejeu n’insère jamais une seconde unité acceptée.

Unités demandées refusées, unités réellement matérialisées, tentatives reçues et unités acceptées sont des mesures distinctes. Un paquet tronqué peut avoir une plage demandée connue mais aucune unité substantielle validée indépendamment. Une preuve absente ne signifie ni travail nul ni preuve favorable.

Les [tests du produit](../../tests/test_economy_product.py) éprouvent une importation substantielle de 1 900 unités, un contenu erroné malgré des métadonnées correctes, corruption, troncature, doublons, révisions périmées, mauvais destinataires, annulation, correction explicite, concurrence et interruptions de véritables processus. Ils modifient aussi le résultat de génération pour vérifier que l’acceptation indépendante détecte le contenu altéré. Ce sont des contrôles exécutables bornés, non une garantie universelle de livraison.
