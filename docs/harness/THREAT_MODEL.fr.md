# CONTINUITÉ Ω — Modèle de menace et limites

[English](THREAT_MODEL.md) · **Français** · [Architecture](ARCHITECTURE.fr.md) · [Exigences](REQUIREMENTS.fr.md)

## Affirmation de sécurité visée

L’affirmation délimitée est qu’un processus candidat ne peut pas redéfinir le contrat conservé, lire les preuves d’acceptation cachées par son interface d’exécution autorisée, ni faire accepter des sorties locales modifiées comme exécution de la promesse originale. Le contrôleur et le vérificateur frais doivent également rendre visibles les preuves incomplètes ou contradictoires.

Cette affirmation concerne l’exercice logiciel local précisé. Elle ne protège pas contre un administrateur malveillant de l’hôte, un noyau compromis, un contrôleur hostile, une panne matérielle de stockage, des documents commerciaux réels frauduleux ou un fournisseur externe. Il faut consulter l’implémentation et ses tests avant de considérer une frontière prévue comme établie.

## Composants de confiance et composants non fiables

| Composant | Hypothèse de confiance | Conséquence d’un défaut |
| --- | --- | --- |
| Noyau de l’hôte et environnement Python | Appliquent l’isolement et exécutent les programmes conformément à leur définition. | Un hôte compromis peut modifier mémoire, code, preuves ou observations ; cette menace est hors périmètre. |
| Autorité de l’exercice | Conserve le contrat synthétique convenu et la référence originale indépendamment du candidat. | Une autorité absente ou incohérente empêche une conclusion favorable sur l’intégrité. |
| Contrôleur et relais | Imposent les opérations autorisées, horloges, limites et calendriers de panne ; consignent les transitions réelles. | Des observations fabriquées invalident l’exercice ; un contrôleur hostile exige une évaluation distincte. |
| Journal d’événements rédigé | Fournit les observations synthétiques déclarées jusqu’à la borne figée. | Une empreinte correspondante prouve l’identité avec ce jeu de données, pas l’authenticité ou la complétude de vraies instructions clients. |
| SQLite, système de fichiers et services locaux | Fournissent les propriétés transactionnelles et de persistance documentées lors des interruptions de processus testées. | L’arrêt forcé de processus n’établit pas la résistance de tous les stockages aux pannes matérielles ou électriques. |
| Horloge | Les mesures monotones de l’hôte sont fiables dans un exercice ; les unités logiques suivent le calendrier figé du contrôleur. | Des preuves temporelles absentes ou incohérentes laissent les affirmations d’échéance concernées non établies. |
| Vérificateur d’acceptation | Rejoue indépendamment les sources et examine les sorties durables actuelles. | Il exige ses propres contre-exemples et tests par mutation ; la réussite d’un candidat ne qualifie pas son vérificateur. |
| Candidat | Peut émettre des demandes mal formées, modifier ses entrées visibles, proposer un mauvais plan, recommencer ou s’arrêter. | Chaque action reste soumise à la validation du relais et du service ; ses déclarations ne sont pas des preuves d’acceptation. |
| Passeport enregistré | Présente une évaluation passée précise. | Il ne sert jamais d’oracle à une vérification fraîche. |

Tous les composants relèvent des auteurs du projet, sauf identification explicite d’un évaluateur externe. Des chemins de code distincts et des travaux d’IA séparés ne constituent pas une certification tierce.

## Isolement des candidats

L’implémentation de la version 0.1 utilise un filtre seccomp BPF Linux x86_64 installé dans le processus candidat après le chargement des modules nécessaires. Le lanceur fourni, le module candidat et les imports sont de confiance pendant cette phase initiale. Les modules Python tiers arbitraires et les imports non fiables ne sont pas pris en charge. Les données du candidat arrivent par une entrée standard bornée après activation du filtre.

Le candidat communique avec un relais restreint par les canaux hérités d’entrée et de sortie standard. Il n’a aucune opération de système de fichiers, même pour écrire directement dans son espace de travail. Tous les effets durables passent par les opérations autorisées du relais. Il ne dispose pas d’opérations arbitraires sur la base, les connexions réseau ou les processus.

La liste d’appels système autorisés interdit l’ouverture de fichiers, l’inspection de processus, l’exécution de nouveaux processus et la création de connexions réseau. Le lanceur ferme les descripteurs 3 à 65 535 et le contrôleur le démarre avec `close_fds=True` ; seuls les flux standards déclarés restent disponibles. Interdire une nouvelle ouverture ne suffirait pas à fermer un descripteur d’autorité déjà ouvert. Le relais refuse l’initialisation du service, les instantanés administratifs complets, l’enregistrement de l’autorité, les chemins arbitraires, l’injection de pannes et les valeurs d’horloge choisies par l’appelant.

Chaque lancement normal du candidat consigne des tests réels de refus portant sur le fichier d’autorité conservé, un fichier de l’espace candidat, la création de connexion réseau, la création de processus et l’inspection du parent par `process_vm_readv`. Le chemin de l’autorité est fourni au test ; l’accès est interdit, pas la connaissance du nom. Le contrôleur exige les cinq observations et le vérificateur frais en contrôle la présence. [`ExecutedControls.test_kernel_isolation_is_actually_probed_for_each_method`](../../tests/test_harness_controller.py) couvre les deux méthodes. [`test_harness_boundaries.py`](../../tests/test_harness_boundaries.py) éprouve les opérations interdites ou mal formées et les limites du processus candidat. Landlock a renvoyé `ENOSYS` dans l’environnement d’implémentation et n’est pas le mécanisme revendiqué. Ce filtre limité au processus ne crée aucun compte ni secret et ne modifie aucune permission système persistante.

