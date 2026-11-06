# CONTINUITÉ Ω — Modèle de menace et limites de l’expérience économique

[English](THREAT_MODEL.md) · [Architecture](ARCHITECTURE.fr.md) · [Spécification du produit](PRODUCT.fr.md)

## Affirmation de sécurité éprouvée

Dans un exercice local jetable, un candidat ne doit pas transformer un engagement altéré, une solution non autorisée ou un résultat invalide en réussite vérifiée indépendamment en modifiant ses données, recalculant les empreintes, rejouant un état favorable ou répétant une action incertaine. La vérification doit conserver les lacunes de preuve et distinguer un échec d’exécution d’un test réussi qui détecte cet échec.

L’obligation protégée est le nouveau produit numérique défini par le contrat conservé. La portée exclut l’authentification d’un client réel, les étiquettes physiques, l’administration malveillante de l’hôte, les systèmes de paiement externes et une acceptation certifiée par un tiers.

## Actifs et confiance

| Actif ou composant | Confiance accordée | Ce qu’il n’établit pas |
| --- | --- | --- |
| Hôte, noyau et système de fichiers local | Confinement des appels système, horloges, durabilité SQLite/fichiers et arrêt des processus corrects | Protection contre root, noyau compromis, pannes matérielles ou toutes les coupures électriques |
| Contrôleur et importations initiales | Conservation honnête du contrat, garde des politiques, application des pannes, autorisations et finalisation | Sûreté avant l’initialisation de confiance, supervision organisationnelle indépendante |
| Autorité synthétique et journal | Les événements rédigés représentent les instructions conservées de l’exercice ; leur exhaustivité est explicite et contrôlée | Instructions authentiques d’un client ou capture complète des sources réelles |
| Horloge | Une horloge monotone de confiance pour les durées observées et les instants logiques consignés | Horodatage distribué de confiance ou mesure d’échéance d’un fournisseur réel |
| Services des participants | Le candidat ne peut modifier les politiques ; décisions et transferts sont conservés durablement | Consentement juridique, contrats, financement ou volonté de payer réels |
| Destinataire | Examen implémenté indépendamment, spécification conservée et importations littérales durables | Auteur indépendant, approbation d’un client externe ou essais physiques |
| Vérificateur frais | Contrôle distinct correct de l’autorité, du contenu, du temps et des registres | Démonstration mathématique générale ou absence certaine de défaut d’implémentation |
| Rapporteur | Présentation bilingue fidèle d’un enregistrement | Preuve nouvelle issue d’un passeport enregistré |

Tous les acteurs partagent l’hôte local et l’origine du développement. Des processus séparés créent des frontières de contrôle et d’état ; ils ne créent pas une certification par un tiers.

## Mécanisme réel d’isolation

Les répertoires d’autorité et d’exécution doivent être disjoints. L’autorité conserve contrat original, politiques, référence liée aux sources, paramètres de capacité et sceau final d’exécution. L’appelant conserve le SHA-256 original de la référence hors du contrôle du candidat. Fournir une empreinte nouvellement calculée depuis un paquet réécrit non fiable n’établit pas cet original.

Le fichier inchangé `continuity_harness/sandbox.py` de la base qualifiée installe une liste d’appels autorisés seccomp-BPF sous Linux x86-64 après les importations de confiance et la fermeture des descripteurs. Le candidat est limité à ses flux standard préexistants et aux appels de calcul permis. Ouverture par chemin, création réseau, lancement de processus et inspection d’autres processus sont interdits. Le filtre ne modifie aucun compte, identifiant, mode de fichier ni politique d’accès de l’hôte.

Avant toute opération du candidat, le contrôleur exige cinq refus observés : ouverture de l’autorité, ouverture de l’espace de travail, réseau, création de processus et inspection de processus. Une plateforme non prise en charge ou une sonde échouée ne peut produire une exécution qualifiée. Contrat et politiques visibles arrivent par le canal après l’isolation ; preuves d’acceptation conservées et sceaux de référence ne sont pas fournis.

