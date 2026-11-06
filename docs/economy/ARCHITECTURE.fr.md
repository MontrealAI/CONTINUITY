# CONTINUITÉ Ω — Architecture de l’expérience économique

[English](ARCHITECTURE.md) · [Contrat du produit](PRODUCT.fr.md) · [Modèle de menace](THREAT_MODEL.fr.md) · [Expérience préenregistrée](EXPERIMENT.md)

## Portée et frontière historique

La version 0.2.0 préserve une **nouvelle obligation de paquet numérique d’étiquettes**. Elle produit un contenu bilingue substantiel, transfère ses octets et importe les unités acceptées dans une base du destinataire contrôlée séparément. Elle examine aussi si une solution synthétique rédigée pour l’exercice respecte les contraintes déclarées des participants. Ces évaluations restent distinctes. Aucune n’établit une livraison physique, l’authenticité d’un client, des paiements réels ou une demande commerciale.

La base qualifiée reste le commit `396227d8da2f55f674f479de16089c7ce28ef290`, étiquette `continuity-harness-v0.1.0`. Son registre transactionnel de capacité, sa sérialisation stricte, son transport entre processus et son isolation du candidat sont réutilisés sans modifier le code ni les affirmations historiques. Dans cette expérience, un reçu d’exécution de la base établit une consommation de capacité ; il ne remplace jamais le contenu numérique ni l’acceptation du destinataire. L’attribution exacte figure dans [la provenance de l’expérience](../../experiments/economy-v0.2/PROVENANCE.json) et dans l’enregistrement d’implémentation de chaque contrôleur.

## Responsabilités et contrôle

| Composant | État contrôlé et responsabilité | Frontière |
| --- | --- | --- |
| Autorité de l’exercice | Contrat original, politiques des participants, journal source, paramètres de capacité, référence et sceau d’exécution | Hors de l’accès du candidat ; empreinte de référence fournie indépendamment |
| Contrôleur | Processus jetables, horloge consignée, autorisations du courtier, pannes rejouables, instantanés durables | Orchestration locale de confiance, sans indépendance organisationnelle |
| Adaptateur candidat | Propose allocations et conditions ; invoque les opérations permises | Mêmes informations et courtier pour les procédures conventionnelle et du banc d’essai |
| Service des participants | Décisions distinctes, consentements, versions des accords, fonds, retenues, coûts engagés et transferts modélisés | Le candidat ne peut modifier les politiques ni fabriquer l’acceptation |
| Services de capacité | Réservation, engagement, libération, expiration et consommation durable par fournisseur et fenêtre | Une allocation n’établit pas l’acceptation du destinataire |
| Producteur | Octets durables du produit, demandes de génération et observations de matérialisation | Ne peut établir sa propre livraison réussie |
| Destinataire | Spécification d’acceptation originale, octets reçus, décisions, observations après validation et unités littérales importées | Examen du contenu implémenté indépendamment |
| Vérificateur frais | Rejoue l’autorité conservée, les registres, le contenu réel et les preuves du destinataire | Aucun passeport enregistré ni verdict du producteur/destinataire ne constitue son oracle |
| Rapporteur | Passeports anglais/français issus d’un enregistrement structuré unique | Présente les évaluations sans les renforcer |

`continuity_economy/schema.py` définit le contrat versionné. `policy_schema.py` définit les données monétaires et de participation. `controller.py` possède le courtier. Producteur, destinataire et service des participants sont de véritables processus Python séparés avec état SQLite durable ; les candidats communiquent uniquement par messages bornés sur les entrées/sorties standard.

## Données figées et identifiants stables

Avant l’exécution, le contrôleur conserve les obligations matérialisées, le point d’arrêt du journal, la perte de reprise permise nulle, les révisions, destinataires, contenus exacts, échéances, fenêtres, ressources, permissions, actions autorisées, révocations, pannes et versions de schéma. Les deux méthodes reçoivent les mêmes informations contractuelles et politiques. L’empreinte de référence, le sceau conservé et les preuves finales d’acceptation ne font pas partie des entrées du candidat.

