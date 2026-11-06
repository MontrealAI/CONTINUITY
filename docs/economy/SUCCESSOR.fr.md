# CONTINUITÉ Ω — Successeur inédit : transfert d’archives par fenêtres

[English](SUCCESSOR.md) · [Successeur préenregistré](../../experiments/economy-v0.2/successor.json) · [Données du cas](../../experiments/economy-v0.2/successor-fixtures/archive-window-transfer.json) · [Gel de réutilisation](../../experiments/economy-v0.2/reuse-freeze.json)

## État du préenregistrement et objectif

**Ce document déclare une expérience avant son exécution. Il ne rapporte aucun résultat de performance du successeur.** Seuls l’admission par schéma neutre, les bornes d’octets canoniques, l’égalité des empreintes figées et les calculs ci-dessous ont été contrôlés pendant la rédaction. Aucune planification, orchestration, production, réception, vérification d’acceptation ou comparaison du successeur n’a été exécutée.

La première comparaison de base employait la source `080a5484d1ff26fe04aac32078d9ea9ef2f739f4`. Son résultat consigné comprenait 21 exécutions de méthodes, 7 entrées d’IA indisponible et 7 égalités fonctionnelles entre méthode conventionnelle et banc d’essai. Le manifeste de réutilisation a ensuite été consigné localement au commit `6653a102b6bd2ffea7b11064305a6b9f6333a842` **avant la rédaction du présent successeur**. Son arbre identique est publié au commit `d172b6491ff0f065fb3804811dd55cc8b5961830`, référence de gel fixée par ce préenregistrement. Il fige 42 fichiers d’implémentation, d’interfaces et de documentation. Le manifeste conserve les empreintes des preuves initiales ; les résultats de base n’établissent pas ceux du successeur.

Ce successeur examine si les mécanismes conservés peuvent préserver un nouvel engagement numérique avec des exigences, participants, conditions économiques et fenêtres temporelles différents. La méthode conventionnelle bénéficie d’une réutilisation ordinaire équivalente. Égalité, victoire conventionnelle, échec et résultat non résolu sont valides. Un transfert synthétique unique n’établit ni inventeur amélioré, ni autonomie générale, ni capacité commerciale de passage à l’échelle.

## Nouvelles obligations numériques

Le cas `archive-window-transfer` définit le nouveau contrat `DIGITAL-ARCHIVE-001`. Le produit conserve le format sémantique borné `continuity-economy/label-job/v1`, mais chaque destinataire actif, référence produit, lot, préfixe de numéro et instruction bilingue est nouvellement défini.

| Obligation | Destinataire | Révision finale | Quantité conservée | Quantité active requise | Échéance logique |
| --- | --- | --- | --- | --- | --- |
| `ARC-410` | `RECIPIENT-NORD` | 3 | 420 | 420 | 130 |
| `ARC-520` | `RECIPIENT-EST` | 2 | 330 | 330 | 440 |
| `ARC-630` | `RECIPIENT-SUD` | 1 | 270 | 270 | 520 |
| `ARC-740` | `RECIPIENT-OUEST` | 1 | 90 | 0 — annulée | 360 |

L’obligation active totale est de **1 020 unités**, au lieu des 1 900 du cas de base. Le journal protégé contient huit événements : quatre acceptations initiales, deux révisions d’`ARC-410`, une révision d’`ARC-520` et l’annulation d’`ARC-740`. Les modifications touchent quantités, destinataire intermédiaire et instructions littérales de routage. Le point d’arrêt conservé est la séquence 8. Un ancien code d’étagère, destinataire antérieur, amendement omis ou annulation ressuscitée ne satisfait pas l’engagement final.

Le contrat initial autorise des lots fixes de 150 unités ou du reste final : `ARC-410` comporte 150/150/120, `ARC-520` 150/150/30 et `ARC-630` 150/120. Ces huit lots atteignent la limite de l’interface existante. Aucune méthode ne peut modifier leur taille, substituer le contenu ou supprimer une obligation après une perturbation. Une correction explicitement consignée par lot est permise selon les règles A1/A2 inchangées ; son financement ne garantit pas la capacité future.

L’échéance logique globale est 560, la limite d’observation 650, la durée de réservation 15 graduations et le délai écoulé 90 000 ms. Les échéances individuelles continuent à régir chaque obligation. Les graduations logiques représentent des opérations et avances de fenêtre modélisées, pas des secondes. Les durées réelles d’exécution et de vérification sont mesurées séparément.

L’acceptation établit le contenu numérique importé exact et la couverture des numéros. Elle n’établit ni apparence rendue, ni aptitude à l’impression, ni matériaux physiques d’archives ou acceptation authentique d’un client externe.

## Dépendances et fenêtres de capacité modifiées