La plateforme prise en charge et la capacité requise du noyau sont des conditions explicites d’exécution. Si le filtre ne peut pas être installé ou si la plateforme n’est pas prise en charge, l’exercice protégé doit refuser de poursuivre avec une affirmation favorable d’isolement. Les contrôles de schéma, les régressions historiques et les autres tests non affectés peuvent continuer. Aucun repli silencieux vers un candidat capable de lire l’oracle n’est admissible.

L’hôte, le contrôleur et les services conservent volontairement des accès plus larges. Cette frontière ne sécurise pas un programme local privilégié arbitraire et ne protège pas contre un administrateur. Les services partagés demeurent de confiance. Le confinement des accès et les limites de protocole/temps ne constituent pas une frontière complète contre le déni de service : la version 0.1 ne revendique pas des quotas indépendants de mémoire, de processeur ou de disque de l’hôte face à un candidat hostile.

## Les propriétés de l’autorité et des sources sont distinctes

| Propriété | Ce que le banc d’essai peut établir dans l’exercice | Ce qu’il n’établit pas |
| --- | --- | --- |
| Intégrité des octets | Le contenu actuel correspond à une empreinte conservée et à une forme canonique prise en charge. | La vérité du contenu. |
| Identité de la source | La source correspond au jeu synthétique enregistré. | L’identité ou la signature d’un vrai client. |
| Garde | Le candidat ne peut pas accéder à l’autorité protégée par l’interface éprouvée. | Une garde juridique indépendante ou une protection contre l’hôte de confiance. |
| Complétude | Le jeu synthétique déclare et contrôle sa borne d’observation et ses conditions de complétude. | L’absence de commandes réelles non divulguées, de modifications manuelles ou de réservations concurrentes inconnues. |

La suite conserve l’autorité à l’extérieur de chaque exécution candidate et fige séparément la référence. La vérification fraîche exige cette référence et son empreinte enregistrée. Calculer une nouvelle empreinte à partir de données contrôlées par le candidat établirait seulement une nouvelle relation de cohérence interne.

Le sceau d’exécution lie les fichiers durables actuels après l’arrêt des services et l’application du journal SQLite à la base. Son stockage est protégé des candidats par la frontière de processus éprouvée ; il ne constitue ni horodatage signé extérieurement ni stockage immuable pour l’administrateur de l’hôte. Les invocations distinctes utilisent des identités d’exécution distinctes, tout en conservant des graines de panne et conditions commerciales préenregistrées et comparables. Un test volontairement privilégié peut sceller de nouveau des preuves altérées pour éprouver la vérification sémantique ; ce cas ne donne pas ce droit à un candidat ordinaire.

Une référence faisant autorité absente, une couverture source requise manquante ou une vérification incomplète produit **NOT ESTABLISHED — NON ÉTABLI** pour l’affirmation concernée. Une incohérence positivement observée constitue un échec. Aucun de ces résultats ne prouve que toutes les voies possibles de continuité sont impossibles.

## Échecs qui doivent rester observables

- La réécriture des événements et de toutes les empreintes du candidat ne doit pas satisfaire le contrat original.
- Les types invalides, clés JSON dupliquées, champs inconnus, valeurs non finies, chemins dangereux et versions non prises en charge doivent être refusés avant modification d’état.
- Une modification manquante, une annulation révoquée à tort, un destinataire ou une spécification incorrects, un artefact dupliqué ou un reçu d’une autre exécution doivent faire échouer l’acceptation.
- Les réservations concurrentes ne doivent pas dépasser la capacité dans un chevauchement testé ; répéter une libération ou une expiration ne doit pas créer de capacité.
- Une action validée dont l’accusé de réception est perdu reste incertaine jusqu’au rapprochement. La nouvelle tentative ne doit pas créer un second achèvement.
- Un arrêt entre la création du reçu durable et l’export doit rester détectable et réparable par rapprochement.
- Une voie indisponible ou retirée et une dépendance défaillante partagée doivent affecter l’exécution ; un secours déclaré n’est pas nécessairement indépendant.
- Un dépassement d’échéance, un vérificateur arrêté, un délai dépassé, un contrôleur incomplet ou un artefact modifié ne doivent pas devenir une évaluation favorable de la promesse complète.

La [matrice des exigences](REQUIREMENTS.fr.md) identifie les preuves exécutables et leur état actuel pour ces cas. Une suite finie échantillonne des comportements ou épuise un modèle explicitement borné ; elle ne constitue pas une preuve générale de sûreté ni une garantie universelle d’exécution exactement une fois.

## Portée des conclusions commerciales et du transfert

Aucune commande par défaut ne contacte clients ou fournisseurs, ne réserve de capacité réelle, ne lit de commandes de production, ne dépense d’argent, ne télécharge de modèle ni ne modifie de permissions externes. Le nettoyage se limite aux processus jetables appartenant à l’exercice ; les preuves des exécutions précédentes restent disponibles.

Un achèvement logiciel local n’établit ni production physique, ni livraison, ni acceptation client, ni revenus, ni rentabilité, ni réseau viable de fournisseurs. Un exercice synthétique réservé à l’évaluation démontre seulement le transfert mesuré dans ces conditions. La comparaison peut aboutir à une égalité ou favoriser une méthode conventionnelle compétente. Les efforts humains et tarifs monétaires inconnus restent inconnus.

L’étape réelle suivante exige séparément l’autorité sur la commande, la garde des sources, la capacité du fournisseur, la divulgation permise, les conditions d’acceptation, les preuves opérationnelles et les obligations complètes décrites dans le [pilote proposé](../continuity-omega/REAL_PILOT.fr.md). Le banc d’essai ne confère pas cette autorité.
