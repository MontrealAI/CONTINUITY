# CONTINUITÉ Ω — Résultats de l’expérience sur l’économie de la continuité

[English](RESULTS.md) · [Installation et commandes](README.fr.md) · [Expérience préenregistrée](EXPERIMENT.md) · [Amendements](AMENDMENTS.md) · [Exigences et tests](REQUIREMENTS.fr.md)

**Qualification ultérieure :** Ce rapport conserve les expériences initiales et leur chronologie source. Un défaut ultérieur de couverture agrégée, sa correction, de nouveaux contrôles positifs et un échec local non résolu de finalisation des preuves sont documentés dans [le dossier après revue](REVIEW_REPAIR.fr.md). Le successeur initial figé n’est pas requalifié en exécution inchangée du vérificateur corrigé ultérieurement. Les mentions de publication ci-dessous décrivent la remise initiale ; la [demande de fusion nº 3](https://github.com/MontrealAI/CONTINUITY/pull/3) consigne l’état d’intégration ultérieur.

**La première expérience préenregistrée a démontré la réalisation numérique acceptée par reprise du service principal, secours ordinaire et solution de remplacement admissible. Elle n’a pas établi d’avantage sur la méthode conventionnelle compétente.** Les deux méthodes actives ont obtenu les mêmes résultats et prix modélisés dans les sept comparaisons de base. Un contrôle technique financé séparément a réalisé le produit malgré le refus de l’achat. Les contrôles de capacité et de valeur incertaine ont correctement laissé des engagements non réalisés. Ces constats sont distincts et ne forment pas une note unique de réussite. [B]

La qualification complète ultérieure a reproduit ces résultats et réalisé un successeur réellement modifié de 1020 unités par les deux méthodes, avec l’implémentation figée inchangée. Les 26 assertions d’épreuves préenregistrées ont réussi. La concurrence de capacité contrainte laissait néanmoins 1400 unités manquantes sur 1900, et un cas de révocation réalisait le produit tout en échouant à couvrir la participation économique modélisée du fournisseur. Ces limites restent visibles dans le résultat qualifié. [Q]

Ce rapport porte sur une nouvelle **obligation de produit numérique**, bornée, de la version 0.2.0. Des processus locaux jetables ont produit, transféré, importé et examiné le contenu substantiel des lots d’étiquettes. L’expérience n’établit ni livraison physique ni acceptation authentique d’un client externe ; elle ne renforce pas rétroactivement les reçus historiques de métadonnées de la v0.1. Valeurs, prix, financements, responsabilités et choix extérieurs des participants sont des hypothèses synthétiques rédigées. Un consentement modélisé n’est ni un accord réel, ni une demande client, ni un paiement, ni une vente. [R]

## 1. Source qualifiée et chronologie

| Élément | Identité ou observation conservée |
| --- | --- |
| Base historique qualifiée | `396227d8da2f55f674f479de16089c7ce28ef290`, publication `continuity-harness-v0.1.0` |
| Source de la première expérience de base préenregistrée | `080a5484d1ff26fe04aac32078d9ea9ef2f739f4` |
| Arbre source | `3cd539623fff2564d76e13f5201edc5e8d53dbf1` |
| Régression avant cette expérience | 424 tests réussis ; 0 échec ; 0 omission ; 73,909 secondes |
| Première suite de base | `economy-qualification/base-attempt-1` : 21 enregistrements de méthodes exécutées et 7 enregistrements IA `NOT_RUN` |
| Nouvelle vérification indépendante de la base | Les 28 enregistrements rapprochés ; aucune anomalie critique de sûreté ni assertion préenregistrée échouée |
| Gel de réutilisation, après la base et avant rédaction du successeur | Commit publié `d172b6491ff0f065fb3804811dd55cc8b5961830` ; 42 fichiers d’implémentation, d’interfaces et de documentation répertoriés |
| Source de l’expérience complète et du premier successeur | `3494becbbfaf15ae571a71df05a49b9ce982cc84` ; arbre `8c8ce255a04202361b8322869c1b1e49302428fc` |
| Expérience complète | `economy-qualification/complete-attempt-1` : reproduction de la base, premier successeur et 26 épreuves préenregistrées ; assertions et vérification fraîche distincte réussies |
| Contrôle du gel après exécution complète et vérification fraîche | Les 42 empreintes conservées sont inchangées ; source qualifiée sans modification locale |
| Qualification ultérieure de disponibilité des tests | `dd00519e965b70ca47bf1cb3ac69bd3022ebfdc9` ; 33 tests du produit, 20 répétitions par paire / 40 exécutions et trois workflows CI réussis ; exécution et documentation figées inchangées |

L’environnement de base utilisait Python 3.12.14, SQLite 3.53.1 et Linux 6.18.57 sur x86_64 avec glibc 2.39. Le candidat a réussi les cinq essais de refus seccomp : accès aux fichiers d’autorité, accès aux fichiers de travail, réseau, création de processus et inspection des processus. Environnement, commandes, empreintes sources, état des modifications et références propres à chaque exercice sont conservés avec les preuves. [B, F]

L’analyse de la première base conserve son historique. La révision 2 lit les événements réels `CANDIDATE_PLANNING` ; la première analyse recherchait un nom d’événement inexistant et omettait donc la télémétrie de planification. L’analyse antérieure reste conservée. Il s’agit d’une correction d’analyse, sans nouvelle exécution ni modification des quantités acceptées, prix, ressources d’exécution mesurées ou conclusions. [A]

## 2. Nature exacte du produit et de l’engagement

Chaque engagement actif exigeait un contenu `continuity-economy/label-job/v1` pour chaque ordinal : numéro unique, référence du produit, noms anglais et français, consignes anglaises et françaises et identifiant de lot. Le destinataire conservait les octets réels, importait les unités dans sa propre base SQLite, les examinait selon son contrat conservé et enregistrait séparément réception, décision et observation durable. Un manifeste, une quantité, une empreinte ou une déclaration du producteur ne suffisait pas à établir l’acceptation. [R, B]

L’engagement de base était le suivant :

| Engagement | Destinataire | Révision | Unités requises | Échéance | Traitement observé |
| --- | --- | ---: | ---: | ---: | --- |
| `DL-100` | `RECIPIENT-A` | 2 | 1100 | Pas 500 | Spécification finale modifiée exigée |
| `DL-200` | `RECIPIENT-B` | 1 | 800 | Pas 500 | Contenu numérique spécifié intégral exigé |
| `DL-300` | `RECIPIENT-C` | 1 | 0 | Pas 500 | Annulé ; ses 100 unités historiques n’ont pas été réactivées |

Le contrat initial autorisait des lots fixes de 500 unités et leurs reliquats finaux. Aucun échec n’a ajouté le droit de répartir le travail ni modifié destinataires, quantités ou spécifications. La limite d’observation était le pas 800 et la durée maximale 60000 ms. Les pas logiques représentent des opérations modélisées, pas des secondes ; la mesure réelle monotone est distincte. [R]

Les contrôles pris en charge établissent le contenu sémantique JSON. Rendu, typographie, comportement des codes-barres, qualité d’impression, performance matérielle et biens physiques restent hors périmètre. Les champs non pris en charge et les produits trop volumineux sont refusés à l’admission. [P]

## 3. Résultats de la première base, engagement par engagement

Le tableau s’applique séparément aux procédures **conventionnelle et du banc d’essai**. Toutes les assertions de base exécutées ont réussi, y compris les cas négatifs et incertains attendus. « Démontré », « Échec » et « Non établi » correspondent aux statuts indépendants `DEMONSTRATED`, `FAILED` et `NOT_ESTABLISHED` ; ils ne sont pas des synonymes du code de sortie d’un processus. [B]

| Cas de base | `DL-100` accepté / requis | `DL-200` accepté / requis | Résultat numérique | Faisabilité du service modélisé | Résultat observé |
| --- | ---: | ---: | --- | --- | --- |
| `primary-recovery` | 1100 / 1100 | 800 / 800 | Démontré | Démontrée | L’historique protégé a restauré le service principal périmé ; produit complet accepté et transaction réglée |
| `conventional-better` | 1100 / 1100 | 800 / 800 | Démontré | Démontrée | Les deux méthodes ont retenu la meilleure solution de secours existante |
| `constructed-continuity` | 1100 / 1100 | 800 / 800 | Démontré | Démontrée | Le secours a échoué avant réservation ; une répartition autorisée a réalisé le même engagement après annulation et redémarrage |
| `repair-after-rejection` | 1100 / 1100 | 800 / 800 | Démontré | Démontrée | Une remise de 500 unités a été rejetée ; une correction distincte et financée a été acceptée |
| `technical-no-trade` | 1100 / 1100 | 800 / 800 | Démontré | Échec | L’acheteur a refusé l’achat ; un commanditaire de recherche explicitement autorisé a financé la réalisation technique |
| `no-deal` | 0 / 1100 | 0 / 800 | Échec | Échec | Seulement 800 unités de capacité de remplacement admissible pour l’engagement de 1900 unités |
| `uncertain-value` | 0 / 1100 | 0 / 800 | Échec | Non établie | L’intervalle de valeur de l’acheteur n’établissait pas son consentement ; aucun accord financé ni production n’a suivi |

`DL-300` est resté annulé, sans unité produite ou acceptée, dans tous les cas. Le vérificateur indépendant n’a signalé, dans aucun enregistrement de base exécuté, d’acceptation en double, de travail accepté tardivement ni d’engagement dangereux ou non autorisé. [B]

### La reprise, les défaillances et les corrections ont réellement été exécutées localement

Le service principal a été reconstitué depuis le journal conservé, avec modification, enregistrements manquants et annulation. Les appels de restauration ont duré 2,697325 ms pour la procédure conventionnelle et 2,228788 ms pour celle du banc. Il s’agit d’une mesure locale par méthode, pas d’une garantie de reprise pour un autre système. [B]

Dans `constructed-continuity`, l’accord de secours initialement accepté a été annulé avant toute acceptation de travail. Ses 200 unités mineures de coordination sont restées engagées. Un nouvel accord a confié les 1100 unités de `DL-100` à `COMPAT-A` et les 800 unités de `DL-200` à `COMPAT-B`. Le destinataire a été arrêté après acceptation durable mais avant accusé de réception ; le candidat a également été arrêté puis redémarré. Il a rapproché l’acceptation existante au lieu de produire du travail en double. Chaque méthode a enregistré un redémarrage de service et un redémarrage du candidat. [B]

Dans `repair-after-rejection`, le producteur a été arrêté pendant une exportation partielle. La reprise du même identifiant a réutilisé le contenu déjà généré durablement ; elle n’a pas été comptée comme une fabrication supplémentaire. Le destinataire a ensuite rejeté le lot de 500 unités, dont le contenu échouait à l’examen. A2 référençait l’A1 rejeté exact, consommait une capacité supplémentaire et engageait un coût de correction distinct. Pour `DL-100`, les tentatives totalisaient 1600 unités produites, 500 rejetées et 1100 acceptées ; `DL-200` comptait 800 unités produites et acceptées. Au total, 2400 unités ont été produites et 1900 acceptées. Le lot rejeté reste conservé. [B]

Le comparateur sans achat a exécuté sept contrôles locaux réels, sans produit, engagement accepté ou transfert modélisé. Son résultat numérique était `FAILED` ; la faisabilité d’une transaction était `NOT_ESTABLISHED`, car aucune transaction n’était proposée. Les sept enregistrements IA étaient `NOT_RUN` : aucune capacité IA locale appropriée et déjà autorisée n’était disponible. Le temps et le stockage nécessaires à ces enregistrements relèvent de l’infrastructure comptable, pas d’une inférence ou d’une performance IA. [B]

## 4. Prix, coûts engagés et participation modélisés

**Chaque montant de cette section est un entier exact en unités mineures SMU.** Cent unités mineures valent une SMU fictive. Aucun taux de change, salaire, prix de marché, consentement à payer ou économie réelle n’a été observé. Les deux méthodes actives ont obtenu les mêmes chiffres. Les coûts des fournisseurs et du coordonnateur sont des dépenses rédigées dans le modèle et transférées vers un compte de coûts explicite ; ils sont distincts des ressources informatiques observées. [R, B]

| Cas | Prix proposé à l’acheteur | Paiement effectif de l’acheteur | Coût modélisé total engagé | Dont correction | Situation financière |
| --- | ---: | ---: | ---: | ---: | --- |
| Reprise principale | 4400 | 4400 | 2200 | 0 | Réglé |
| Secours existant | 4500 | 4500 | 2250 | 0 | Réglé |
| Continuité reconstruite | 4500 initialement ; 5500 en remplacement | 5500 | 2800 | 0 | Premier accord annulé ; second réglé ; coût de l’échec conservé |
| Rejet et correction | 4500 | 4500 | 2900 | 650 | Réglé ; correction facturée une fois |
| Réalisation technique sans transaction | 8300, refusé | 0 | 4150 | 0 | Contrôle de recherche financé par le commanditaire ; aucun paiement commercial acheteur/fournisseur |
| Absence d’accord | Aucune proposition | 0 | 0 | 0 | Aucun accord |
| Valeur incertaine | 8300, non résolu | 0 | 0 | 0 | Aucun accord ni fonds bloqués |

Le prix principal de 4400 rémunérait le fournisseur à hauteur de 4100 et le coordonnateur de 300. Leurs bénéfices modélisés réalisés étaient respectivement 2100 et 100. Le secours ordinaire à 4500 versait 4200 au fournisseur et 300 au coordonnateur ; sans correction, leurs bénéfices étaient 2150 et 100. Le cas de réparation conservait le même prix mais engageait 650 de correction, laissant 1500 au fournisseur et 100 au coordonnateur. Ces chiffres positifs découlent de conditions synthétiques à prix fixe incluant une provision de correction ; ils ne prouvent pas une rentabilité commerciale. [B]

Le cas reconstruit versait 2700 à `COMPAT-A` pour 1300 de coûts et 2300 à `COMPAT-B` pour 1100 de coûts. Le coordonnateur recevait 500 pour **400** de coûts totaux sur les deux accords, couvrant son seuil de participation de 100. Omettre le premier accord améliorerait artificiellement le résultat. Les fonds bloqués de l’acheteur et les provisions de correction inutilisées ont été libérés ou réglés selon les écritures ; aucun fonds ne restait bloqué à la fin de ces cas de base achevés. [B]

### Régions de faisabilité et limites

Pour un prix `P`, une valeur acheteur `V` et une utilité extérieure `U`, la condition modélisée inclut `V ≥ P + U`, la limite de prix et le financement disponible. Un intervalle `[L,H]` n’établit l’acceptabilité certaine que si sa borne inférieure satisfait cette condition. Le paiement du fournisseur doit couvrir travail initial, provision financière complète de correction permise et maximum du bénéfice requis ou accessible ailleurs ; fonds de travail et limite d’exposition à l’échec doivent également suffire. Une provision financière ne garantit pas la disponibilité ultérieure de capacité de production. [R]

Pour la campagne reconstruite, le seuil acheteur pertinent est **7500 = 5500 + 2000** unités mineures. Le plancher intrinsèque de devis de 7300 omet les 200 de coordination antérieurs ; ce n’est pas le seuil de la campagne. Dans `uncertain-value`, le prix de 8300 et l’utilité extérieure de 2000 exigent une valeur d’au moins 10300. L’intervalle synthétique `[2000, 30000]` traverse cette limite : le consentement reste `NOT_ESTABLISHED`. Aucune valeur favorable n’a été choisie arbitrairement dans cet intervalle. [B]

Le contrôle technique rend cette distinction décisive : valeur, limite de prix et fonds de l’acheteur étaient chacun de 100, avec une utilité extérieure de 2000. La transaction de 8300 a été refusée. Un commanditaire a engagé séparément 4150, et le destinataire a tout de même accepté le produit numérique. **Une réussite technique n’a pas créé une transaction acceptable.** [B]

## 5. Ce que la comparaison établit

La procédure conventionnelle énumérait le domaine complet borné des affectations admissibles ; celle du banc utilisait une recherche avec élagage dans le même domaine, avec les mêmes équations tarifaires. Toutes deux recevaient le même contrat public, financement courant, politiques, possibilités de capacité, observations, actions autorisées, transactions, mécanismes d’idempotence et éléments réutilisables. Toutes deux pouvaient restaurer le service principal, employer le secours ou construire une solution admissible. La référence d’acceptation conservée était cachée aux deux. [R, F]

Les sept comparaisons fonctionnelles sont à égalité. Le nom `conventional-better` décrit une meilleure **voie de secours conventionnelle**, retenue par les deux méthodes. Ce n’est pas une victoire algorithmique contre le banc. Plus largement, l’expérience compare deux procédures disposant de la même infrastructure de reprise, d’exécution et de vérification ; elle n’isole pas la valeur du produit complet face à une organisation qui en serait dépourvue. Aucune comparaison IA réelle n’a eu lieu. [B]

### Ressources d’exécution et de vérification mesurées

Ces totaux additionnent une observation par cellule de base. Le calcul comprend le contrôleur et ses processus enfants. Le stockage est la taille enregistrée du répertoire de l’exercice à la limite déclarée. Les chiffres de vérification ci-dessous proviennent des évaluations initiales `RESULT.json` ; les audits supplémentaires constituent un travail distinct. [A, B]

| Mesure, total des sept cas | Conventionnelle | Banc d’essai | Sans achat |
| --- | ---: | ---: | ---: |
| Engagements acceptés | 10 | 10 | 0 |
| Unités acceptées | 9500 | 9500 | 0 |
| Unités produites | 10000 | 10000 | 0 |
| Unités des remises rejetées | 500 | 500 | 0 |
| Durée d’exécution, secondes | 6,551096307 | 6,547990511 | 3,573861314 |
| Calcul d’exécution, secondes CPU | 5,648582992 | 5,559624989 | 3,074385984 |
| Durée de vérification initiale, secondes | 1,124176314 | 1,122230587 | 0,242987897 |
| Calcul de vérification initiale, secondes CPU | 1,123835481 | 1,122049222 | 0,242846647 |
| Octets enregistrés de l’exercice | 48141686 | 48140834 | 8514025 |
| Requêtes du candidat au courtier | 163 | 163 | 0 |
| Requêtes aux services | 878 | 878 | 126 |
| Reprises de production avec le même identifiant | 1 | 1 | 0 |
| Redémarrages de service / candidat | 2 / 1 | 2 / 1 | 0 / 0 |
| Interventions humaines à l’exécution | 0 | 0 | 0 |

Le démarrage des services et la conservation des preuves représentent un coût réel pour le comparateur sans achat, malgré l’absence de production. Son volume inférieur de résultats et de stockage s’accompagne de zéro engagement réalisé ; ce n’est pas un gain d’efficacité de continuité. Les faibles écarts de stockage entre méthodes actives comprennent les identifiants et tailles des enregistrements ; ils n’établissent pas un avantage de stockage. [B]

La dernière acceptation durable réelle survenait aux durées suivantes depuis le démarrage du contrôleur. Elle est distincte de la finalisation ultérieure des preuves et du règlement financier. [B]

| Cas de base achevé | Conventionnelle, secondes | Banc d’essai, secondes |
| --- | ---: | ---: |
| Reprise principale | 0,920383111 | 0,850515362 |
| Secours existant | 0,834026608 | 0,904178730 |
| Continuité reconstruite | 0,889768313 | 0,983170564 |
| Rejet et correction | 0,869306102 | 0,879915057 |
| Contrôle technique | 0,831958447 | 0,755410240 |

La télémétrie déclarée par les candidats comptait 2303 affectations complètes pour l’énumération conventionnelle, contre 124 affectations complètes et 712 nœuds partiels pour le banc. Le temps de planification déclaré totalisait respectivement 74,262624 ms et 23,228911 ms. Ces chiffres décrivent les implémentations figées dans le domaine fini déclaré. Ce ne sont ni des mesures CPU indépendantes ni la preuve d’un avantage général de découverte ; la couverture par élagage ne signifie pas que chaque affectation a été visitée. [A]

Il n’y avait qu’une observation par cas et méthode, dans un ordre fixe, sans randomisation ni répétitions. Démarrage, stockage et vérification représentent une grande part de l’exécution. L’écart total de durée était d’environ trois millisecondes sur sept exercices ; la procédure conventionnelle était plus rapide dans certaines cellules. **Un avantage fiable de vitesse ou de coût complet reste `NOT_ESTABLISHED`.** [A, B]

Le travail de préparation, d’intégration, de rédaction des cas, d’adaptation et de vérification n’a pas été mesuré. La mémoire maximale des processus et les taux de conversion monétaire réels restent inconnus. La limite de mesure du contrôleur exclut son dernier enregistrement, le sceau d’exécution et la publication ultérieure des résultats et Passeports ; le stockage partage cette limite explicite. Zéro intervention humaine enregistrée à l’exécution ne signifie pas zéro travail de développement. Aucun prix ou durée inventé ne comble ces lacunes. [A, F]

## 6. Défis, défauts et engagements non résolus

L’historique de développement conserve les preuves défavorables et les défauts corrigés : acceptation d’A2 sans A1 rejeté, admission directe trop permissive, blocage trop large de l’A1 d’un nouvel accord, omission des fonds et responsabilités visibles dans la planification, admission de produits trop volumineux avant leur génération et annulation après acceptation acquise du destinataire. Chacun possède un enregistrement antérieur distinct ; la réussite d’un test adversarial exposant un défaut ne qualifiait pas le composant défectueux. Les corrections et chemins exacts figurent dans [AMENDMENTS.md](AMENDMENTS.md). [D]

La qualification complète a exécuté **26 épreuves préenregistrées : 11 exercices réels, 12 altérations délibérées de preuves et 3 mutations ciblées du vérificateur**. Toutes les assertions préenregistrées ont réussi ; aucun vérificateur défectueux n’a été qualifié. Les preuves volontairement falsifiées et les vérificateurs défectueux conservent correctement des affirmations échouées ou non établies même si le test extérieur réussit. Ces observations ne représentent pas 26 engagements clients réalisés. [Q]

### Résultats et coûts des épreuves exécutées

Le tableau indique les quantités acceptées contre l’engagement original conservé de 1100/800 unités. Tous les montants sont en unités mineures SMU synthétiques. Pour la réécriture cohérente, paiement et coût décrivent l’exécution du paquet altéré ; ils n’établissent pas une transaction autorisée contre le contrat original. [Q]

| Épreuve exécutée | `DL-100` / `DL-200` acceptées | Résultat numérique | Faisabilité du service modélisé | Paiement acheteur / coût engagé |
| --- | ---: | --- | --- | ---: |
| Contrôle numérique valide | 1100 / 800 | Démontré | Démontrée | 4400 / 2200 |
| Réécriture cohérente à 1850 unités | 0 / 0 | Échec | Échec | 4300 / 2150 |
| Consentement retiré avant production | 1100 / 800 | Démontré | Démontrée | 8500 / 4350 |
| Autorisation retirée avant transfert | 1100 / 800 | Démontré | Échec | 13100 / 7250 |
| Fonds retirés après proposition | 0 / 0 | Échec | Échec | 0 / 0 |
| Prix modifié après proposition | 1100 / 800 | Démontré | Démontrée | 8300 / 4150 |
| Dépendance défaillante commune | 1100 / 800 | Démontré | Démontrée | 12900 / 6400 |
| Expiration de l’échéance | 0 / 0 | Échec | Échec | 0 / 800 |
| Compétition pour la capacité restante | 500 / 0 | Échec | Échec | 0 / 850 |
| Exhaustivité source absente | 0 / 0 | Non établi | Non établie | 0 / 1600 |
| Passeport favorable périmé | 0 / 0 | Échec | Non établie | 0 / 0 |

La concurrence de capacité est conséquente : deux lots autorisés se sont disputé les 500 dernières unités à travers des barrières transactionnelles déterministes. `DL-100` comptait **500 unités acceptées et 600 manquantes**, et `DL-200` **0 acceptée et 800 manquantes**. L’accord restait `ACTIVE` ; 4500 de fonds de l’acheteur et 3450 de provisions restantes du fournisseur demeuraient bloqués. Le fournisseur avait engagé 650 de production et le coordonnateur 200, sans paiement de règlement. La sûreté était démontrée dans ce contrôle, tandis que réalisation complète et faisabilité réalisée échouaient. **Le règlement partiel consenti n’est pas implémenté et reste non résolu.** La tentative défectueuse antérieure conservée annulait une acceptation acquise ; le comportement corrigé refuse cette annulation. [Q, D]

Le retrait d’autorisation avant transfert révèle une autre limite économique. Le premier fournisseur de secours avait produit 500 unités, engageant 650, auxquels s’ajoutaient 200 de coordination. La divulgation a été révoquée avant transfert ; ces unités n’ont pas été livrées. Un nouvel accord accepté a produit les 1900 unités requises, portant la production à 2400 et le coût de campagne à 7250. Bien que le produit du client ait été accepté et que le coordonnateur ait couvert son coût combiné, le fournisseur abandonné n’a reçu aucune compensation avec les frais d’annulation nuls définis dans le modèle. Sa participation réalisée a échoué. Achever le produit n’a donc pas établi une solution viable pour tous les participants. [Q]

L’expiration de l’échéance a conservé 500 unités produites, aucun travail accepté et 800 de coûts engagés. L’exhaustivité source absente a conservé huit tentatives annulées et 1600 de coordination, sans produit ni résultat établi. Ce dernier cas révèle des planifications répétées inutiles face au même obstacle de preuve ; ces tentatives sont comptées, sans être dissimulées. Cette limite bornée reste non résolue. Le retrait de financement a conduit à une absence d’accord honnête. Les changements de prix et de consentement ont exigé de nouvelles décisions ; ils n’ont pas modifié silencieusement l’engagement déjà accepté. [Q]

### Altérations de preuves et mutations de vérificateur

Les 12 altérations couvraient contenu erroné, contenu dupliqué, troncature, révision périmée, mauvais destinataire, unités importées absentes, observation durable tardive, observation d’acceptation absente, empreinte de référence absente, base du destinataire provenant d’un autre exercice, références de règlement inventées et paiement équilibré mais erroné. Le vérificateur indépendant refusait le contenu substantiel altéré même après recalcul des sceaux. Une preuve d’autorité ou d’observation d’acceptation absente restait `NOT_ESTABLISHED`. Un ancien Passeport favorable ne prouvait aucun résultat. Le paquet distinct de 1850 unités déclarait son achèvement, mais échouait contre la référence indépendante conservée de 1900 unités avec `REFERENCE_PIN_MISMATCH`. [Q]

Trois observations de mutation rendent explicite la distinction des évaluations :

| Vérificateur volontairement défectueux | Test extérieur | Verdict du composant | Stade de preuve | Qualification du vérificateur / résultat numérique réel |
| --- | --- | --- | --- | --- |
| Ignore le contenu sémantique | Réussi | Démontré | Mutation ciblée du vérificateur | Échec / Échec |
| Ignore l’échéance après validation durable | Réussi | Démontré | Mutation ciblée du vérificateur | Échec / Échec |
| Rejette le contenu valide | Réussi | Échec | Mutation ciblée du vérificateur | Échec / Démontré |

Les 11 contrôleurs d’épreuves réelles ont consommé 9,541403860 secondes d’exécution, 8,234553978 secondes CPU, 296 requêtes au courtier et 1364 aux services ; leur vérification initiale a pris 1,580017039 seconde. Le stockage enregistré des exercices réels était de 63921902 octets. Les 12 altérations et les 3 observations de mutation ont enregistré respectivement 3,168169042 et 1,336721247 secondes d’observation des épreuves, comprenant leur inspection. Leurs champs de ressources hérités de l’exercice source décrivent la provenance, pas une production supplémentaire, et ne sont pas recomptés comme 15 nouvelles exécutions. Les limites de mesure de la section 5 s’appliquent. [Q]

Les tests finis aux points de transition et la recherche bornée ne prouvent pas la correction pour tous les ordonnanceurs, pannes matérielles ou systèmes d’exploitation. Le modèle de menace fait confiance à l’hôte, au noyau, au contrôleur, à l’horloge et à l’autorité synthétique conservée. Identité, garde, exhaustivité et intégrité des octets restent distinctes. Une empreinte n’authentifie pas une instruction de client réel. Des processus séparés et une rédaction commune ne constituent pas une certification tierce. [T]

## 7. Successeur et qualification définitive

L’expérience complète s’est exécutée depuis la source sans modification locale `3494becbbfaf15ae571a71df05a49b9ce982cc84`, après ajout des entrées préenregistrées séparément pour le successeur. Les 42 empreintes réutilisables d’implémentation, interfaces et documentation sont restées identiques au gel `080a5484d1ff26fe04aac32078d9ea9ef2f739f4`, avant et après exécution. La suite complète et une vérification fraîche distincte ont toutes deux réussi leurs assertions. Cette tentative complète contient 21 enregistrements de base exécutés, 3 du successeur exécutés, 8 enregistrements IA indisponible et les 26 épreuves décrites ci-dessus. [Q, F]

La tentative complète a reproduit la base avant d’exécuter le premier successeur. Les sept comparaisons conventionnelle/banc sont encore à égalité, avec les mêmes quantités, prix et statuts d’affirmation. Cette reproduction est conservée séparément des premières observations des sections 3 à 5. Ses durées d’exécution conventionnelle, du banc et sans achat totalisaient respectivement 6,769026085, 6,920246962 et 3,766151806 secondes ; les vérifications initiales totalisaient 1,254313465, 1,196926019 et 0,255785635 secondes. Ces valeurs ne sont pas fusionnées avec la première base en échantillon statistique préenregistré. [Q]

### Un engagement numérique réellement modifié

Le successeur, `archive-window-transfer`, exigeait de nouveaux contenus bilingues d’index d’archives dans le même format numérique pris en charge. Il modifiait destinataires, révisions finales, quantités, huit lots fixes de 150 unités ou reliquats finaux, échéances individuelles, fenêtres de capacité, dépendances, financements et prix. Principal et secours conventionnel partageaient une dépendance défaillante. Les solutions admissibles disposaient de capacité précoce jusqu’au pas 140 et ultérieure à partir du pas 260. L’échéance globale était 560, la limite d’observation 650 et la durée maximale 90000 ms. Aucun produit du successeur déjà achevé ni témoin arithmétique de revue n’était fourni aux candidats. [S]

| Engagement du successeur | Destinataire | Révision | Requis / accepté, chaque méthode active | Échéance individuelle | Dernier pas d’acceptation observé |
| --- | --- | ---: | ---: | ---: | ---: |
| `ARC-410` | `RECIPIENT-NORD` | 3 | 420 / 420 | 130 | 19 |
| `ARC-520` | `RECIPIENT-EST` | 2 | 330 / 330 | 440 | 268 |
| `ARC-630` | `RECIPIENT-SUD` | 1 | 270 / 270 | 520 | 278 |
| `ARC-740` | `RECIPIENT-OUEST` | 1 | 0 / 0 | 360 | Annulé ; aucune acceptation |

Les deux méthodes ont sélectionné indépendamment `ARCHIVE-COMPAT-A` pour 900 unités — 570 précoces et 330 ultérieures — et `ARCHIVE-COMPAT-B` pour 120 unités ultérieures. Le contrôleur a avancé explicitement l’horloge modélisée à la fenêtre ultérieure ; aucune pause arbitraire n’établissait la correction. Le deuxième accusé d’acceptation a été perdu après observation durable du destinataire. Chaque méthode a redémarré le service de réception et rapproché la même remise : huit produits, huit lots acceptés, une reprise enregistrée, un redémarrage de service, zéro acceptation en double et zéro coût de correction. Les 90 unités historiques d’`ARC-740` sont restées annulées. [Q]

Les deux méthodes actives ont démontré résultat numérique et faisabilité modélisée, avec avantage de méthode `NOT_ESTABLISHED`. L’exercice sans achat n’a accepté aucun des trois engagements ; le résultat échouait et la faisabilité de transaction restait non établie. L’enregistrement IA restait `NOT_RUN`. [Q]

### Économie du successeur et effort mesuré

Chaque méthode active a payé 5700 unités mineures synthétiques : 4220 au fournisseur A, 1190 au fournisseur B et 290 au coordonnateur. Les coûts engagés étaient 2040, 570 et 180, soit 2790 au total. Les bénéfices modélisés réalisés étaient 2180, 620 et 110, couvrant les seuils de participation rédigés de 260, 200 et 110. La provision complète de correction de 2340 n’a pas été dépensée ; ses fonds bloqués ont été libérés et tous les soldes bloqués réglés ont fini à zéro. Le registre simulé conservait ses 26100 unités mineures initiales, compte de coûts compris. Ce sont des observations financières synthétiques, pas une validation commerciale. [Q]

L’intervalle de valeur de l’acheteur était `[8200, 9600]`, son utilité extérieure 1800 et son prix maximal 7000. Au prix de 5700, l’utilité conservée était `[2500, 3900]`, entièrement supérieure à l’option extérieure. La valeur d’équilibre acheteur était 7500 ; le plafond de prix acceptable avec certitude était 6400 et le plafond possible 7000. Aucune valeur favorable n’a été choisie dans l’intervalle. [S, Q]

| Ressource du successeur, une observation | Conventionnelle | Banc d’essai | Sans achat |
| --- | ---: | ---: | ---: |
| Engagements / unités acceptés | 3 / 1020 | 3 / 1020 | 0 / 0 |
| Durée d’exécution, secondes | 1,123797768 | 1,302063181 | 0,575467300 |
| Calcul d’exécution, secondes CPU | 0,933073997 | 1,041059999 | 0,488968998 |
| Durée de vérification initiale, secondes | 0,185452904 | 0,194249523 | 0,053022534 |
| Calcul de vérification initiale, secondes CPU | 0,185318916 | 0,193997262 | 0,050383782 |
| Dernière acceptation durable, secondes écoulées | 0,927510226 | 1,090146026 | Aucune acceptation |
| Octets enregistrés de l’exercice | 6506796 | 6498354 | 1392094 |
| Requêtes courtier / services | 45 / 239 | 45 / 239 | 0 / 21 |
| Reprises enregistrées / redémarrages de service | 1 / 1 | 1 / 1 | 0 / 0 |

La télémétrie du candidat conventionnel déclarait 6561 affectations complètes énumérées en 12,721471 ms. Celle du banc déclarait 48 affectations complètes et 125 nœuds partiels en 4,442647 ms ; les deux trouvaient 27 affectations faisables. Malgré une durée de recherche déclarée inférieure, la procédure conventionnelle a réalisé l’exécution complète mesurée la plus courte dans cette seule observation du successeur. L’ordre fixe et le travail non mesuré empêchent une conclusion fiable de vitesse ou d’effort complet. [Q]

**Le transfert sans modification d’implémentation est démontré pour ce successeur spécifié, par les deux méthodes compétentes. Une réduction du travail d’adaptation, un avantage général de découverte, une capacité de déploiement commercial à grande échelle et l’autonomie générale restent `NOT_ESTABLISHED`.** Le travail de rédaction du nouveau cas et d’adaptation n’a pas été chronométré ; zéro fichier figé modifié ne signifie pas zéro effort humain. [S, F, Q]

### Correction de disponibilité des tests CI et vérification de l’archive

À la source `3494becbbfaf15ae571a71df05a49b9ce982cc84`, les tâches CI de l’économie et du banc historique ont réussi. L’exécution CI plus large [42310192424](https://github.com/MontrealAI/CONTINUITY/actions/runs/42310192424) a enregistré une erreur de démarrage dans `ProductProcessControls.test_two_producer_processes_reconcile_one_capacity_key` : `RPC_ID_MISMATCH` à l’instantané initial, avant la concurrence de production. Le [journal original](../../evidence/economy-v0.2/ci/source-3494-validation-attempt-1.log) et les [métadonnées de la tâche](../../evidence/economy-v0.2/ci/source-3494-validation-attempt-1.json) restent conservés. Cet échec est distinct des 424 tests locaux antérieurement réussis et n’est pas requalifié en première tentative CI réussie. [Q]

La révision publiée `dd00519e965b70ca47bf1cb3ac69bd3022ebfdc9` corrige uniquement la disponibilité au démarrage du test : le premier processus confirme son instantané initialisé avant le démarrage du second. Opérations concurrentes de production/acceptation, points de transition déterministes et assertions restent inchangés. Les [preuves conservées de la correction](../../evidence/economy-v0.2/ci/README.md) comprennent sources avant/après, différence exacte, 33 tests du produit réussis et 20 répétitions bornées par paire, soit 40 exécutions toutes réussies. Les 42 fichiers figés d’implémentation, interfaces et documentation restent inchangés. **Les opérations concurrentes de services initialisés sont qualifiées dans ces contrôles ; l’initialisation simultanée d’un tout nouveau schéma partagé reste non qualifiée.** La réponse générique de démarrage n’établit pas l’instruction SQLite ou système précise ayant échoué. [Q]

Les trois workflows à la révision `dd00519e965b70ca47bf1cb3ac69bd3022ebfdc9` se sont ensuite terminés avec succès :

| Workflow | Conclusion observée | Lien de l’exécution conservée |
| --- | --- | --- |
| Banc historique | SUCCESS | [42311289463](https://github.com/MontrealAI/CONTINUITY/actions/runs/42311289463) |
| Expérience économique | SUCCESS | [42311289404](https://github.com/MontrealAI/CONTINUITY/actions/runs/42311289404) |
| Validation bilingue complète | SUCCESS | [42311289375](https://github.com/MontrealAI/CONTINUITY/actions/runs/42311289375) |

L’[archive scellée de l’expérience](../../evidence/economy-v0.2/attempts.tar.xz) contient 2879196 octets, avec le SHA-256 `a96c6b7c25e0e17ed1c1f7d0fcf13b70c338159ae9c10c5f825699b9e186db25`. Après extraction, les empreintes des 7416 fichiers conservés correspondaient toutes au manifeste. Les vérifications fraîches distinctes de la première base extraite et de l’expérience complète extraite ont toutes deux retourné `PASSED`. L’échec CI ultérieur et sa correction de disponibilité restent des preuves complémentaires à côté de l’archive déjà scellée ; ils ne sont ni omis ni réécrits dans les résultats antérieurs. Ces contrôles portent sur le dossier de preuves du dépôt ; aucune nouvelle publication de version ni fusion n’est affirmée. [Q]

## 8. Reproduction et prochaine répétition autorisée

L’expérience complète bornée, sa vérification fraîche indépendante et la comparaison distincte emploient la source `3494becbbfaf15ae571a71df05a49b9ce982cc84` et de nouveaux répertoires :

```sh
git checkout 3494becbbfaf15ae571a71df05a49b9ce982cc84
python3 -m continuity_economy --language fr experiment --out /tmp/continuity-economy-complete-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuity-economy-complete-001
python3 -m continuity_economy --language fr compare --out /tmp/continuity-economy-comparison-001
```

La chronologie de la première base peut être reproduite par `compare` à la source `080a5484d1ff26fe04aac32078d9ea9ef2f739f4`. Le [guide des preuves](../../evidence/economy-v0.2/README.md) donne les commandes d’extraction et de vérification fraîche de l’archive conservée. La nouvelle vérification rouvre les preuves durables face à l’autorité conservée ; un Passeport sauvegardé n’est pas une preuve. Pour un exercice isolé, utiliser l’empreinte originale conservée indépendamment, sans la recalculer depuis un paquet potentiellement modifié. [R, F, Q]

Implémentation et preuves sont préparées pour revue sur `feat/continuity-economy-v0.2`. Aucune fusion, nouvelle publication de version ou mise en production n’est affirmée ici ; aucune nouvelle version téléchargée n’est présentée comme testée. Comportements historiques, articles, PDF, identités des preuves, version v0.1 et liens du Lab original restent préservés. La nouvelle expérience numérique ne requalifie pas les anciennes preuves de métadonnées en acceptation réelle du destinataire. [Q, R]

Les preuves supplémentaires minimales pour une répétition réelle bornée et autorisée sont un engagement numérique authentique et versionné provenant d’une autorité d’entreprise nommée ; un destinataire configuré indépendamment et sa spécification d’acceptation exacte ; des conditions réellement consenties de fournisseurs et de coordination couvrant capacité, divulgation, financement et responsabilités d’annulation/correction ; et un protocole écrit d’environnement jetable avec conditions d’arrêt, garde des preuves et opérateur responsable. La répétition devrait conserver le contrôle de reprise ordinaire et mesurer le travail d’intégration et de vérification. Résoudre le règlement partiel avant d’employer une solution pouvant accumuler du travail partiellement accepté. La réalisation physique exige son propre contrat et des preuves physiques supplémentaires. Cette expérience n’autorise ni prise de contact, ni perturbation de production, ni réservation réelle, ni dépense, ni changement d’accès. [R, T]

## Localisation des preuves

- **[B] Première base préenregistrée :** `economy-qualification/base-attempt-1/INDEX.json`, `SUMMARY.json`, chaque `runs/<fixture>.<method>/RESULT.json`, `controller.json`, les bases fermées du destinataire, des participants et de capacité, ainsi que les fichiers `authorities/` correspondants. Environnement et identité des régressions : `economy-qualification/BASE-ENVIRONMENT.json`.
- **[A] Analyse de base :** `economy-qualification/FIRST-BASE-ANALYSIS.json`, révision 2 ; le précédent `FIRST-BASE-ANALYSIS.attempt-1.json` est conservé. La durée jusqu’à acceptation ci-dessus est calculée depuis la dernière observation durable `ACCEPTED` du destinataire, moins le début du contrôleur.
- **[F] Gel de réutilisation :** [gel versionné](../../experiments/economy-v0.2/reuse-freeze.json), publié après la base au commit `d172b6491ff0f065fb3804811dd55cc8b5961830`.
- **[R] Règles et hypothèses :** [spécification préenregistrée](../../experiments/economy-v0.2/spec.json), cas associés avec empreintes, [architecture](ARCHITECTURE.fr.md) et [installation](README.fr.md).
- **[P] Produit pris en charge :** [spécification du produit numérique](PRODUCT.fr.md).
- **[D] Preuves de développement et adaptations :** [amendements](AMENDMENTS.md), contrôles originaux et corrigés compris. Les contrôles de développement restent distincts des comparaisons figées.
- **[T] Limites :** [modèle de menace](THREAT_MODEL.fr.md) et [matrice exigences-tests](REQUIREMENTS.fr.md).
- **[S] Successeur préenregistré :** [spécification du successeur](../../experiments/economy-v0.2/successor.json) et [nouveau cas](../../experiments/economy-v0.2/successor-fixtures/archive-window-transfer.json), rédigés après le gel de réutilisation et avant sa première exécution.
- **[Q] Qualification complète et échecs conservés :** [guide des preuves](../../evidence/economy-v0.2/README.md) et [archive comprimée](../../evidence/economy-v0.2/attempts.tar.xz). Les chemins d’archive `qualification/complete-attempt-1/`, `qualification/COMPLETE-ENVIRONMENT.json`, `qualification/FREEZE-CHECK.after.json` et `qualification/logs/complete-attempt-1.fresh.json` conservent premier successeur, reproduction complète, épreuves et vérification distincte. Les preuves CI complémentaires sont conservées dans `evidence/economy-v0.2/ci/` à côté de l’archive ; les altérations de copies ne doivent pas être comptées comme nouvelles productions.