| Fournisseur | Dépendance déclarée | Fenêtre | Capacité | État |
| --- | --- | --- | --- | --- |
| `ARCHIVE-PRIMARY` | `SHARED-INDEX-NETWORK` | `ALL` : 0–600 | 1 600 | Indisponible |
| `ARCHIVE-BACKUP` | `SHARED-INDEX-NETWORK` | `ALL` : 0–600 | 1 600 | Indisponible |
| `ARCHIVE-COMPAT-A` | `ARCHIVE-OFFLINE-A` | `EARLY` : 0–140 | 570 | Autorisé |
| `ARCHIVE-COMPAT-A` | `ARCHIVE-OFFLINE-A` | `LATE` : 260–560 | 330 | Autorisé |
| `ARCHIVE-COMPAT-B` | `ARCHIVE-OFFLINE-B` | `LATE` : 260–560 | 330 | Autorisé |

Le service principal et le secours conventionnel partagent la même dépendance déclarée défaillante dès le départ. Leurs capacités nominales ne constituent donc pas des ressources de secours disponibles. Les deux services compatibles autorisent production et divulgation nécessaires. Leur indépendance est une hypothèse rédigée du modèle local, pas une preuve de fournisseurs réels.

Les fenêtres ultérieures offrent ensemble 660 unités, moins que 1 020 ; du travail précoce est nécessaire. Le fournisseur A offre 900 unités sur ses deux fenêtres, encore moins que 1 020 ; le fournisseur B est nécessaire. `ARC-410` doit finir avant l’ouverture de toute fenêtre ultérieure. Ce sont des contraintes réellement figées, pas une souplesse ajoutée pour obtenir un résultat favorable.

La graine consignée est **7919**. La seule panne de transition injectée est `ACK_LOST_AFTER_ACCEPTANCE` lors de la **deuxième** opération `inspect`, cible `ANY`. Elle perd l’accusé après l’acceptation durable. La réponse permise retrouve l’identité et l’observation originales, sans doublon de contenu, charge de capacité ou paiement modélisé. La panne de dépendance commune est déclarée séparément dans l’état initial du contrat ; ce n’est pas une surprise non consignée.

## Économie définie et témoin arithmétique de faisabilité

Chaque montant ci-dessous est un nombre exact d’**unités mineures synthétiques** : **100 unités mineures valent 1 SMU fictive**. Tarifs, valeurs, soldes, responsabilités et consentements sont des hypothèses rédigées. Aucun n’est une observation de marché, un contrat réel, une mesure de volonté de payer ou un paiement.

L’intervalle de valeur conservé de l’acheteur est 8 200–9 600, son utilité extérieure 1 800, son plafond de prix 7 000 et ses fonds disponibles 7 600. L’intervalle n’est pas remplacé par un point avantageux. Le coordonnateur exige son coût d’exploitation de 180 plus le maximum de son bénéfice minimal de 70 et de son bénéfice extérieur de 110, soit une rémunération minimale de 290.

Le tableau suivant est un **témoin arithmétique réservé à la revue**, pas un plan calculé, une proposition sélectionnée ou un résultat observé. Il n’est fourni à aucun adaptateur. Il illustre 900 unités chez A et 120 chez B, compatibles avec les allocations agrégées 570/330/120 entre A-précoce/A-ultérieur/B-ultérieur.

| Condition définie | Fournisseur A, 900 unités | Fournisseur B, 120 unités |
| --- | --- | --- |
| Mise en route initiale + coût unitaire | 240 + 2 × 900 = 2 040 | 90 + 4 × 120 = 570 |
| Provision complète de correction permise | 120 + 2 × 900 = 1 920 | 60 + 3 × 120 = 420 |
| Bénéfice de participation requis | max(180, 260) = 260 | max(150, 200) = 200 |
| Paiement minimal de ce témoin | 4 220 | 1 190 |
| Fonds de roulement disponibles | 6 000 | 2 500 |
| Limite de responsabilité déclarée | 4 200 | 1 600 |

Le prix acheteur minimal de ce témoin est 4 220 + 1 190 + 290 = **5 700 unités mineures**, soit **57,00 SMU fictives**. Sa valeur d’équilibre pour l’acheteur est 5 700 + 1 800 = **7 500 unités mineures**. Le plafond certainement acceptable est min(7 000, 8 200 − 1 800) = **6 400** ; le plafond possiblement acceptable est min(7 000, 9 600 − 1 800) = **7 000**. Le témoin possède donc une région de prix certainement acceptable **[5 700, 6 400]**, avec acceptabilité possible jusqu’à 7 000 selon l’intervalle conservé et toutes les autres contraintes.

Le témoin couvre les exigences modélisées de fonds de roulement et de responsabilité. Ce calcul n’établit pas qu’une méthode découvre, exécute ou règle cette solution. Les méthodes peuvent choisir une autre solution et un autre prix autorisés. Aucune allocation, proposition, tarification ou victoire exacte ne constitue un critère d’acceptation.