Une obligation couvre exactement les ordinaux `1..quantity`. Lorsque le fractionnement est permis, des lots fixes partitionnent cette plage ; sinon, l’obligation entière forme un lot. Aucun exécuteur ne peut réduire l’engagement pour l’adapter à une voie. Un changement d’engagement exige un nouveau contrat conservé et une évaluation distincte.

| Identité | Dérivation |
| --- | --- |
| Lot | `{obligation_id}.L{index:03d}`, indice initial 1 |
| Production et clé de capacité | `{agreement_id}.{lot_id}.A{attempt}` |
| Livraison | `{production_id}.D` |
| Ordre de capacité de la base | `{lot_id}.A{attempt}` |

La première tentative est `A1`. La seule correction prise en charge, `A2`, désigne la livraison `A1` du même accord et du même lot, refusée durablement. Sa clé de capacité et sa facturation de production distinctes conservent les deux tentatives. Une correction entre accords d’un engagement partiellement livré n’est pas prise en charge.

Avant toute acceptation par le destinataire, un accord échoué peut être annulé durablement puis remplacé par un accord accepté séparément, commençant à `A1`. Il s’agit d’une nouvelle production financée, pas d’une correction à coût réduit. Coûts antérieurs, capacité consommée et octets refusés restent présents. Courtier et vérificateur frais contrôlent annulation, absence d’engagements chevauchants et financement ; le destinataire vérifie indépendamment contenu correct et unicité des unités acceptées.

## Cycle effectivement exécuté

1. **Reprendre et proposer.** L’adaptateur peut restaurer le service principal depuis son état périmé et le journal protégé, employer le secours conventionnel ou rechercher des allocations compatibles permises. Toutes les conditions proposées et décisions des participants restent consignées, y compris les propositions refusées.
2. **Accepter une solution.** Le service des participants évalue l’intervalle de valeur défini de l’acheteur et son option externe, les coûts et seuils de participation des fournisseurs, les coûts du coordonnateur, les responsabilités, les consentements et les fonds actuellement disponibles. Une proposition ne devient un accord qu’après inscription durable de ces décisions et retenues de financement.
3. **Réserver et produire.** Le courtier vérifie permissions, dépendances, consentements actuels et fenêtre choisie. La capacité est réservée puis engagée. Le registre des participants comptabilise la tentative unique. Le producteur conserve les octets substantiels avant d’exporter le fichier. La consommation de capacité consigne ensuite la production locale réelle.
4. **Transférer et recevoir.** Après une nouvelle autorisation, le contrôleur copie le fichier réel dans la boîte de réception. Le destinataire conserve ces octets durablement. La réception seule n’accepte pas leur contenu.
5. **Examiner et accepter ou refuser.** Le destinataire analyse les octets selon son contrat conservé, importe transactionnellement les unités uniques correctes et consigne séparément une observation après validation de la transaction. Octets et décisions refusés restent présents. Une correction permise exige une nouvelle tentative et de nouvelles ressources.
6. **Régler ou résoudre un travail incomplet.** Le règlement exige une livraison acceptée dans les délais pour chaque lot alloué. Avant toute acceptation du destinataire, l’annulation libère les retenues restantes en conservant les coûts engagés et responsabilités d’annulation explicites. Après une décision d’acceptation, le courtier refuse l’annulation. Une solution partielle échouée reste `ACTIVE` avec séquestre restant et responsabilités conservés ; le règlement partiel est non pris en charge et non résolu. Le travail accepté n’est pas effacé, les fonds retenus ne sont pas considérés comme payés et l’engagement partiel n’est pas présenté comme complet. Le vérificateur frais contrôle chaque référence d’acceptation et effet financier.
7. **Finaliser et vérifier.** À des frontières explicites sans opération active, le contrôleur calcule les empreintes logiques des bases, vérifie les points de contrôle complets, ferme ses processus et exporte des sauvegardes SQLite autonomes. Il compare leur contenu logique avant de sceller les preuves finales. La vérification fraîche examine ces fichiers réels et l’autorité conservée séparément.