Le courtier accepte un ensemble borné d’opérations validées et dérive lui-même les identités de production, capacité et livraison. Les points de panne internes et l’administration des politiques appartiennent au contrôleur, pas à des commandes arbitraires du candidat. Les deux méthodes implémentées subissent le même confinement et les mêmes permissions.

Ce mécanisme fait confiance au code initial et au noyau. Il ne protège pas l’importation de code Python arbitraire non révisé, ne constitue pas une frontière de conteneur contre l’administrateur et n’élimine pas tous les canaux auxiliaires. Les sondes observent des chemins et appels déterminés ; elles ne vérifient pas exhaustivement le noyau.

## Adversaires, pannes et défenses

| Épreuve | Réponse ou preuve requise |
| --- | --- |
| Réécriture cohérente de 1 900 unités en 1 850 avec nouvelles empreintes | Référence externe originale et obligations conservées restent applicables ; les octets modifiés ne peuvent les satisfaire |
| Autorité, empreinte originale ou preuve d’exhaustivité absente | `NOT_ESTABLISHED` au lieu d’une acceptation favorable |
| Métadonnées correctes et contenu substantiel erroné, absent ou corrompu | Destinataire et vérificateur analysent les octets réels et comparent chaque unité littérale |
| Révision périmée, mauvais destinataire, annulation ou modification perdue | Rejouer la source conservée et lier chaque unité acceptée à l’obligation figée |
| Clés JSON dupliquées, monnaie booléenne, quantité textuelle, champ inconnu, chemin dangereux ou version non prise en charge | Refus structuré avant les changements d’état concernés |
| Requêtes concurrentes, capacité chevauchante ou ressources retirées | Invariants transactionnels et rejeu indépendant du registre |
| Dépendance défaillante commune | Les deux voies restent indisponibles ; un second nom de fournisseur ne prouve pas l’indépendance |
| Accusé incertain, nouvelle requête ou arrêt de processus | Rapprocher identité stable et état durable ; ne jamais supposer l’échec de l’action |
| Export corrompu, transfert tronqué ou interruption | Conserver octets réels, fichiers partiels et historique ; ne pas inventer un produit complet |
| Refus suivi d’une correction | Prédécesseur A1 refusé du même accord et lot, capacité/coût A2 distincts, deux enregistrements conservés |
| Consentement révoqué, prix/responsabilité modifié ou financement retiré | Évaluer politiques effectives et fonds disponibles à l’action concernée ; conserver les décisions antérieures |
| Acceptation rejouée, preuves de plusieurs exécutions ou ancien passeport favorable | Revérifier les liens exécution/contrat/contenu/destinataire/temps depuis les preuves durables |
| Annulation après acceptation d’un sous-ensemble | Refus du courtier, accord actif/séquestre/responsabilités conservés et règlement partiel non résolu |
| Arrêt du vérificateur, instantané absent ou état non consolidé | Vérification incomplète ou `NOT_ESTABLISHED`, jamais réussite déduite |
| Mutation d’un vérificateur défectueux | Un test de détection réussi laisse échouer la qualification du vérificateur défectueux |

Achèvement par le producteur, réception et acceptation par le destinataire sont trois étapes distinctes. Un produit refusé peut notamment consommer capacité et coûts modélisés. Un refus correct peut préserver la sûreté tout en laissant l’engagement client incomplet.

## Consentement, responsabilités et temps

Les versions des politiques sont conservées. Le consentement reste actif tant que l’instant est strictement antérieur à `consent_until_tick` ; une révocation à l’instant `t` bloque l’action concernée à `t` et ensuite. Les conditions initialement acceptées restent enregistrées. Les changements de prix, financement et responsabilité ne peuvent être masqués par la réécriture d’une proposition ou d’un solde.

Les actions historiques ne sont jamais effacées rétroactivement. Le rejeu d’une action achevée retrouve son enregistrement existant. Une nouvelle production, un transfert ou une acceptation exige une autorisation selon les conditions effectives. Un contrôle technique financé délibérément reste distinct d’une transaction et exige sa propre permission.

Les échéances logiques du produit sont inclusives ; l’expiration des propositions et du consentement est exclusive. Une décision conservée sans observation après validation ne prouve pas une acceptation dans les délais. Les reprises après une observation durable à temps conservent cet instant ; celles créées après un arrêt emploient l’instant réel ultérieur. Le vérificateur contrôle aussi la limite d’observation déclarée.