Le financement technique est désactivé et sans fonds dans ce successeur. Une transaction refusée ne peut devenir une vente financée par commandite. Coûts et capacités des travaux infructueux restent consignés. Après toute acceptation acquise du destinataire, le courtier inchangé refuse l’annulation : un échec partiel conserve accord actif, séquestre restant et responsabilités en attente d’une résolution autorisée. Le règlement partiel n’est pas pris en charge.

## Affirmations, réfutations et preuves manquantes préenregistrées

| Affirmation | Observation favorable | Contre-exemple | Preuve dont l’absence empêche la conclusion |
| --- | --- | --- | --- |
| Résultat | Les 1 020 unités actives sont acceptées avec contenu, identité, destinataire, révision et délais finaux ; aucune unité annulée | Travail requis absent ou incorrect accepté, doublon, retard, action non autorisée ou réussite complète injustifiée | Autorité originale, exhaustivité, octets réels, importations ou observations après validation |
| Faisabilité du service modélisé | Décisions séparées, consentements, fonds, fenêtres, coûts engagés et transferts concordent | Dépendance défaillante utilisée, double allocation, financement insuffisant, participation non couverte ou acceptation acquise effacée | Garde des politiques, décisions, preuves monétaires/de capacité ou règlement résolu |
| Transfert de l’implémentation conservée | La première évaluation s’achève avec les 42 empreintes inchangées et les seules nouvelles données préenregistrées | Réussite nécessitant une modification exécutable propre au successeur, un livrable caché ou des moyens inégaux | Comparaison au gel, identité source exacte et première tentative |
| Avantage de méthode | Meilleur résultat accepté ou effort complet face à la méthode conventionnelle également équipée | L’avantage allégué disparaît avec une réutilisation ordinaire compétente ou une comptabilité complète | Travail d’adaptation/rédaction, coûts complets ou observations suffisamment répétées |

Les critères attendus des procédures conventionnelle et du banc sont : résultat `DEMONSTRATED`, faisabilité modélisée `DEMONSTRATED` et 1 020 unités acceptées. Il s’agit d’attentes réfutables, pas de résultats rapportés. Le contrôle sans achat attend zéro unité acceptée, un résultat échoué et une faisabilité `NOT_ESTABLISHED`. L’IA indisponible reste `NOT_RUN` avec résultat et faisabilité non établis. L’absence d’action et l’IA indisponible n’ont aucune transition d’acceptation susceptible de déclencher cette panne.

Pour les méthodes conventionnelle et du banc effectivement exécutées, l’accusé perdu préenregistré doit être observé et rapproché. Chaque méthode conserve ses champs d’évaluation réels ; une assertion réussie ne remplace jamais le verdict de résultat ou de transaction.

## Réutilisation permise, éléments cachés et mesures

Les deux méthodes implémentées peuvent réutiliser le code figé, les interfaces neutres, les procédures générales de transaction/reprise/rapprochement, la documentation publique et les enseignements déjà qualifiés. Elles reçoivent les mêmes nouvelles données contractuelles et politiques et les mêmes possibilités d’observation. Produits de base achevés, bases du destinataire, références d’acceptation, oracle externe, réponses attendues et témoin de revue sont exclus des matériaux initiaux des candidats.

Consigner égalité exacte des fichiers figés, fichiers d’entrée modifiés, quantités, tentatives, refus, coûts, retenues, transferts, requêtes, reprises, redémarrages, processeur, stockage et durées d’exécution/vérification. **Le travail de rédaction des données, d’intégration, d’adaptation et de vérification humaine n’a pas été instrumenté et reste inconnu.** Zéro fichier exécutable modifié ne signifie pas zéro effort humain ou une réduction prouvée du coût complet d’adaptation. L’essai unique par méthode et l’ordre fixe ne permettent aucune conclusion statistique de vitesse.

Conserver le premier résultat tenté, même infructueux. Toute réparation de l’exécuteur après le gel doit être consignée et évaluée comme adaptation ; elle ne peut qualifier rétroactivement le transfert initial d’inchangé. Les affirmations supplémentaires exigent leurs propres preuves.

## Exécution après consignation du préenregistrement

L’opérateur doit consigner le cas et le préenregistrement du successeur dans Git avant d’exécuter :

```sh
python3 -m continuity_economy --language fr successor --out /tmp/continuite-economie-successeur-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-successeur-001
```

Employer un nouveau répertoire et conserver ses références d’autorité indépendantes. La commande complète inchangée `experiment` inclura aussi ce successeur préenregistré séparément. Les constats effectifs appartiennent à un rapport ultérieur, avec révision source, tous les résultats, mesures manquantes et état de publication.