Ces étapes traversent plusieurs bases. Elles **ne forment pas une transaction atomique distribuée**. Identifiants stables, états durables et rapprochement au redémarrage gèrent les points d’interruption éprouvés ; un état non résolu entre services reste un résultat incomplet.

## Temps, pannes et incertitude

Les instants logiques déterminent fenêtres, expiration des réservations, consentements et échéances. Une horloge monotone de l’hôte borne séparément l’exécution observée. Une décision acceptée sans observation après validation de transaction n’établit pas une acceptation dans les délais. Si l’accusé est perdu après cette observation, une nouvelle requête retrouve le résultat durable original sans accepter deux fois les unités.

Les pannes sont enregistrées par événement, opération déclenchante, occurrence et cible. Des points de transition nommés créent des interruptions déterministes autour des transactions et de l’export des fichiers. Les tests emploient arrêts de processus et barrières, sans temporisations arbitraires pour choisir l’issue d’une course. Une action annulée ou révoquée reste dans l’historique : la révocation bloque les actions futures concernées à partir de son instant effectif sans effacer une action observée antérieure.

Conservation de la capacité, conservation des fonds et unicité des unités acceptées ont des registres et contrôles distincts. Une réservation consomme la capacité jusqu’à sa libération ou expiration ; un travail engagé suit la sémantique de la base, et la capacité consommée ne peut être libérée. Un produit refusé peut donc consommer des ressources modélisées sans satisfaire une obligation client.

## Interprétation économique et comparaison

Chaque montant monétaire est un entier exact en unités mineures synthétiques : **100 unités mineures valent 1 `SMU` fictive**. Les rapports conservent ces entiers sans changement d’échelle. Coûts, soldes, valeurs, options externes et préférences sont des données définies pour l’expérience. Le registre simulé distingue retenues, transferts et coûts de production. Le vérificateur examine la faisabilité initiale de l’accord et les effets réalisés sur toute la campagne, accords annulés, corrections et fonds encore retenus compris.

Un contrôle technique explicitement autorisé et financé peut démontrer un contenu numérique accepté après le refus d’une transaction. Il ne démontre ni viabilité de cette transaction ni volonté réelle de payer. Un intervalle de valeur incertain produit une faisabilité modélisée possible ou certaine ; l’implémentation doit conserver cette incertitude.

Les adaptateurs conventionnel et du banc d’essai disposent du même domaine de voies, des mêmes outils, permissions et matériaux réutilisables utiles. Leurs recherches peuvent différer ; exécution et vérification sont communes. L’IA directe indisponible reste `NOT_RUN`. Le contrôle sans achat est distinct. Processeur, durée, requêtes, stockage, reprises et échecs mesurés ne remplacent pas les travaux non mesurés de préparation, d’intégration, d’adaptation ou de vérification humaine. Aucun avantage de coût complet ne découle de catégories encore inconnues.

## Preuves et inspection

L’enregistrement canonique distingue assertion du test, verdict du composant, stade de preuve et état de l’affirmation. Il présente production, réception, refus et quantité acceptée dans les délais par obligation ; décisions et conditions par accord ; comptes modélisés de campagne ; pannes ; versions ; empreintes ; ressources mesurées et catégories manquantes.

`PASSPORT.en.md` et `PASSPORT.fr.md` présentent le même enregistrement avec titres, explications, quantités et incertitudes traduits. Ils incluent tous deux l’enregistrement machine complet inchangé. Une réévaluation conserve les anciens passeports dans `passport-history/`. Un test contradictoire réussi peut révéler un vérificateur défectueux ; le rapporteur maintient cette qualification distincte.

Implémentation : [contrôleur](../../continuity_economy/controller.py), [producteur](../../continuity_economy/producer.py), [destinataire](../../continuity_economy/receiver.py), [participants](../../continuity_economy/participants.py), [vérificateur frais](../../continuity_economy/verifier.py), [rapporteur](../../continuity_economy/reporting.py). Les contrôles de produit et de processus figurent dans [les tests du produit](../../tests/test_economy_product.py) ; la parité des rapports dans [leurs tests](../../tests/test_economy_reporting.py).