Responsabilités modélisées et options externes sont des hypothèses explicites. Les montants sont des unités mineures synthétiques exactes, avec **100 unités mineures par `SMU` fictive** ; les rapports ne changent pas l’échelle des entiers conservés. Les fonds sont conservés entre comptes, retenues et transferts ; ils ne peuvent être comptés deux fois. Ce registre ne règle aucune obligation juridique et ne découvre aucune préférence réelle. Une marge synthétique positive n’établit jamais une demande volontaire réelle ni un avantage commercial.

Le protocole actuel de règlement exige l’acceptation du travail complet. Dès qu’une acceptation du destinataire est acquise, le courtier bloque l’annulation, même si la suite échoue ou si le respect des délais reste non résolu. L’accord demeure `ACTIVE` ; séquestre restant et responsabilités restent consignés. Aucun protocole de règlement partiel n’est implémenté. Le vérificateur doit exposer cet état non résolu, sans assimiler des fonds retenus à un paiement achevé, effacer le travail accepté ou libérer les responsabilités par annulation silencieuse.

## Vérification fraîche et garde des preuves

Le vérificateur frais lit les fichiers SQLite finaux et les résultats bruts réels, sans se fier aux mentions du producteur, résumés d’instantanés ou résultats enregistrés. Il contrôle séparément rejeu des sources, contenu littéral, capacité, décisions, conservation monétaire, références d’acceptation et observations. Schémas stricts et sérialisation sont une infrastructure neutre ; génération du producteur et décision du destinataire ne servent pas d’oracles.

Le contrôleur calcule les empreintes logiques complètes à des frontières inactives, vérifie les points de contrôle, ferme les auteurs d’écriture et sauvegarde l’état engagé en preuves autonomes. Le vérificateur refuse les fichiers auxiliaires SQLite incomplets et contrôle l’intégrité des bases en lecture seule. Les sceaux relient les fichiers à l’autorité conservée. Les modifications pendant vérification sont détectées aux endroits contrôlés ; une réécriture concurrente par un hôte hostile dépasse le modèle de confiance.

L’égalité des empreintes établit **l’intégrité des octets**, sans établir identité d’une source client, indépendance de garde ou exhaustivité. Ces propriétés sont des entrées et affirmations distinctes. Une référence d’autorité originale absente ne se répare pas en croyant le remplacement cohérent du candidat.

Exécutions échouées ou incomplètes, propositions annulées, produits refusés et corrections restent inspectables. Les réévaluations ajoutent ou conservent les rapports antérieurs sans réécrire l’histoire en réussite. Seuls les processus jetables du banc d’essai sont arrêtés ; les preuves générées ne font pas l’objet d’un nettoyage automatique.

## Limites des preuves et prochaine frontière

Les tests couvrent des données bornées déclarées, des transitions explicites, des courses déterministes et des mutations choisies. Une énumération finie ne s’applique qu’au domaine fini annoncé ; des arrêts échantillonnés ne démontrent ni tous les entrelacements, ni livraison universelle exactement une fois, ni planification illimitée, ni résistance à un hôte malveillant. La durabilité après arrêt de processus ne constitue pas une campagne complète de coupures électriques.

Les ressources locales mesurées excluent le travail d’ingénierie et d’adaptation non consigné ; la mesure processeur des enfants sur un hôte partagé peut inclure des exercices concurrents. Une capacité indisponible reste `NOT_RUN` ou non établie. Une trace d’IA simulée ou enregistrée ne mesure pas ses performances.

Avant une répétition réelle autorisée, il faut en plus : une nouvelle obligation numérique d’un client authentifié ; une acceptation et garde des preuves réellement distinctes ; les permissions et dépendances effectives des fournisseurs ; des fenêtres de capacité observées ; des accords et responsabilités de correction explicites ; des conditions financées ; des efforts d’intégration et d’adaptation mesurés. Toute affirmation physique exige aussi un protocole d’acceptation physique conservé et des essais physiques observés. Cette version ne fournit aucune de ces observations réelles.
